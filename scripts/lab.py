#!/usr/bin/env python3
"""Offline JSONL predictions -> metrics -> SQLite. Does NOT call DSH or a model."""
from __future__ import annotations
import argparse, datetime as dt, hashlib, json, sqlite3, subprocess, sys, uuid
from pathlib import Path

MODES={"direct","fast","interactive","background"}
DDL="""CREATE TABLE IF NOT EXISTS experiment_runs (
run_id TEXT PRIMARY KEY, created_at TEXT NOT NULL, mode TEXT NOT NULL, tag TEXT NOT NULL,
git_commit TEXT, labels_sha256 TEXT NOT NULL, predictions_sha256 TEXT NOT NULL,
k INTEGER, case_count INTEGER NOT NULL, metrics_json TEXT NOT NULL);
CREATE INDEX IF NOT EXISTS idx_experiment_created ON experiment_runs(created_at);"""

def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def read_jsonl(path):
    path=Path(path)
    if not path.is_file(): raise ValueError(f"File not found: {path}")
    rows={}
    for n,line in enumerate(path.read_text(encoding="utf-8").splitlines(),1):
        if not line.strip(): continue
        try: row=json.loads(line)
        except json.JSONDecodeError as e: raise ValueError(f"{path}:{n} invalid JSON: {e}") from e
        if not isinstance(row,dict) or not isinstance(row.get("id"),str) or not row["id"].strip():
            raise ValueError(f"{path}:{n}: nonempty string id required")
        if row["id"] in rows: raise ValueError(f"{path}:{n}: duplicate id {row['id']}")
        rows[row["id"]]=row
    if not rows: raise ValueError(f"No cases in {path}")
    return rows

def check_ids(labels,preds):
    missing=set(labels)-set(preds); extra=set(preds)-set(labels)
    if missing or extra: raise ValueError(f"Prediction IDs mismatch: missing={sorted(missing)} extra={sorted(extra)}")

def string_list(value,field,case):
    if not isinstance(value,list) or any(not isinstance(x,str) or not x.strip() for x in value):
        raise ValueError(f"Case {case}: {field} must be list of nonempty strings")
    if len(value)!=len(set(value)): raise ValueError(f"Case {case}: duplicate values in {field}")
    return value

def score_skill(labels,preds,k):
    if k<1: raise ValueError("k must be >= 1")
    keys=("recall_at_k","precision_at_k","hit_at_k","mrr_at_k","forbidden_at_k")
    sums={key:0. for key in keys}; empty=0
    for case,truth in labels.items():
        relevant=set(string_list(truth.get("relevant_skills"),"relevant_skills",case))
        forbidden=set(string_list(truth.get("forbidden_skills",[]),"forbidden_skills",case))
        ranked=string_list(preds[case].get("ranked_skills"),"ranked_skills",case)[:k]
        hits=[i+1 for i,s in enumerate(ranked) if s in relevant]
        empty+=not bool(relevant)
        sums["recall_at_k"]+=(len(hits)/len(relevant) if relevant else float(not ranked))
        sums["precision_at_k"]+=len(hits)/k
        sums["hit_at_k"]+=bool(hits)
        sums["mrr_at_k"]+=1/min(hits) if hits else 0
        sums["forbidden_at_k"]+=bool(set(ranked)&forbidden)
    return {key:round(sums[key]/len(labels),6) for key in keys}|{"case_count":len(labels),"k":k,"empty_relevant_cases":empty}

def score_task(labels,preds):
    totals={m:0 for m in sorted(MODES)}; correct={m:0 for m in sorted(MODES)}
    for case,truth in labels.items():
        expected=truth.get("expected_mode"); actual=preds[case].get("predicted_mode")
        if expected not in MODES or actual not in MODES: raise ValueError(f"{case}: invalid routing mode")
        totals[expected]+=1; correct[expected]+=expected==actual
    return {"case_count":len(labels),"accuracy":round(sum(correct.values())/len(labels),6),
        "recall_by_class":{m:round(correct[m]/totals[m],6) if totals[m] else None for m in sorted(MODES)}}

def score_context(labels,preds):
    recall=extra=0.
    for case,truth in labels.items():
        req=set(string_list(truth.get("required_refs"),"required_refs",case))
        got=set(string_list(preds[case].get("retained_refs"),"retained_refs",case))
        recall+=len(req&got)/len(req) if req else 1.
        extra+=len(got-req)/len(got) if got else 0.
    return {"case_count":len(labels),"reference_recall":round(recall/len(labels),6),
       "extra_reference_ratio":round(extra/len(labels),6)}

def db_connect(path):
    path=Path(path)
    if str(path)!=":memory:": path.parent.mkdir(parents=True,exist_ok=True)
    conn=sqlite3.connect(str(path),timeout=5)
    conn.executescript(DDL)
    return conn

def git_commit():
    try:
        r=subprocess.run(["git","rev-parse","HEAD"],capture_output=True,text=True,timeout=3)
        return r.stdout.strip() if r.returncode==0 else None
    except (OSError,subprocess.TimeoutExpired): return None

