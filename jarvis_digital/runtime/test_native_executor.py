import unittest,sys,json,tempfile,copy
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
import native_executor as n
class ExecutorTests(unittest.TestCase):
 def test_rejects_private_and_account_urls(self):
  for url in ['https://127.0.0.1/','http://example.com/','https://www.instagram.com/direct/inbox/','https://x:y@example.com/','https://www.instagram.com/accounts/login/']:
   with self.subTest(url=url),self.assertRaises(ValueError):n.public_url(url)
 def test_rejects_paths_outside_mission(self):
  with self.assertRaises(ValueError):n.path('../../outside')
 def test_rejects_mutating_approved_baseline(self):
  with self.assertRaisesRegex(ValueError,'NEW_SITE_VERSION_REQUIRED'):n.build({'site':'sites/studio-962-real-v3'},Path(tempfile.gettempdir()))
 def test_canonical_gate_rejects_tampered_evidence(self):
  gate=n.PipelineOrchestrator(db_path=n.B/'state/runtime-test.sqlite',workspace_root=n.ROOT,canonical_gate_path=n.B.parent/'automacoes/JARVIS-Propostas/lead_presence_gate.py')._lead_presence_gate
  c=json.loads((n.B/'evidence/ismerim-barbearia/candidate.json').read_text(encoding='utf8'))
  self.assertTrue(gate.evaluate(c,n.ROOT)['eligible_for_production'])
  c=copy.deepcopy(c);c['presence_audit']['identity']['evidence']['sha256']='0'*64
  self.assertFalse(gate.evaluate(c,n.ROOT)['eligible_for_production'])
 def test_dist_rejects_internal_files(self):
  with tempfile.TemporaryDirectory() as folder:
   p=Path(folder);(p/'.env').write_text('TEST_ONLY');(p/'lead.json').write_text('{}')
   clean,errors,files=n.PagesPackager.audit_dist_files(p)
   self.assertFalse(clean);self.assertGreaterEqual(len(errors),2)
if __name__=='__main__':unittest.main(verbosity=2)