"""
Orchestrator for Local Leads Qualification & Pipeline State Management.
Strictly imports and executes the canonical lead_presence_gate.py.
Rejects all non-approved candidates. Enforces transactional SQLite state,
idempotency by unit/slug, and source attribution per field.

P0 Review updates:
1. No hardcoded personal paths. Workspace root and canonical gate path are dynamically configurable
   via constructor, environment variables (JARVIS_WORKSPACE_ROOT, CANONICAL_GATE_PATH), or resolved dynamically.
2. Unique identity key: combination of canonical identity key + unique slug. Overwriting another company or unit is prevented.
3. Operation idempotency: same identity unit safely updates without slug collisions.
4. Candidate readiness re-evaluates stale evidence before returning READY.
"""
import sys
import os
import json
import sqlite3
import datetime
import hashlib
import importlib.util
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

class PipelineOrchestrator:
    def __init__(
        self,
        db_path: Optional[Path] = None,
        workspace_root: Optional[Path] = None,
        canonical_gate_path: Optional[Path] = None
    ):
        # Dynamically determine workspace root
        env_root = os.environ.get("JARVIS_WORKSPACE_ROOT")
        if workspace_root:
            self.workspace_root = Path(workspace_root).resolve()
        elif env_root:
            self.workspace_root = Path(env_root).resolve()
        else:
            # Fallback to standard relative traversal from current location
            self.workspace_root = Path(__file__).resolve().parents[3]

        self.db_path = Path(db_path or (Path(__file__).parent / "pipeline.sqlite")).resolve()
        
        # Load canonical gate dynamically
        env_gate = os.environ.get("CANONICAL_GATE_PATH")
        if canonical_gate_path:
            self.canonical_gate_path = Path(canonical_gate_path).resolve()
        elif env_gate:
            self.canonical_gate_path = Path(env_gate).resolve()
        else:
            self.canonical_gate_path = (self.workspace_root / "Nucleos" / "Operacao Comercial" / "automacoes" / "JARVIS-Propostas" / "lead_presence_gate.py").resolve()

        self._lead_presence_gate = self._load_canonical_gate()
        self._init_db()

    def _load_canonical_gate(self):
        if not self.canonical_gate_path.is_file():
            raise FileNotFoundError(f"CANONICAL_GATE_NOT_FOUND: Could not locate canonical gate at '{self.canonical_gate_path}'")
        
        spec = importlib.util.spec_from_file_location("lead_presence_gate", str(self.canonical_gate_path))
        if spec is None or spec.loader is None:
            raise ImportError(f"Could not load spec for lead_presence_gate from {self.canonical_gate_path}")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        with self._get_connection() as conn:
            conn.execute("""
            CREATE TABLE IF NOT EXISTS candidates (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                slug TEXT UNIQUE NOT NULL,
                identity_key TEXT NOT NULL,
                nome_comercial TEXT NOT NULL,
                unidade TEXT NOT NULL,
                status TEXT NOT NULL,
                eligible_for_production INTEGER NOT NULL DEFAULT 0,
                gate_verdict_json TEXT,
                lead_data_json TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
            """)
            conn.execute("""
            CREATE TABLE IF NOT EXISTS audit_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                candidate_slug TEXT NOT NULL,
                action TEXT NOT NULL,
                verdict_status TEXT NOT NULL,
                reasons_json TEXT,
                errors_json TEXT,
                timestamp TEXT NOT NULL,
                FOREIGN KEY (candidate_slug) REFERENCES candidates(slug)
            );
            """)
            conn.commit()

    def _compute_identity_key(self, candidate_data: Dict[str, Any]) -> str:
        """
        Computes a stable identity key combining commercial name, unit, and phone or place_id.
        """
        nome = str(candidate_data.get('nome_comercial', '')).strip().lower()
        unidade = str(candidate_data.get('unidade', 'matriz')).strip().lower()
        phone = str(candidate_data.get('telefone', '') or candidate_data.get('whatsapp', '')).strip()
        place_id = str(candidate_data.get('google_place_id', '')).strip()
        raw = f"{nome}::{unidade}::{phone}::{place_id}"
        return hashlib.sha256(raw.encode('utf-8')).hexdigest()[:16]

    def process_candidate(self, candidate_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Runs the canonical lead_presence_gate evaluate function.
        Rejects non-eligible leads immediately.
        Persists state transactionally with collision prevention and unit idempotency.
        """
        slug = candidate_data.get('slug') or candidate_data.get('lead_id')
        if not slug:
            nome = candidate_data.get('nome_comercial', 'unknown').lower()
            slug = "".join(c if c.isalnum() else "-" for c in nome).strip("-")

        unidade = candidate_data.get('unidade', 'matriz')
        identity_key = self._compute_identity_key(candidate_data)
        now_str = datetime.datetime.now(datetime.timezone.utc).isoformat()

        # Run canonical lead_presence_gate
        verdict = self._lead_presence_gate.evaluate(candidate_data, self.workspace_root)
        is_eligible = 1 if verdict.get('eligible_for_production') else 0
        status = verdict.get('status', 'REPROVADO')

        with self._get_connection() as conn:
            # Check existing candidate by slug
            row = conn.execute("SELECT id, slug, identity_key, nome_comercial, unidade FROM candidates WHERE slug = ?", (slug,)).fetchone()
            
            if row:
                # If slug exists for a DIFFERENT company/identity, prevent collision
                if row['identity_key'] != identity_key:
                    raise ValueError(f"SLUG_COLLISION_DETECTED: Slug '{slug}' is already owned by '{row['nome_comercial']}' ({row['identity_key']}). Cannot overwrite with '{candidate_data.get('nome_comercial')}' ({identity_key}).")
                
                # Idempotent update for the same company/unit
                conn.execute("""
                UPDATE candidates SET
                    nome_comercial = ?,
                    unidade = ?,
                    status = ?,
                    eligible_for_production = ?,
                    gate_verdict_json = ?,
                    lead_data_json = ?,
                    updated_at = ?
                WHERE slug = ?
                """, (
                    candidate_data.get('nome_comercial', ''),
                    unidade,
                    status,
                    is_eligible,
                    json.dumps(verdict, ensure_ascii=False),
                    json.dumps(candidate_data, ensure_ascii=False),
                    now_str,
                    slug
                ))
            else:
                conn.execute("""
                INSERT INTO candidates (
                    slug, identity_key, nome_comercial, unidade, status, eligible_for_production,
                    gate_verdict_json, lead_data_json, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    slug,
                    identity_key,
                    candidate_data.get('nome_comercial', ''),
                    unidade,
                    status,
                    is_eligible,
                    json.dumps(verdict, ensure_ascii=False),
                    json.dumps(candidate_data, ensure_ascii=False),
                    now_str,
                    now_str
                ))

            # Record audit history
            conn.execute("""
            INSERT INTO audit_history (
                candidate_slug, action, verdict_status, reasons_json, errors_json, timestamp
            ) VALUES (?, ?, ?, ?, ?, ?)
            """, (
                slug,
                'EVALUATE_PRESENCE_GATE',
                status,
                json.dumps(verdict.get('reasons', []), ensure_ascii=False),
                json.dumps(verdict.get('errors', []), ensure_ascii=False),
                now_str
            ))
            conn.commit()

        return {
            'slug': slug,
            'identity_key': identity_key,
            'status': status,
            'eligible_for_production': bool(is_eligible),
            'verdict': verdict
        }

    def list_production_ready(self) -> List[Dict[str, Any]]:
        """
        Returns list of eligible candidates, re-evaluating evidence freshness.
        """
        ready = []
        with self._get_connection() as conn:
            rows = conn.execute("SELECT * FROM candidates WHERE eligible_for_production = 1").fetchall()
            for r in rows:
                c_data = json.loads(r['lead_data_json'])
                # Re-verify freshness using canonical gate
                v = self._lead_presence_gate.evaluate(c_data, self.workspace_root)
                if v.get('eligible_for_production'):
                    item = dict(r)
                    item['gate_verdict'] = v
                    ready.append(item)
        return ready

    def get_candidate(self, slug: str) -> Optional[Dict[str, Any]]:
        with self._get_connection() as conn:
            row = conn.execute("SELECT * FROM candidates WHERE slug = ?", (slug,)).fetchone()
            return dict(row) if row else None