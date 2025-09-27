from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path
from typing import Annotated

import typer
from pydantic import BaseModel
from rich import print

from .pcap import Justification, PCAP, ProofRef

app = typer.Typer(help="Orchestrator: build PCAPs and prepare hermetic workspace.")

ROOT = Path(__file__).resolve().parents[2]
EXAMPLES = ROOT / "examples"
OUT = ROOT / "out"
WORK = OUT / "workspace"


class Obligations(BaseModel):
    function_name: str
    type_signature: str
    properties: list[str]


def sha256_of_files(paths: list[Path]) -> str:
    h = hashlib.sha256()
    for p in sorted(paths):
        h.update(p.read_bytes())
        h.update(str(p).encode())
    return h.hexdigest()


def prepare_workspace(candidate: Path) -> tuple[Path, Path]:
    if WORK.exists():
        shutil.rmtree(WORK)
    (WORK / "candidates").mkdir(parents=True, exist_ok=True)
    (WORK / "tests").mkdir(parents=True, exist_ok=True)
    # Copy candidate as candidates/impl.py
    shutil.copy(candidate, WORK / "candidates" / "impl.py")
    # Copy tests
    src_tests = EXAMPLES / "proofs" / "tests"
    shutil.copytree(src_tests, WORK / "tests", dirs_exist_ok=True)
    return WORK / "candidates" / "impl.py", WORK / "tests"


CandidateOption = Annotated[
    Path, typer.Option("--candidate", "-c", exists=True, help="Path to candidate .py file")
]
ObligationsOption = Annotated[
    Path, typer.Option("--obligations", exists=True, help="Path to obligations JSON")
]
OutOption = Annotated[Path, typer.Option("--out", help="Output PCAP file")]


@app.command("build-pcap")
def build_pcap(
    candidate: CandidateOption,
    obligations_path: ObligationsOption = EXAMPLES / "constraints" / "obligations.simple.json",
    out: OutOption = OUT / "pcap.add.json",
):
    OUT.mkdir(exist_ok=True, parents=True)
    impl_py, tests_dir = prepare_workspace(candidate)
    obligations = json.loads(obligations_path.read_text())
    # Compute context hash on candidate + tests + obligations
    files = [impl_py, obligations_path] + list(tests_dir.rglob("*.py"))
    ctx = sha256_of_files(files)
    pcap = PCAP(
        action="code_change",
        context_hash=ctx,
        obligations=obligations,
        proofs=[
            ProofRef(kind="unit_test", path=str(Path("tests") / "test_add.py")),
            ProofRef(kind="static", path="ruff"),
            ProofRef(kind="static", path="mypy"),
        ],
        justification=Justification(exec_time_est=0.1, audit_cost_est=0.2),
        metadata={"demo": True, "candidate": str(candidate)},
    )
    out.write_text(pcap.model_dump_json(indent=2))
    print(f"[green]PCAP written to[/green] {out}")
    print(f"[cyan]Workspace prepared at[/cyan] {WORK}")


if __name__ == "__main__":
    app()
