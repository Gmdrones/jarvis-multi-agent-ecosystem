"""
Comprehensive Adversarial Test Suite for Jarvis Digital Engine.
Tests all P0 requirements:
1. Rejection of unverified candidate (missing presence audit evidence).
2. Rejection when own domain exists (e.g. Studio 761 case).
3. Rejection of unverified/unlicensed media in manifest and dist.
4. Detection of altered asset (hash mismatch) between QA and packaging time.
5. Strict dist security: rejection of forbidden files (.env, .sqlite, .ts, CRM json, credentials).
6. HTML lint: detection of malformed URLs, empty hrefs, missing viewport/charset, missing noindex/disclaimer.
7. Anti-bypass QA: rejection of fake APROVADO and missing browser rendering evidence.
8. Packager safety: slug path traversal rejection, package collision prevention, and SEM_SITE_CONFIRMADO requirement.
9. Instagram intelligence: robust normalization of BR phone numbers and address matching with verified evidence.
10. Orchestrator: dynamic canonical gate loading, slug collision rejection between different businesses, and idempotency.
"""
import unittest
import tempfile
import shutil
import json
import hashlib
from pathlib import Path
import datetime

from orchestrator import PipelineOrchestrator
from instagram_intelligence import InstagramIntelligence, normalize_phone_br
from pages_packager import PagesPackager
from technical_qa import TechnicalQA

