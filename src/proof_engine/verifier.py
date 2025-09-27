from __future__ import annotations

import hashlib
import hmac
import json
import os
import shutil
import subprocess
import sys
import time
from importlib import metadata as md
from pathlib import Path

import typer
from jsonschema import validate
from rich import print

from .pcap import PCAP

app = typer.Typer(help="Formal Verifier: validate PCAP, run checks, emit attestation.")

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "out"
WORK = OUT / "workspace"
ATTEST = OUT / "attestations"
SCHEMAS = ROOT / "src" / "proof_engine" / "schemas"


def run(cmd: list[str], cwd: Path) -> tuple[int, str]:
    p = subprocess.run(
        cmd, cwd=str(cwd), stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True
    )
    return p.returncode, p.stdout


def demo_sign(payload: bytes) -> str:
    key = os.environ.get("DEMO_SECRET", "demo-secret").encode()
    return hmac.new(key, payload, hashlib.sha256).hexdigest()


def main(pcap: Path = typer.Option(..., exists=True)):
    ATTEST.mkdir(parents=True, exist_ok=True)
    pcap_obj = PCAP.model_validate_json(pcap.read_text())
    schema = json.loads((SCHEMAS / "pcap.schema.json").read_text())
    validate(instance=json.loads(pcap.read_text()), schema=schema)

    # Reconstruct workspace from PCAP metadata
    if WORK.exists():
        shutil.rmtree(WORK)
    (WORK / "candidates").mkdir(parents=True, exist_ok=True)
    (WORK / "tests").mkdir(parents=True, exist_ok=True)
    
    # Get candidate path from PCAP metadata
    candidate_path = Path(pcap_obj.metadata.get("candidate", "examples/candidates/add_v1.py"))
    if not candidate_path.is_absolute():
        candidate_path = ROOT / candidate_path
    
    # Copy candidate as candidates/impl.py
    shutil.copy(candidate_path, WORK / "candidates" / "impl.py")
    
    # Copy tests
    src_tests = ROOT / "examples" / "proofs" / "tests"
    shutil.copytree(src_tests, WORK / "tests", dirs_exist_ok=True)

    results = {}

    # Debug: Check workspace contents
    print(f"[yellow]Workspace contents:[/yellow]")
    for item in WORK.rglob("*"):
        print(f"  {item.relative_to(WORK)}")
    
    # Debug: Check if files exist
    impl_file = WORK / "candidates" / "impl.py"
    test_dir = WORK / "tests"
    print(f"[yellow]Files exist:[/yellow]")
    print(f"  impl.py: {impl_file.exists()}")
    print(f"  tests/: {test_dir.exists()}")
    if impl_file.exists():
        print(f"  impl.py content preview: {impl_file.read_text()[:100]}...")

    # Static: ruff
    code_r, code_o = run([sys.executable, "-m", "ruff", "check", "candidates/impl.py"], cwd=WORK)
    results["ruff"] = {"ok": code_r == 0, "output": code_o}
    print(f"[yellow]Ruff result:[/yellow] ok={code_r == 0}, output={code_o[:200]}...")

    # Static types: mypy
    mypy_r, mypy_o = run(
        [sys.executable, "-m", "mypy", "--python-version", "3.11", "candidates/impl.py"], cwd=WORK
    )
    results["mypy"] = {"ok": mypy_r == 0, "output": mypy_o}
    print(f"[yellow]Mypy result:[/yellow] ok={mypy_r == 0}, output={mypy_o[:200]}...")

    # Unit tests: pytest
    pytest_r, pytest_o = run([sys.executable, "-m", "pytest", "-q"], cwd=WORK)
    results["pytest"] = {"ok": pytest_r == 0, "output": pytest_o}
    print(f"[yellow]Pytest result:[/yellow] ok={pytest_r == 0}, output={pytest_o[:200]}...")

    accepted = all(v["ok"] for v in results.values())

    tool_versions = {
        "python": sys.version,
        "typer": md.version("typer"),
        "click": md.version("click"),
        "pytest": md.version("pytest"),
        "ruff": md.version("ruff"),
        "mypy": md.version("mypy"),
        "jsonschema": md.version("jsonschema"),
    }

    att = {
        "timestamp": int(time.time()),
        "pcap_path": str(pcap),
        "context_hash": pcap_obj.context_hash,
        "accepted": accepted,
        "checks": results,
        "tool_versions": tool_versions,
    }
    payload = json.dumps(att, sort_keys=True).encode()
    att["demo_signature"] = demo_sign(payload)
    out_path = ATTEST / "attestation.json"
    out_path.write_text(json.dumps(att, indent=2))
    print(f"[bold]{'ACCEPTED' if accepted else 'REJECTED'}[/bold] — attestation at {out_path}")
    if not accepted:
        raise typer.Exit(code=1)


if __name__ == "__main__":
    typer.run(main)
