#!/usr/bin/env python3
import argparse,json,sys
from pathlib import Path
from datetime import date
ALLOWED_STATUS={"pending","ready","completed","stale"}
CONF={"high","medium","low"}
CATS={"frontend","backend","other"}
SIDES={"frontend","backend"}

def load(p):
    with open(p,encoding="utf-8") as f:return json.load(f)

def req(cond,msg,errs):
    if not cond: errs.append(msg)

def unique(xs): return len(xs)==len(set(xs))

def rev(obj,errs):
    r=obj.get("revision",{})
    req(isinstance(r,dict),"revision missing",errs)
    req(isinstance(r.get("version"),int) and r.get("version",0)>0,"revision.version invalid",errs)
    req(r.get("last_modified_by") in {"ai","human"},"revision.last_modified_by invalid",errs)
    req(isinstance(r.get("changes"),list),"revision.changes invalid",errs)

def same_req(obj,init,errs):
    if init: req(obj.get("requirement_id")==init["requirement"]["id"],"requirement_id mismatch",errs)

def validate_init(d,errs):
    req(d.get("schema_version")=="4.0","schema_version must be 4.0",errs)
    r=d.get("requirement",{})
    for k in ("id","title","description","priority"): req(isinstance(r.get(k),str) and r.get(k)!="",f"requirement.{k} missing",errs)
    s=d.get("stage_status",{})
    req(set(s)=={"understanding","breakdown","estimation","scheduling"},"stage_status keys invalid",errs)
    for k,v in s.items(): req(v in ALLOWED_STATUS,f"stage_status.{k} invalid",errs)
    rev(d,errs)

def validate_understanding(d,init,errs):
    req(d.get("schema_version")=="4.0","schema_version must be 4.0",errs); same_req(d,init,errs)
    for k in ("goal",): req(isinstance(d.get(k),str) and d.get(k)!="",f"{k} missing",errs)
    for k in ("scope","out_of_scope","modules","assumptions","review_items"): req(isinstance(d.get(k),list),f"{k} must be list",errs)
    mids=[]
    for m in d.get("modules",[]):
        req(m.get("side") in SIDES,"module.side invalid",errs)
        for k in ("id","name","repository","change_summary"): req(isinstance(m.get(k),str),f"module.{k} invalid",errs)
        mids.append(m.get("id"))
    req(unique(mids),"duplicate module ids",errs)
    qids=[]
    for q in d.get("review_items",[]):
        req(q.get("type") in {"choice","text"},"review item type invalid",errs)
        for k in ("id","question","ai_assumption","impact"): req(isinstance(q.get(k),str),f"review_item.{k} invalid",errs)
        req(isinstance(q.get("required"),bool),"review_item.required invalid",errs)
        if q.get("type")=="choice":
            req(isinstance(q.get("options"),list) and len(q["options"])>=2,"choice options invalid",errs)
            req("自定义" not in q.get("options",[]),"choice options must not include 自定义",errs)
            req(isinstance(q.get("custom_value"),str),"custom_value invalid",errs)
        qids.append(q.get("id"))
    req(unique(qids),"duplicate review item ids",errs); rev(d,errs)

def task_map(breakdown): return {t["id"]:t for t in breakdown.get("tasks",[]) if isinstance(t,dict) and "id" in t}

def validate_breakdown(d,init,understanding,errs):
    req(d.get("schema_version")=="4.0","schema_version must be 4.0",errs); same_req(d,init,errs)
    tasks=d.get("tasks",[]); req(isinstance(tasks,list),"tasks must be list",errs)
    ids=[]; mids={m["id"] for m in understanding.get("modules",[])} if understanding else set()
    graph={}
    for t in tasks:
        ids.append(t.get("id")); graph[t.get("id")]=t.get("dependencies",[])
        for k in ("id","title","description"): req(isinstance(t.get(k),str) and t.get(k)!="",f"task.{k} invalid",errs)
        req(t.get("category") in CATS,"task.category invalid",errs)
        req(t.get("module_id") is None or isinstance(t.get("module_id"),str),"task.module_id invalid",errs)
        if understanding and t.get("module_id") is not None: req(t["module_id"] in mids,f"unknown module_id {t['module_id']}",errs)
        req(isinstance(t.get("dependencies"),list),"task.dependencies invalid",errs)
    req(unique(ids),"duplicate task ids",errs)
    idset=set(ids)
    for tid,deps in graph.items():
        for dep in deps: req(dep in idset,f"{tid} dependency {dep} missing",errs)
    visiting=set();done=set()
    def dfs(n):
        if n in visiting: return True
        if n in done:return False
        visiting.add(n)
        for x in graph.get(n,[]):
            if dfs(x):return True
        visiting.remove(n);done.add(n);return False
    req(not any(dfs(x) for x in ids if x not in done),"task dependency cycle",errs); rev(d,errs)