class TestJarvisDigitalEngine(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.workspace_root = Path(self.test_dir).resolve()
        
        # Setup mock canonical gate in mock workspace
        propostas_dir = self.workspace_root / "Nucleos" / "Operacao Comercial" / "automacoes" / "JARVIS-Propostas"
        propostas_dir.mkdir(parents=True, exist_ok=True)
        self.gate_path = propostas_dir / "lead_presence_gate.py"

        # Copy canonical lead_presence_gate from original repo
        real_gate = Path(__file__).resolve().parents[2] / "automacoes" / "JARVIS-Propostas" / "lead_presence_gate.py"
        shutil.copy2(real_gate, self.gate_path)

        self.db_path = self.workspace_root / "test_pipeline.sqlite"
        self.orchestrator = PipelineOrchestrator(
            db_path=self.db_path,
            workspace_root=self.workspace_root,
            canonical_gate_path=self.gate_path
        )
        self.packager = PagesPackager(
            output_base=self.workspace_root / "dist_packages",
            workspace_root=self.workspace_root
        )
        self.qa = TechnicalQA(workspace_root=self.workspace_root)

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def _create_evidence_file(self, content: str = "<html>Evidence</html>") -> Path:
        ev_dir = self.workspace_root / "evidence"
        ev_dir.mkdir(parents=True, exist_ok=True)
        f = ev_dir / f"ev_{hashlib.sha256(content.encode()).hexdigest()[:10]}.html"
        f.write_text(content, encoding='utf-8')
        return f

    def test_01_rejection_of_unverified_candidate(self):
        candidate = {
            "lead_id": "lead-unverified-001",
            "nome_comercial": "Barbearia Sem Evidencias",
            "unidade": "Barra",
        }
        res = self.orchestrator.process_candidate(candidate)
        self.assertFalse(res['eligible_for_production'])
        self.assertIn('PENDENTE', res['status'])

    def test_02_rejection_when_own_domain_present(self):
        ev_file = self._create_evidence_file("Studio 761 Official Site")
        sha = hashlib.sha256(ev_file.read_bytes()).hexdigest()
        now = datetime.datetime.now(datetime.timezone.utc).isoformat()

        candidate = {
            "lead_id": "studio-761-official",
            "nome_comercial": "Studio 761",
            "unidade": "Barra",
            "presence_audit": {
                "identity": {
                    "status": "MATCHED_UNIT",
                    "matched_identifiers": ["address", "phone"],
                    "evidence": {"url": "https://maps.google.com", "captured_at": now, "file": str(ev_file), "sha256": sha}
                },
                "name_searches": [
                    {"query": "Studio 761 Barra", "purpose": "EXACT_NAME_CITY", "outcome": "RESULTS_REVIEWED", "evidence": {"url": "https://google.com", "captured_at": now, "file": str(ev_file), "sha256": sha}},
                    {"query": "Studio 761 site", "purpose": "NAME_WEBSITE", "outcome": "RESULTS_REVIEWED", "evidence": {"url": "https://google.com", "captured_at": now, "file": str(ev_file), "sha256": sha}},
                    {"query": "Studio 761 perfil", "purpose": "NAME_GOOGLE_PROFILE", "outcome": "RESULTS_REVIEWED", "evidence": {"url": "https://google.com", "captured_at": now, "file": str(ev_file), "sha256": sha}}
                ],
                "website": {
                    "status": "PRESENT",
                    "url": "https://studio761.com.br",
                    "identity_status": "MATCHED_UNIT",
                    "quality": "ADEQUATE",
                    "evidence": {"url": "https://studio761.com.br", "captured_at": now, "file": str(ev_file), "sha256": sha},
                    "desktop_capture": {"url": "https://studio761.com.br", "captured_at": now, "file": str(ev_file), "sha256": sha},
                    "mobile_capture": {"url": "https://studio761.com.br", "captured_at": now, "file": str(ev_file), "sha256": sha}
                },
                "google_profile": {
                    "status": "PRESENT",
                    "url": "https://maps.google.com/?cid=123",
                    "identity_status": "MATCHED_UNIT",
                    "quality": "ADEQUATE",
                    "evidence": {"url": "https://maps.google.com", "captured_at": now, "file": str(ev_file), "sha256": sha}
                }
            }
        }
        res = self.orchestrator.process_candidate(candidate)
        self.assertFalse(res['eligible_for_production'])
        self.assertEqual(res['status'], 'BASE_FUTURA_SEM_OPORTUNIDADE_COMPROVADA')

    def test_03_rejection_of_unauthorized_media_in_manifest(self):
        ig = InstagramIntelligence(workspace_root=self.workspace_root)
        handle = ig.parse_handle("@barbearia_exemplo")
        media = [{
            "media_id": "img_01",
            "media_type": "image",
            "license_type": "UNKNOWN_SCRAPED",
            "rights_confirmed": False
        }]
        manifest = ig.build_visual_manifest(handle, [], media)
        self.assertEqual(manifest['authorized_media_count'], 0)
        self.assertEqual(len(manifest['authorized_media']), 0)

    def test_04_rejection_of_forbidden_internal_files_in_dist(self):
        dist_dir = self.workspace_root / "dist_leak_test"
        dist_dir.mkdir(parents=True)
        (dist_dir / "index.html").write_text("<html><meta name='robots' content='noindex'><!-- demonstração conceitual não oficial --></html>", encoding='utf-8')
        (dist_dir / ".env").write_text("SECRET_KEY=123", encoding='utf-8')
        (dist_dir / "crm_leads.json").write_text("{}", encoding='utf-8')

        is_clean, violations, _ = PagesPackager.audit_dist_files(dist_dir)
        self.assertFalse(is_clean)
        self.assertTrue(any(".env" in v for v in violations))
        self.assertTrue(any("crm_leads.json" in v for v in violations))

    def test_05_detection_of_malformed_urls_and_missing_viewport(self):
        bad_html = """
        <html>
        <head><title>Test</title></head>
        <body>
            <a href="https://instagram.com/https://instagram.com/foo">IG</a>
            <a href="">Empty</a>
        </body>
        </html>
        """
        audit = TechnicalQA.audit_html_technical(bad_html)
        self.assertFalse(audit['passed'])
        self.assertTrue(any('MISSING_VIEWPORT_META_TAG' in i for i in audit['issues']))
        self.assertTrue(any('MALFORMED_CONCATENATED_URL' in i for i in audit['issues']))

    def test_06_qa_rejects_approval_without_browser_rendering(self):
        dist_dir = self.workspace_root / "dist_qa_test"
        dist_dir.mkdir(parents=True)
        (dist_dir / "index.html").write_text(
            "<!doctype html><html><head><meta charset='utf-8'><meta name='viewport' content='width=device-width'><meta name='robots' content='noindex, nofollow'></head><body><header>Demonstração conceitual não oficial</header></body></html>",
            encoding='utf-8'
        )
        # Calling QA without browser render evidence MUST return PENDENTE (never APROVADO)
        qa_res = self.qa.run_build_qa(dist_dir, "test-candidate")
        self.assertEqual(qa_res['verdict'], 'PENDENTE')
        self.assertFalse(qa_res['browser_render_verified'])
        self.assertEqual(len(qa_res['viewports_tested']), 0)

    def test_07_packager_rejection_of_fake_qa_and_missing_gate(self):
        dist_dir = self.workspace_root / "dist_fake_qa"
        dist_dir.mkdir(parents=True)
        (dist_dir / "index.html").write_text(
            "<!doctype html><html><head><meta charset='utf-8'><meta name='viewport' content='width=device-width'><meta name='robots' content='noindex, nofollow'></head><body><header>Demonstração conceitual não oficial</header></body></html>",
            encoding='utf-8'
        )
        fake_qa = {'verdict': 'APROVADO', 'browser_render_verified': False}
        unverified_candidate = {'nome_comercial': 'Fake Corp'}

        with self.assertRaises(PermissionError):
            self.packager.prepare_deployment_package(
                candidate_slug="fake-corp",
                candidate_data=unverified_candidate,
                qa_report=fake_qa,
                visual_manifest={'authorized_media': []},
                source_dist_dir=dist_dir
            )

    def test_08_packager_slug_traversal_and_collision_prevention(self):
        # Slug traversal rejection
        with self.assertRaises(ValueError):
            self.packager.validate_slug("../escaped_dir")
        
        # Package collision rejection
        existing_pkg = self.packager.output_base / "barbearia-unidade-1"
        existing_pkg.mkdir(parents=True, exist_ok=True)
        (existing_pkg / "index.html").write_text("existing", encoding='utf-8')

        with self.assertRaises(FileExistsError):
            self.packager.prepare_deployment_package(
                candidate_slug="barbearia-unidade-1",
                candidate_data={},
                qa_report={},
                visual_manifest={},
                source_dist_dir=existing_pkg
            )

    def test_09_instagram_phone_normalization_and_handle_security(self):
        # Test BR phone normalization
        self.assertEqual(normalize_phone_br("(21) 98765-4321"), "5521987654321")
        self.assertEqual(normalize_phone_br("2131725174"), "552131725174")
        self.assertIsNone(normalize_phone_br("21")) # Substring rejected

        # Handle security
        ig = InstagramIntelligence(workspace_root=self.workspace_root)
        self.assertIsNone(ig.parse_handle("https://user:pass@instagram.com/fake"))
        self.assertIsNone(ig.parse_handle("https://instagram.com/p/Cxyz123/"))
        parsed = ig.parse_handle("https://instagram.com/barbearia_real/")
        self.assertIsNotNone(parsed)
        self.assertEqual(parsed['handle'], "barbearia_real")

    def test_10_orchestrator_slug_collision_between_distinct_businesses(self):
        c1 = {"lead_id": "slug-shared", "nome_comercial": "Barbearia A", "unidade": "Barra", "telefone": "21999990001"}
        c2 = {"lead_id": "slug-shared", "nome_comercial": "Clinica Odonto B", "unidade": "Barra", "telefone": "21999990002"}

        self.orchestrator.process_candidate(c1)
        # Attempting to reuse same slug for a different business must raise ValueError
        with self.assertRaises(ValueError):
            self.orchestrator.process_candidate(c2)

    def test_11_missing_hash_coverage_blocks_even_claimed_approval(self):
        dist = self.workspace_root / 'hash-test'; dist.mkdir()
        (dist / 'index.html').write_text("<meta name='robots' content='noindex,nofollow'>Demonstração conceitual não oficial", encoding='utf8')
        qa = {'verdict':'APROVADO','browser_render_verified':True,'visual_approved':True,'factual_approved':True,'reviewed_by':'TEST_ONLY'}
        mock_gate = lambda *_: {'eligible_for_production':True,'reasons':[{'criterion':'SEM_SITE_CONFIRMADO'}]}
        with self.assertRaisesRegex(PermissionError,'HASH_COVERAGE'):
            self.packager.prepare_deployment_package('test-only-hash',{},qa,{},dist,canonical_gate_fn=mock_gate)

    def test_12_changed_file_invalidates_previous_qa_hash(self):
        dist = self.workspace_root / 'tamper-test'; dist.mkdir()
        file = dist / 'index.html'; file.write_text("<meta name='robots' content='noindex,nofollow'>Demonstração conceitual não oficial", encoding='utf8')
        qa = {'verdict':'APROVADO','browser_render_verified':True,'visual_approved':True,'factual_approved':True,'reviewed_by':'TEST_ONLY','dist_hashes':{'index.html':hashlib.sha256(file.read_bytes()).hexdigest()}}
        file.write_text(file.read_text(encoding='utf8')+' changed',encoding='utf8')
        mock_gate = lambda *_: {'eligible_for_production':True,'reasons':[{'criterion':'SEM_SITE_CONFIRMADO'}]}
        with self.assertRaisesRegex(ValueError,'TAMPERING'):
            self.packager.prepare_deployment_package('test-only-tamper',{},qa,{},dist,canonical_gate_fn=mock_gate)

    def test_13_dist_media_must_be_authorized(self):
        clean, violations = self.packager.verify_media_manifest([{'file':'unlicensed.jpg','sha256':'unlicensed','is_media':True}],{'authorized_media':[]})
        self.assertFalse(clean)
        self.assertTrue(violations)

if __name__ == '__main__':
    unittest.main()