"""
Run-directory capture library — the provenance substrate (MVP-1, stage 5).

Pure stdlib so any experiment code or Claude Code skill can `import run_dir`
without a dependency. Manages the five machine-readable artifacts of a run
directory (see docs/schemas.md and templates/run_dir/README.md):

    metadata.json          reproducibility metadata            (this module writes it)
    prereg.yaml            the commitment device               (src/preregister.py owns it)
    provenance.jsonl       agent decisions / tool calls        RunDir.log_provenance()
    gates.jsonl            human approval gates                RunDir.log_gate()
    attention_checks.jsonl seeded overseer checks              RunDir.log_attention_check()

The three .jsonl logs are append-only and event ids are a deterministic counter
(no randomness), so a killed run resumes cleanly and history can't be silently
rewritten. metadata.json is written atomically (tmp + rename) so an interrupted
write on ephemeral compute never leaves a half-file.
"""

import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

STAGES = (
    "lit_review", "planning", "preregistration", "implementation",
    "tracking", "analysis", "resolution", "communication", "publication",
)
STAGE_STATUS = ("pending", "running", "done", "frozen", "skipped", "failed")
PROVENANCE_EVENTS = (
    "tool_call", "model_invocation", "decision", "branch_selected",
    "artifact_written", "error",
)
GATE_DECISIONS = ("approve", "reject", "edit")
# Sampled from the real AI-mistake distribution (see docs/supervision_attention_checks.md).
ERROR_TYPES = (
    "fabricated_result", "subtle_bug", "unfaithful_summary", "misread_metric",
    "dropped_confound", "overstated_conclusion",
)
DIFFICULTIES = ("easy", "medium", "hard")


def _now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _git_sha(repo: Path) -> str:
    """HEAD sha of the code repo, or 'uncommitted' if there are no commits."""
    result = subprocess.run(
        ["git", "-C", str(repo), "rev-parse", "HEAD"],
        capture_output=True, text=True,
    )
    return result.stdout.strip() if result.returncode == 0 else "uncommitted"


def _append_jsonl(path: Path, record: dict) -> None:
    with open(path, "a") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")


def _count_lines(path: Path) -> int:
    if not path.exists():
        return 0
    with open(path) as f:
        return sum(1 for _ in f)