def validate_estimation(d,init,breakdown,errs):
    req(d.get("schema_version")=="4.0","schema_version must be 4.0",errs); same_req(d,init,errs)
    est=d.get("estimations",[]); req(isinstance(est,list),"estimations must be list",errs)
    tids=set(task_map(breakdown)) if breakdown else set(); ids=[]; total=0; counts={"high":0,"medium":0,"low":0}
    for e in est:
        tid=e.get("task_id");ids.append(tid)
        if breakdown:req(tid in tids,f"unknown task_id {tid}",errs)
        effort=e.get("effort_days");req(isinstance(effort,(int,float)) and not isinstance(effort,bool) and effort>0,"effort_days invalid",errs)
        if isinstance(effort,(int,float)): total+=effort
        c=e.get("confidence");req(c in CONF,"confidence invalid",errs)
        if c in counts:counts[c]+=1
        basis=e.get("estimate_basis",[]);req(isinstance(basis,list) and len(basis)>0,"estimate_basis invalid",errs)
        bsum=0
        for b in basis:
            req(isinstance(b.get("item"),str) and b.get("item"),"estimate basis item invalid",errs)
            be=b.get("effort_days");req(isinstance(be,(int,float)) and be>0,"estimate basis effort invalid",errs)
            if isinstance(be,(int,float)):bsum+=be
        if isinstance(effort,(int,float)):req(abs(bsum-effort)<1e-9,f"{tid} basis sum mismatch",errs)
        req(isinstance(e.get("uncertainties"),list),"uncertainties invalid",errs)
    req(unique(ids),"duplicate estimation task_id",errs)
    if breakdown:req(set(ids)==tids,"estimations must cover all breakdown tasks",errs)
    s=d.get("summary",{});req(abs(s.get("total_effort_days",-1)-total)<1e-9,"summary.total_effort_days mismatch",errs)
    req(s.get("confidence_counts")==counts,"summary.confidence_counts mismatch",errs);rev(d,errs)

def validate_scheduling(d,init,breakdown,estimation,errs):
    req(d.get("schema_version")=="4.0","schema_version must be 4.0",errs); same_req(d,init,errs)
    sched=d.get("schedule",[]); req(isinstance(sched,list),"schedule must be list",errs)
    tm=task_map(breakdown) if breakdown else {}; tids=set(tm); ids=[]; dates={}
    for s in sched:
        tid=s.get("task_id");ids.append(tid)
        if breakdown:req(tid in tids,f"unknown task_id {tid}",errs)
        req(isinstance(s.get("assignee"),str) and s.get("assignee"),"assignee invalid",errs)
        try:a=date.fromisoformat(s["start_date"]);b=date.fromisoformat(s["end_date"]);req(a<=b,f"{tid} date range invalid",errs);dates[tid]=(a,b)
        except Exception:errs.append(f"{tid} date invalid")
    req(unique(ids),"duplicate schedule task_id",errs)
    if breakdown:req(set(ids)==tids,"schedule must cover all breakdown tasks",errs)
    for tid,t in tm.items():
        if tid in dates:
            for dep in t.get("dependencies",[]):
                if dep in dates:req(dates[tid][0]>dates[dep][1],f"{tid} starts before {dep} completed",errs)
    summary=d.get("summary",{})
    if dates:
        req(summary.get("start_date")==min(a for a,b in dates.values()).isoformat(),"summary.start_date mismatch",errs)
        req(summary.get("delivery_date")==max(b for a,b in dates.values()).isoformat(),"summary.delivery_date mismatch",errs)
    req(isinstance(summary.get("estimated_working_days"),int) and summary.get("estimated_working_days",0)>0,"estimated_working_days invalid",errs)
    cp=summary.get("critical_path",[]);req(isinstance(cp,list),"critical_path invalid",errs)
    for x in cp:
        if breakdown:req(x in tids,f"critical_path unknown task {x}",errs)
    rev(d,errs)

def main():
    p=argparse.ArgumentParser()
    p.add_argument("stage",choices=["init","understanding","breakdown","estimation","scheduling"])
    p.add_argument("file")
    p.add_argument("--init");p.add_argument("--understanding");p.add_argument("--breakdown");p.add_argument("--estimation")
    a=p.parse_args();d=load(a.file);errs=[]
    init=load(a.init) if a.init else None;u=load(a.understanding) if a.understanding else None;b=load(a.breakdown) if a.breakdown else None;e=load(a.estimation) if a.estimation else None
    {"init":lambda:validate_init(d,errs),
     "understanding":lambda:validate_understanding(d,init,errs),
     "breakdown":lambda:validate_breakdown(d,init,u,errs),
     "estimation":lambda:validate_estimation(d,init,b,errs),
     "scheduling":lambda:validate_scheduling(d,init,b,e,errs)}[a.stage]()
    if errs:
        for x in errs:print("ERROR:",x,file=sys.stderr)
        print(f"FAILED: {len(errs)} error(s)",file=sys.stderr);return 1
    print(f"OK: {a.stage} JSON valid");return 0
if __name__=="__main__":raise SystemExit(main())