def cmd_eval(args):
    labels=read_jsonl(args.labels); preds=read_jsonl(args.predictions); check_ids(labels,preds)
    if args.out and Path(args.out).exists(): raise ValueError("Refusing to overwrite existing report")
    metrics={"skill":lambda:score_skill(labels,preds,args.k),"task":lambda:score_task(labels,preds),
             "context":lambda:score_context(labels,preds)}[args.mode]()
    row={"run_id":str(uuid.uuid4()),"created_at":dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
      "mode":args.mode,"tag":args.tag,"git_commit":git_commit(),"labels_sha256":sha256(args.labels),
      "predictions_sha256":sha256(args.predictions),"k":args.k if args.mode=="skill" else None,
      "case_count":len(labels),"metrics":metrics}
    with db_connect(args.db) as conn:
        conn.execute("INSERT INTO experiment_runs VALUES (?,?,?,?,?,?,?,?,?,?)",
        (row["run_id"],row["created_at"],row["mode"],row["tag"],row["git_commit"],
        row["labels_sha256"],row["predictions_sha256"],row["k"],row["case_count"],
        json.dumps(metrics,ensure_ascii=False,sort_keys=True)))
    output=json.dumps(row,ensure_ascii=False,indent=2)
    if args.out:
        p=Path(args.out);p.parent.mkdir(parents=True,exist_ok=True);p.write_text(output+"\n",encoding="utf-8")
    print(output);print("NOTE: offline scoring only; no DSH execution.",file=sys.stderr)

def load_run(conn,run_id):
    conn.row_factory=sqlite3.Row
    r=conn.execute("SELECT * FROM experiment_runs WHERE run_id=?",(run_id,)).fetchone()
    if r is None: raise ValueError(f"Run not found: {run_id}")
    v=dict(r);v["metrics"]=json.loads(v.pop("metrics_json"));return v

def cmd_history(args):
    if not Path(args.db).exists(): print("No experiment database yet.");return
    with db_connect(args.db) as conn:
        for row in conn.execute("SELECT run_id,created_at,mode,tag,case_count FROM experiment_runs ORDER BY created_at DESC,rowid DESC LIMIT ?",(args.limit,)):
            print(f"{row[0]}  {row[1]}  {row[2]:<7} {row[4]:>3} cases  {row[3]}")

def cmd_compare(args):
    if not Path(args.db).exists(): raise ValueError("Experiment database missing")
    with db_connect(args.db) as conn: a=load_run(conn,args.baseline);b=load_run(conn,args.candidate)
    if a["mode"]!=b["mode"] or a["labels_sha256"]!=b["labels_sha256"] or a["k"]!=b["k"]:
        raise ValueError("Incompatible runs: compare same mode, labels hash and K")
    print("baseline",a["run_id"],a["tag"],"candidate",b["run_id"],b["tag"])
    for key in sorted(a["metrics"]):
        x=a["metrics"][key];y=b["metrics"].get(key)
        if isinstance(x,(int,float)) and isinstance(y,(int,float)):
            print(f"{key:<28} {x:>10.5f} {y:>10.5f} {y-x:>+10.5f}")
    print("NOTE: offline comparisons are not proof of E2E Agent performance.")

def cmd_selftest(args):
    root=Path(__file__).resolve().parent.parent/"fixtures"
    for mode,fn in [("skill","skills"),("task","tasks"),("context","context")]:
        labels=read_jsonl(root/f"{fn}.labels.jsonl")
        preds=read_jsonl(root/f"{fn}.predictions.baseline.jsonl")
        check_ids(labels,preds)
        value=score_skill(labels,preds,3) if mode=="skill" else score_task(labels,preds) if mode=="task" else score_context(labels,preds)
        assert value["case_count"]==len(labels)
        print("PASS",mode,value)
    with db_connect(":memory:") as conn:
        assert conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='experiment_runs'").fetchone()
    print("PASS SQLite schema")

def main():
    p=argparse.ArgumentParser(description=__doc__);subs=p.add_subparsers(dest="cmd",required=True)
    ev=subs.add_parser("eval");ev.add_argument("mode",choices=["skill","task","context"])
    ev.add_argument("--labels",required=True);ev.add_argument("--predictions",required=True)
    ev.add_argument("--db",default=".local/experiments.sqlite3");ev.add_argument("--tag",default="untagged")
    ev.add_argument("--k",type=int,default=3);ev.add_argument("--out");ev.set_defaults(fn=cmd_eval)
    history=subs.add_parser("history");history.add_argument("--db",default=".local/experiments.sqlite3")
    history.add_argument("--limit",type=int,default=20);history.set_defaults(fn=cmd_history)
    compare=subs.add_parser("compare");compare.add_argument("baseline");compare.add_argument("candidate")
    compare.add_argument("--db",default=".local/experiments.sqlite3");compare.set_defaults(fn=cmd_compare)
    selftest=subs.add_parser("self-test");selftest.set_defaults(fn=cmd_selftest)
    args=p.parse_args()
    try: args.fn(args);return 0
    except (ValueError,OSError,sqlite3.Error) as e: print("ERROR:",e,file=sys.stderr);return 2

if __name__=="__main__": sys.exit(main())