class RunDir:
    """A handle to one run directory. Create with RunDir.create(); reopen with RunDir(path)."""

    def __init__(self, path: Path):
        self.path = Path(path)
        assert self.path.is_dir(), f"run dir does not exist: {self.path}"
        assert self.metadata_path.exists(), f"not a run dir (no metadata.json): {self.path}"

    # --- artifact paths ------------------------------------------------------
    @property
    def metadata_path(self) -> Path: return self.path / "metadata.json"
    @property
    def provenance_path(self) -> Path: return self.path / "provenance.jsonl"
    @property
    def gates_path(self) -> Path: return self.path / "gates.jsonl"
    @property
    def attention_checks_path(self) -> Path: return self.path / "attention_checks.jsonl"

    # --- creation ------------------------------------------------------------
    @classmethod
    def create(cls, base: Path, run_id: str, *, models: list[dict], harness: dict,
               compute: dict | None = None, code_repo: Path | None = None) -> "RunDir":
        assert run_id.startswith("run_"), f"run_id must be run_<ts>_<name>, got {run_id!r}"
        assert isinstance(models, list) and models, "must supply at least one model"
        for m in models:
            assert m.get("id") and m.get("role"), f"each model needs id+role, got {m!r}"
        assert harness.get("tool"), "harness must name a tool"

        path = Path(base) / run_id
        path.mkdir(parents=True, exist_ok=False)  # fail loudly if the run already exists

        metadata = {
            "run_id": run_id,
            "created_at": _now_iso(),
            "git_sha": _git_sha(code_repo or Path.cwd()),
            "models": models,
            "harness": harness,
            "compute": compute,
            "cost": {"usd": None, "tokens_in": 0, "tokens_out": 0},
            "prereg": None,
            "stage_status": {s: "pending" for s in STAGES},
        }
        self = cls.__new__(cls)
        self.path = path
        self._write_metadata(metadata)
        return self

    # --- metadata ------------------------------------------------------------
    def read_metadata(self) -> dict:
        with open(self.metadata_path) as f:
            return json.load(f)

    def _write_metadata(self, metadata: dict) -> None:
        # Atomic: an interrupted write on a spot instance must not corrupt metadata.
        tmp = self.metadata_path.with_suffix(".json.tmp")
        with open(tmp, "w") as f:
            json.dump(metadata, f, indent=2)
        tmp.replace(self.metadata_path)

    def set_stage_status(self, stage: str, status: str) -> None:
        assert stage in STAGES, f"unknown stage {stage!r}"
        assert status in STAGE_STATUS, f"unknown status {status!r}"
        meta = self.read_metadata()
        meta["stage_status"][stage] = status
        self._write_metadata(meta)

    def add_cost(self, *, tokens_in: int = 0, tokens_out: int = 0, usd: float | None = None) -> None:
        meta = self.read_metadata()
        c = meta["cost"]
        c["tokens_in"] += tokens_in
        c["tokens_out"] += tokens_out
        if usd is not None:
            c["usd"] = (c["usd"] or 0.0) + usd
        self._write_metadata(meta)

    def link_prereg(self, *, frozen_at: str, content_hash: str) -> None:
        meta = self.read_metadata()
        meta["prereg"] = {"frozen_at": frozen_at, "content_hash": content_hash}
        self._write_metadata(meta)

    # --- append-only logs ----------------------------------------------------
    def _next_id(self, path: Path, prefix: str) -> str:
        return f"{prefix}_{_count_lines(path):04d}"

    def log_provenance(self, *, actor: str, stage: str, event: str, summary: str,
                       model_id: str | None = None, prompt_hash: str | None = None,
                       inputs: dict | None = None, outputs: dict | None = None,
                       cost: dict | None = None, parent_event_id: str | None = None) -> str:
        assert actor in ("agent", "human"), f"actor must be agent|human, got {actor!r}"
        assert stage in STAGES, f"unknown stage {stage!r}"
        assert event in PROVENANCE_EVENTS, f"unknown event {event!r}"
        event_id = self._next_id(self.provenance_path, "ev")
        _append_jsonl(self.provenance_path, {
            "event_id": event_id, "parent_event_id": parent_event_id,
            "ts": _now_iso(), "run_id": self.read_metadata()["run_id"],
            "actor": actor, "stage": stage, "event": event,
            "model_id": model_id, "prompt_hash": prompt_hash,
            "summary": summary, "inputs": inputs or {}, "outputs": outputs or {},
            "cost": cost,
        })
        if cost:
            self.add_cost(tokens_in=cost.get("tokens_in", 0),
                          tokens_out=cost.get("tokens_out", 0), usd=cost.get("usd"))
        return event_id

    def log_gate(self, *, stage: str, artifact: str, decision: str, review_seconds: int,
                 attention_check_ids: list[str] | None = None, notes: str = "") -> str:
        assert stage in STAGES, f"unknown stage {stage!r}"
        assert decision in GATE_DECISIONS, f"decision must be {GATE_DECISIONS}, got {decision!r}"
        assert review_seconds >= 0, "review_seconds cannot be negative"
        gate_id = self._next_id(self.gates_path, "gt")
        _append_jsonl(self.gates_path, {
            "gate_id": gate_id, "ts": _now_iso(), "run_id": self.read_metadata()["run_id"],
            "stage": stage, "artifact": artifact, "decision": decision,
            "review_seconds": review_seconds,
            "attention_check_ids": attention_check_ids or [], "notes": notes,
        })
        return gate_id

    def log_attention_check(self, *, stage: str, injected_into_gate: str,
                            error_type: str | None, difficulty: str, ground_truth: str,
                            source_provenance_event: str | None = None,
                            two_sided_control: bool = False,
                            caught: bool | None = None) -> str:
        assert stage in STAGES, f"unknown stage {stage!r}"
        # A two-sided control is a CORRECT item (no injected error), so it has no
        # error_type; a defect must name one from the real-mistake distribution.
        if two_sided_control:
            assert error_type is None, "two-sided control must not carry an error_type"
        else:
            assert error_type in ERROR_TYPES, f"unknown error_type {error_type!r}"
        assert difficulty in DIFFICULTIES, f"difficulty must be {DIFFICULTIES}, got {difficulty!r}"
        ac_id = self._next_id(self.attention_checks_path, "ac")
        _append_jsonl(self.attention_checks_path, {
            "ac_id": ac_id, "ts": _now_iso(), "run_id": self.read_metadata()["run_id"],
            "stage": stage, "injected_into_gate": injected_into_gate,
            "error_type": error_type, "difficulty": difficulty,
            "source_provenance_event": source_provenance_event,
            "ground_truth": ground_truth, "two_sided_control": two_sided_control,
            "caught": caught, "caught_at": _now_iso() if caught is not None else None,
        })
        return ac_id

    def resolve_attention_check(self, ac_id: str, caught: bool) -> None:
        """Mark a pending check caught/missed. Append-only: writes a resolution line
        rather than editing the original, preserving the tamper-evident history."""
        _append_jsonl(self.attention_checks_path, {
            "ac_id": ac_id, "ts": _now_iso(), "run_id": self.read_metadata()["run_id"],
            "event": "resolution", "caught": caught, "caught_at": _now_iso(),
        })

    # --- reads ---------------------------------------------------------------
    def read_log(self, path: Path) -> list[dict]:
        if not path.exists():
            return []
        with open(path) as f:
            return [json.loads(line) for line in f if line.strip()]
