import importlib.util,json,sqlite3,subprocess,sys,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent
spec=importlib.util.spec_from_file_location("dsh_lab",ROOT/"scripts/lab.py")
lab=importlib.util.module_from_spec(spec);spec.loader.exec_module(lab)
class LabTests(unittest.TestCase):
    def test_fixtures(self):
        root=ROOT/"fixtures"
        a=lab.read_jsonl(root/"skills.labels.jsonl")
        b=lab.read_jsonl(root/"skills.predictions.baseline.jsonl")
        c=lab.read_jsonl(root/"skills.predictions.candidate.jsonl")
        lab.check_ids(a,b)
        x,y=lab.score_skill(a,b,3),lab.score_skill(a,c,3)
        self.assertGreater(y["mrr_at_k"],x["mrr_at_k"])
        self.assertEqual(y["forbidden_at_k"],0.)
        self.assertEqual(y["recall_at_k"],1.)
    def test_duplicate_ids(self):
        with tempfile.TemporaryDirectory() as t:
            p=Path(t)/"x.jsonl";p.write_text('{"id":"x"}\n{"id":"x"}\n')
            with self.assertRaisesRegex(ValueError,"duplicate id"):lab.read_jsonl(p)
    def test_mismatched_ids(self):
        with self.assertRaisesRegex(ValueError,"mismatch"):lab.check_ids({"1":{}},{"2":{}})
    def test_invalid_skills(self):
        with self.assertRaisesRegex(ValueError,"duplicate values"):
            lab.score_skill({"x":{"relevant_skills":["a"]}},{"x":{"ranked_skills":["a","a"]}},2)
    def test_sqlite(self):
        with tempfile.TemporaryDirectory() as t:
            p=Path(t)/"nested/test.sqlite3"
            with lab.db_connect(p) as db:
                db.execute("INSERT INTO experiment_runs VALUES (?,?,?,?,?,?,?,?,?,?)",
                    ("run","now","skill","x",None,"hash","p",3,2,json.dumps({"hit_at_k":0.5})))
            with lab.db_connect(p) as db:
                self.assertEqual(lab.load_run(db,"run")["metrics"]["hit_at_k"],0.5)
    def test_scaffold_dry_run(self):
        with tempfile.TemporaryDirectory() as t:
            r=subprocess.run([sys.executable,str(ROOT/"scripts/scaffold.py"),"--project",t],capture_output=True)
            self.assertEqual(r.returncode,0)
            self.assertFalse((Path(t)/"evals").exists())
    def test_scaffold_no_overwrite(self):
        with tempfile.TemporaryDirectory() as t:
            p=Path(t)/"evals/datasets/skills.labels.jsonl";p.parent.mkdir(parents=True)
            p.write_text("EXISTING")
            r=subprocess.run([sys.executable,str(ROOT/"scripts/scaffold.py"),"--project",t,"--apply"],capture_output=True)
            self.assertEqual(r.returncode,0)
            self.assertEqual(p.read_text(),"EXISTING")
            self.assertTrue((Path(t)/".local/.gitignore").exists())
if __name__=="__main__":unittest.main()
