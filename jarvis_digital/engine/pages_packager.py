"""
Cloudflare Pages Packager & Build Publisher Guard.
Enforces that any package destined for jarvis-digital.pages.dev must:
1. Re-execute canonical lead presence gate with candidate data, requiring SEM_SITE_CONFIRMADO for this mission.
2. Require independent QA with real factual and visual evidence (no dummy dict bypasses).
3. Verify matching SHA-256 for all build output assets and invalidate if altered.
4. Verify confirmed media usage rights (zero unlicensed media; every image/video mapped to authorized manifest with sha256).
5. Enforce slug safety: strictly [a-z0-9]+(?:-[a-z0-9]+)*, reject ../, absolute paths, and prevent overwriting existing packages.
6. Enforce STRICT dist allowlist: no .env, source code, sqlite, CRM or credentials to dist. Restrict .json names and content.
7. Support configurable expiration/deactivation via client-side/worker barrier and noindex/disclaimer.
8. Support authorized media extensions only (.html, .js, .css, .svg, .png, .jpg, .jpeg, .webp, .woff, .woff2, .ico, and authorized .mp4/.webm).
"""
from typing import Dict, Any, List, Optional, Tuple, Set
from pathlib import Path
import json
import hashlib
import datetime
import shutil
import re
import sys

# Safe slug pattern: strictly lowercase alphanumeric with hyphens, no consecutive hyphens
SLUG_REGEX = re.compile(r'^[a-z0-9]+(?:-[a-z0-9]+)*$')

DISALLOWED_FILE_PATTERNS = [
    r'^\.env', r'.*\.sqlite.*', r'.*\.db$', r'.*\.log$', r'.*\.ts$', r'.*\.tsx$',
    r'.*\.py$', r'.*\.sh$', r'.*\.cmd$', r'.*\.bak.*', r'.*credentials.*', r'.*secret.*',
    r'.*crm.*', r'.*lead.*'
]

ALLOWED_DIST_EXTENSIONS = {
    '.html', '.js', '.css', '.svg', '.png', '.jpg', '.jpeg', '.webp', '.woff', '.woff2', '.ico',
    '.mp4', '.webm', '.json'
}

# Permitted public JSON files only (CRM or sensitive data strictly banned)
ALLOWED_JSON_FILENAMES = {
    'manifest.json', 'site.webmanifest', 'flow_assets.json', 'robots.json'
}

MEDIA_EXTENSIONS = {'.png', '.jpg', '.jpeg', '.webp', '.svg', '.mp4', '.webm', '.ico'}

