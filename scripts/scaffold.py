#!/usr/bin/env python3
"""Initialize missing fixture files in an Agent plugin repo. Dry-run by default."""
import argparse,shutil,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent
SOURCES={
"evals/datasets/skills.labels.jsonl":"skills.labels.jsonl",
"evals/predictions/skills.baseline.jsonl":"skills.predictions.baseline.jsonl",
"evals/predictions/skills.candidate.jsonl":"skills.predictions.candidate.jsonl",
"evals/datasets/tasks.labels.jsonl":"tasks.labels.jsonl",
"evals/predictions/tasks.baseline.jsonl":"tasks.predictions.baseline.jsonl",
"evals/datasets/context.labels.jsonl":"context.labels.jsonl",
"evals/predictions/context.baseline.jsonl":"context.predictions.baseline.jsonl"}
README="# DSH Algorithm Evaluation\n\nThese are example synthetic fixtures, not actual DSH predictions. Replace them with separately labeled and predicted JSONL. Run the lab.py scorer from your project root.\n"
def main():
    p=argparse.ArgumentParser();p.add_argument("--project",default=".");p.add_argument("--apply",action="store_true");a=p.parse_args()
    root=Path(a.project).resolve()
    if not root.is_dir():print("ERROR project missing",file=sys.stderr);return 2
    targets=[(root/path,ROOT/"fixtures"/source) for path,source in SOURCES.items()]
    targets.extend([(root/"evals/README.md",None),(root/".local/.gitignore",None)])
    for dst,src in targets:
        if dst.exists(): print("SKIP existing",dst.relative_to(root));continue
        if not a.apply:print("WOULD CREATE",dst.relative_to(root));continue
        dst.parent.mkdir(parents=True,exist_ok=True)
        if src:
            with src.open("rb") as fin,dst.open("xb") as fout:shutil.copyfileobj(fin,fout)
        else:
            dst.write_text("*\n!.gitignore\n" if dst.name==".gitignore" else README,encoding="utf-8")
        print("CREATED",dst.relative_to(root))
    print("DONE" if a.apply else "DRY RUN — use --apply to write")
    return 0
if __name__=="__main__":sys.exit(main())
