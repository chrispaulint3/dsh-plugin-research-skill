#!/usr/bin/env python3
"""Read-only DSH local plugin environment diagnostic. Stdlib only."""
import argparse,json,os,platform,shutil,subprocess,sys
from pathlib import Path
def version(name,flags=("--version",)):
    if not shutil.which(name):return None
    try:
        proc=subprocess.run([name,*flags],capture_output=True,text=True,timeout=5)
        return (proc.stdout.strip() or proc.stderr.strip()).splitlines()[0][:180] if proc.returncode==0 else f"ERROR({proc.returncode})"
    except (OSError,subprocess.TimeoutExpired,IndexError): return "ERROR"
def inspect(project,profile):
    root=Path(project).expanduser().resolve()
    home=Path(os.getenv("DSH_HOME",str(Path.home()/".dsh"))).expanduser()
    profile_dir=home/"profiles"/profile
    try:
        r=subprocess.run(["git","-C",str(root),"rev-parse","--show-toplevel"],capture_output=True,text=True,timeout=3)
        git_root=r.stdout.strip() if r.returncode==0 else None
    except (OSError,subprocess.TimeoutExpired):git_root=None
    result={"project":str(root),"project_exists":root.is_dir(),"os":platform.system(),
        "architecture":platform.machine(),"python":platform.python_version(),
        "node":version("node"),"pnpm":version("pnpm"),"dsh":version("dsh"),
        "git_root":git_root,"profile_name":profile,"profile_exists":profile_dir.is_dir(),
        "project_skill_present":(root/".agents/skills/dsh-plugin-research/SKILL.md").is_file()}
    warnings=[]
    if not root.is_dir():warnings.append("Project directory missing")
    if not git_root:warnings.append("Not in Git worktree")
    for name in ("node","pnpm","dsh"):
        if not result[name] or result[name].startswith("ERROR"):warnings.append(f"{name} unavailable")
    if not result["profile_exists"]:warnings.append("Profile not found; do NOT auto-reset")
    if not result["project_skill_present"]:warnings.append("Project Skill path not found")
    result["warnings"]=warnings
    return result
def main():
    p=argparse.ArgumentParser();p.add_argument("--project",default=".")
    p.add_argument("--profile",default="adaptive-dev");p.add_argument("--json",action="store_true")
    p.add_argument("--strict",action="store_true");args=p.parse_args()
    result=inspect(args.project,args.profile)
    if args.json: print(json.dumps(result,ensure_ascii=False,indent=2))
    else:
        for k,v in result.items():print(f"{k}: {v}")
    return 1 if args.strict and result["warnings"] else 0
if __name__=="__main__":sys.exit(main())