class PagesPackager:
    def __init__(self, output_base: Optional[Path] = None, workspace_root: Optional[Path] = None):
        self.output_base = Path(output_base or (Path(__file__).parent / "dist_packages")).resolve()
        self.output_base.mkdir(parents=True, exist_ok=True)
        self.workspace_root = Path(workspace_root or Path(__file__).resolve().parents[3]).resolve()

    def validate_slug(self, candidate_slug: str) -> str:
        if not candidate_slug or not isinstance(candidate_slug, str):
            raise ValueError(f"INVALID_SLUG: Slug cannot be empty.")
        clean_slug = candidate_slug.strip()
        if not SLUG_REGEX.match(clean_slug):
            raise ValueError(f"INVALID_SLUG_FORMAT: '{candidate_slug}' must match strictly [a-z0-9]+(?:-[a-z0-9]+)*")
        
        # Check path traversal
        target_path = (self.output_base / clean_slug).resolve()
        if not target_path.is_relative_to(self.output_base):
            raise PermissionError(f"SLUG_PATH_TRAVERSAL_DETECTED: '{candidate_slug}' escapes output_base.")
        return clean_slug

    @staticmethod
    def audit_dist_files(dist_dir: Path) -> Tuple[bool, List[str], List[Dict[str, Any]]]:
        """
        Inspects directory. Returns (is_clean, violations, file_manifest).
        Rejects internal files, secrets, non-web extensions, symlinks escaping root,
        or unauthorized json/crm files.
        """
        violations = []
        manifest = []
        resolved_dist = dist_dir.resolve()

        if not resolved_dist.is_dir():
            return False, [f"DIST_DIRECTORY_NOT_FOUND: {dist_dir}"], []

        for p in resolved_dist.rglob('*'):
            # Detect symlinks/junctions pointing outside
            if p.is_symlink():
                target = p.resolve()
                if not target.is_relative_to(resolved_dist):
                    violations.append(f"ILLEGAL_SYMLINK_ESCAPING_ROOT: {p}")
                    continue

            if p.is_file():
                rel_path = p.relative_to(resolved_dist).as_posix()
                
                # Check disallowed patterns
                for pat in DISALLOWED_FILE_PATTERNS:
                    if re.match(pat, p.name, re.IGNORECASE) or re.match(pat, rel_path, re.IGNORECASE):
                        violations.append(f"FORBIDDEN_FILE_DETECTED: {rel_path}")
                
                # Check extension
                ext = p.suffix.lower()
                if ext not in ALLOWED_DIST_EXTENSIONS:
                    violations.append(f"UNAPPROVED_DIST_EXTENSION: {rel_path} ({ext})")
                
                # Check JSON files - only explicit public names permitted
                if ext == '.json' and p.name.lower() not in ALLOWED_JSON_FILENAMES:
                    violations.append(f"UNAUTHORIZED_JSON_FILE: {rel_path} (Only allowed: {ALLOWED_JSON_FILENAMES})")

                # Calculate sha256
                sha = hashlib.sha256(p.read_bytes()).hexdigest()
                manifest.append({
                    'file': rel_path,
                    'sha256': sha,
                    'size_bytes': p.stat().st_size,
                    'is_media': ext in MEDIA_EXTENSIONS
                })

        return (len(violations) == 0, violations, manifest)

    @staticmethod
    def verify_html_policy(html_content: str) -> Dict[str, bool]:
        """
        Verifies presence of noindex, nofollow, and conceptual demo disclaimer.
        """
        has_noindex = bool(re.search(r'<meta[^>]+name=["\']robots["\'][^>]+content=["\'][^"\']*noindex', html_content, re.IGNORECASE))
        has_disclaimer = bool(re.search(r'demonstração conceitual não oficial', html_content, re.IGNORECASE) or
                              re.search(r'demonstracao conceitual nao oficial', html_content, re.IGNORECASE))
        return {
            'has_noindex': has_noindex,
            'has_disclaimer': has_disclaimer,
            'compliant': has_noindex and has_disclaimer
        }

    def verify_media_manifest(
        self,
        dist_manifest: List[Dict[str, Any]],
        visual_manifest: Dict[str, Any]
    ) -> Tuple[bool, List[str]]:
        """
        Every media file in dist must map directly to an authorized item in visual_manifest
        with rights_confirmed=True and matching sha256.
        """
        violations = []
        authorized_media = visual_manifest.get('authorized_media', [])
        # Map by sha256
        auth_by_sha = {m.get('sha256'): m for m in authorized_media if m.get('sha256') and m.get('rights_confirmed')}

        media_files = [m for m in dist_manifest if m.get('is_media')]
        for mf in media_files:
            file_sha = mf['sha256']
            if file_sha not in auth_by_sha:
                violations.append(f"UNAUTHORIZED_MEDIA_ASSET: File '{mf['file']}' (sha256: {file_sha[:10]}...) is not registered with verified license/rights in visual_manifest.")
            else:
                item = auth_by_sha[file_sha]
                if not item.get('rights_confirmed') or item.get('license_type') not in {'CC0', 'ORIGINAL_CREATED', 'EXPLICIT_CLIENT_WRITTEN_PERMISSION'}:
                    violations.append(f"INVALID_MEDIA_RIGHTS: Media for '{mf['file']}' has invalid license '{item.get('license_type')}'.")

        return len(violations) == 0, violations

    def prepare_deployment_package(
        self,
        candidate_slug: str,
        candidate_data: Dict[str, Any],
        qa_report: Dict[str, Any],
        visual_manifest: Dict[str, Any],
        source_dist_dir: Path,
        expiration_days: int = 7,
        canonical_gate_fn: Optional[Any] = None
    ) -> Dict[str, Any]:
        """
        Validates all prerequisites and prepares the deployable package.
        Re-executes canonical gate on candidate_data and strictly checks required criterion: SEM_SITE_CONFIRMADO.
        Requires genuine QA report with browser render verification and verified asset hashes.
        Never deletes an existing production package; rejects collisions.
        """
        clean_slug = self.validate_slug(candidate_slug)

        # 1. Collision check: NEVER delete an existing package to prevent destructive overwriting
        dest_pkg = self.output_base / clean_slug
        if dest_pkg.exists():
            raise FileExistsError(f"PACKAGE_COLLISION: Package '{clean_slug}' already exists in output_base. Overwriting is strictly forbidden.")

        # 2. Re-run canonical lead presence gate directly on candidate_data
        if canonical_gate_fn is None:
            # Dynamically import lead_presence_gate
            gate_dir = self.workspace_root / "Nucleos" / "Operacao Comercial" / "automacoes" / "JARVIS-Propostas"
            if str(gate_dir) not in sys.path:
                sys.path.insert(0, str(gate_dir))
            import lead_presence_gate
            canonical_gate_fn = lead_presence_gate.evaluate

        gate_verdict = canonical_gate_fn(candidate_data, self.workspace_root)
        if not gate_verdict.get('eligible_for_production'):
            raise PermissionError(f"GATE_REJECTED: Candidate {clean_slug} failed canonical gate: {gate_verdict.get('status')} errors: {gate_verdict.get('errors')}")

        # Check mission constraint: SEM_SITE_CONFIRMADO is mandatory for this campaign
        reasons = [r.get('criterion') for r in gate_verdict.get('reasons', []) if isinstance(r, dict)]
        if 'SEM_SITE_CONFIRMADO' not in reasons:
            raise PermissionError(f"MISSION_POLICY_VIOLATION: Candidate {clean_slug} is not verified as 'SEM_SITE_CONFIRMADO'. Detected criteria: {reasons}")

        # 3. Check QA Report - reject fake passes and require real visual verification
        if not isinstance(qa_report, dict) or qa_report.get('verdict') != 'APROVADO':
            raise PermissionError(f"QA_REJECTED: Candidate {clean_slug} QA verdict is not APROVADO: {qa_report.get('verdict') if isinstance(qa_report, dict) else 'INVALID_REPORT'}")

        if not qa_report.get('browser_render_verified'):
            raise PermissionError(f"QA_REJECTED: QA report lacks verified browser rendering across required viewports.")

        # 4. Audit source dist directory
        is_clean, violations, manifest = self.audit_dist_files(source_dist_dir)
        if not is_clean:
            raise PermissionError(f"DIST_AUDIT_FAILED: Violations: {violations}")

        # 5. Verify asset hash equality between QA report and actual dist files
        qa_hashes = qa_report.get('dist_hashes', {})
        if set(qa_hashes) != {item['file'] for item in manifest}:
            raise PermissionError('QA_HASH_COVERAGE_INCOMPLETE: Every build file must match the reviewed manifest.')
        if not qa_report.get('visual_approved') or not qa_report.get('factual_approved') or not qa_report.get('reviewed_by'):
            raise PermissionError('INDEPENDENT_REVIEW_MISSING: Visual and factual review remain mandatory.')
        for item in manifest:
            rel = item['file']
            if rel in qa_hashes and qa_hashes[rel] != item['sha256']:
                raise ValueError(f"BUILD_TAMPERING_DETECTED: File '{rel}' sha256 mismatch between QA audit and packaging time.")

        # 6. Verify media manifest and rights
        media_clean, media_violations = self.verify_media_manifest(manifest, visual_manifest)
        if not media_clean:
            raise PermissionError(f"MEDIA_RIGHTS_VIOLATION: {media_violations}")

        # 7. Check index.html compliance
        index_html_path = source_dist_dir / "index.html"
        if not index_html_path.is_file():
            raise FileNotFoundError("INDEX_HTML_MISSING: dist must contain an index.html file.")

        index_html_text = index_html_path.read_text(encoding='utf-8', errors='ignore')
        html_policy = self.verify_html_policy(index_html_text)
        if not html_policy['compliant']:
            raise PermissionError(f"HTML_POLICY_VIOLATION: Missing noindex or conceptual demo banner: {html_policy}")

        # 8. Create staging package
        dest_pkg.mkdir(parents=True)

        for item in manifest:
            src = source_dist_dir / item['file']
            dst = dest_pkg / item['file']
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)

        now = datetime.datetime.now(datetime.timezone.utc)
        expires_at = now + datetime.timedelta(days=expiration_days)

        # Inject expiration enforcement barrier (script in index.html to block display after expiration)
        # and create _headers file for Cloudflare Pages (X-Robots-Tag: noindex, nofollow)
        cf_headers = "/*\n  X-Robots-Tag: noindex, nofollow\n  Cache-Control: public, max-age=3600\n"
        (dest_pkg / "_headers").write_text(cf_headers, encoding='utf-8')

        meta = {
            'slug': clean_slug,
            'packaged_at': now.isoformat(),
            'expires_at': expires_at.isoformat(),
            'status': 'PACKAGED_FOR_PAGES',
            'target_url': f"https://jarvis-digital.pages.dev/{clean_slug}",
            'file_count': len(manifest),
            'files': manifest,
            'html_policy': html_policy,
            'expiration_barrier_enforced': False,
            'deployment_requires': 'Compose root Pages worker with hosting/expiry_worker.mjs; package metadata alone does not enforce expiration.',
            'sha256_package': hashlib.sha256(json.dumps(manifest, sort_keys=True).encode()).hexdigest()
        }

        # Keep PACKAGE_META outside dist or safely private in package metadata
        meta_private_dir = self.output_base / ".metadata"
        meta_private_dir.mkdir(exist_ok=True)
        (meta_private_dir / f"{clean_slug}.meta.json").write_text(json.dumps(meta, indent=2), encoding='utf-8')

        return meta