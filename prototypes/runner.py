"""CLI and immutable artifact writer for the article prototype pack."""

from __future__ import annotations

import argparse
import importlib
import json
import platform
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SCENARIOS = {
    "01": "External memory and retrieval",
    "02": "Binary networks and XNOR/popcount",
    "03": "Single agent versus parallel agents",
    "04": "Agent navigation in a large repository",
    "05": "Tiny Transformer CPU training",
    "06": "RNN versus Transformer under a compute budget",
    "07": "Python versus native code",
    "08": "Overfitting and data leakage",
    "09": "Safe infrastructure operator",
    "10": "Lookahead bias in a backtest",
    "11": "Agent fault recovery",
    "12": "Serving cost calculator",
    "13": "Long-term agent memory",
    "14": "End-to-end RAG failure diagnosis",
    "15": "Benchmark uncertainty and sample size",
}
DEFAULT_RESULTS = Path(__file__).resolve().parent / "results"


def list_scenarios() -> list[dict[str, str]]:
    return [{"id": article_id, "title": title} for article_id, title in SCENARIOS.items()]


def _safe_id(article_id: str) -> str:
    value = str(article_id).strip()
    if value not in SCENARIOS:
        raise ValueError(f"Unknown article scenario: {value!r}")
    return value


def write_artifact(
    article_id: str,
    seed: int,
    result: dict[str, Any],
    output_dir: Path,
) -> Path:
    article_id = _safe_id(article_id)
    if not isinstance(result, dict):
        raise TypeError("Scenario result must be a dictionary")
    evidence_type = result.get("evidence_type")
    if evidence_type not in {"synthetic", "simulation", "measured", "computed"}:
        raise ValueError("Scenario result must declare a supported evidence_type")
    if "limitations" not in result:
        raise ValueError("Scenario result must declare limitations")

    created = datetime.now(timezone.utc)
    payload = {
        **result,
        "article_id": article_id,
        "title": SCENARIOS[article_id],
        "seed": int(seed),
        "created_utc": created.isoformat(),
        "python_version": platform.python_version(),
        "runtime_platform": platform.platform(),
        "runtime_machine": platform.machine(),
    }
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    stamp = created.strftime("%Y%m%dT%H%M%S.%fZ")
    path = output_dir / f"article-{article_id}-{stamp}-{uuid.uuid4().hex[:8]}-seed-{seed}.json"
    with path.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(payload, stream, ensure_ascii=False, indent=2, sort_keys=True)
        stream.write("\n")
    return path


def run_scenario(article_id: str, seed: int = 42, output_dir: Path | None = None) -> Path:
    article_id = _safe_id(article_id)
    module = importlib.import_module(f"prototypes.scenarios.article{article_id}")
    result = module.run(seed=seed)
    destination = output_dir or DEFAULT_RESULTS
    return write_artifact(article_id, seed, result, Path(destination))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m prototypes")
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("list", help="list the 15 article scenarios")
    run_parser = commands.add_parser("run", help="run one scenario")
    run_parser.add_argument("article_id", help="article number, 01 through 15")
    run_parser.add_argument("--seed", type=int, default=42)
    run_parser.add_argument("--out", type=Path, default=DEFAULT_RESULTS)
    args = parser.parse_args(argv)

    if args.command == "list":
        for row in list_scenarios():
            print(f"{row['id']}  {row['title']}")
        return 0
    try:
        path = run_scenario(args.article_id, seed=args.seed, output_dir=args.out)
    except (ValueError, ImportError, TypeError) as exc:
        parser.error(str(exc))
    print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
