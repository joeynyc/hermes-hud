"""Compare agent collector latency in isolated baseline/candidate workers."""

from __future__ import annotations

import argparse
import json
import os
import sqlite3
import statistics
import subprocess
import sys
import tarfile
import tempfile
from io import BytesIO
from pathlib import Path


WORKER = r'''
import json
import sys
import time
from dataclasses import asdict
from pathlib import Path

from hermes_hud.collectors import agents

worktree, hermes_dir, sample_count, warmups, suffix = sys.argv[1:]
worktree = Path(worktree).resolve()
agents_file = Path(agents.__file__).resolve()
if not agents_file.is_relative_to(worktree):
    raise RuntimeError(f"imported {agents_file} outside {worktree}")

agents.AGENT_PROCESSES = [
    (f"bench-{i}", f"__hermes_hud_bench_missing_{suffix}_{i}__")
    for i in range(8)
]
agents._list_tmux_panes = lambda: []

def collect():
    return agents.collect_agents(hermes_dir)

def assert_fixture(state):
    if any(process.running for process in state.processes):
        raise RuntimeError("fixture unexpectedly matched a running process")
    if len(state.recent_sessions) != 3:
        raise RuntimeError(
            f"fixture expected 3 recent sessions, got {len(state.recent_sessions)}"
        )

for _ in range(int(warmups)):
    assert_fixture(collect())

timings = []
output = None
for _ in range(int(sample_count)):
    started = time.perf_counter_ns()
    state = collect()
    timings.append((time.perf_counter_ns() - started) / 1_000_000)
    assert_fixture(state)
    current = json.dumps(asdict(state), default=str, sort_keys=True)
    if output is None:
        output = current
    elif current != output:
        raise RuntimeError("collector output changed within worker")

print(json.dumps({"agents_file": str(agents_file), "output": output, "timings": timings}))
'''


def _nearest_rank(samples: list[float], percentile: int) -> float:
    ordered = sorted(samples)
    rank = (percentile * len(ordered) + 99) // 100
    return ordered[rank - 1]


def _summary(samples: list[float]) -> str:
    return (
        f"n={len(samples)} median={statistics.median(samples):.2f}ms "
        f"p95={_nearest_rank(samples, 95):.2f}ms "
        f"p99={_nearest_rank(samples, 99):.2f}ms "
        f"max={max(samples):.2f}ms"
    )


def _fixture(root: Path) -> Path:
    hermes = root / "hermes"
    hermes.mkdir()
    (hermes / "state.db").touch()
    connection = sqlite3.connect(hermes / "state.db")
    connection.execute(
        "CREATE TABLE sessions (id TEXT PRIMARY KEY, source TEXT, title TEXT, "
        "started_at REAL, ended_at REAL, model TEXT)"
    )
    connection.execute(
        "CREATE TABLE messages (id TEXT PRIMARY KEY, session_id TEXT, "
        "tool_calls TEXT)"
    )
    sessions = [
        ("sess-0", "cli", "Test session 0", 1700000000, 1700003600, "model"),
        ("sess-1", "cli", "Test session 1", 1700086400, 1700090000, "model"),
        ("sess-2", "telegram", "Test session 2", 1700172800, 1700176400, "model"),
    ]
    messages = [
        ("msg-0", "sess-0", '[{"function":{"name":"terminal"}}]'),
        ("msg-1", "sess-0", "[]"),
        ("msg-2", "sess-1", '[{"function":{"name":"read_file"}}]'),
        ("msg-3", "sess-1", "[]"),
        ("msg-4", "sess-2", '[{"function":{"name":"terminal"}}]'),
        ("msg-5", "sess-2", "[]"),
    ]
    connection.executemany("INSERT INTO sessions VALUES (?,?,?,?,?,?)", sessions)
    connection.executemany("INSERT INTO messages VALUES (?,?,?)", messages)
    connection.commit()
    connection.close()
    return hermes


def _baseline_worktree(ref: str, root: Path) -> tuple[Path, str]:
    result = subprocess.run(
        ["git", "rev-parse", ref], check=True, cwd=Path.cwd(),
        capture_output=True, text=True,
    )
    archive = subprocess.run(
        ["git", "archive", ref], check=True, cwd=Path.cwd(),
        stdout=subprocess.PIPE,
    ).stdout
    destination = root / "baseline"
    destination.mkdir()
    with tarfile.open(fileobj=BytesIO(archive), mode="r:") as tar:
        tar.extractall(destination)
    return destination, result.stdout.strip()


def _run_batch(
    worktree: Path, hermes: Path, samples: int, warmups: int, suffix: str,
) -> dict:
    env = os.environ.copy()
    env.pop("PYTHONPATH", None)
    result = subprocess.run(
        [
            sys.executable, "-c", WORKER, str(worktree), str(hermes),
            str(samples), str(warmups), suffix,
        ],
        cwd=worktree, env=env, check=True, capture_output=True, text=True,
    )
    return json.loads(result.stdout)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--baseline-ref", default="origin/main")
    parser.add_argument("--samples-per-batch", type=int, default=100)
    parser.add_argument("--warmups", type=int, default=5)
    args = parser.parse_args()
    if args.samples_per_batch <= 0 or args.warmups <= 0:
        parser.error("--samples-per-batch and --warmups must be positive")
    if args.samples_per_batch * 3 < 300:
        parser.error("three batches must produce at least 300 samples per version")

    with tempfile.TemporaryDirectory(prefix="hermes-hud-agent-bench-") as temp:
        root = Path(temp)
        hermes = _fixture(root)
        baseline, baseline_sha = _baseline_worktree(args.baseline_ref, root)
        candidate = Path.cwd().resolve()
        candidate_sha = subprocess.run(
            ["git", "rev-parse", "HEAD"], check=True, cwd=candidate,
            capture_output=True, text=True,
        ).stdout.strip()
        all_samples = {"baseline": [], "candidate": []}
        expected_output = None
        imported_files = {}

        print(f"baseline_ref={args.baseline_ref} baseline_sha={baseline_sha}")
        print(f"candidate_sha={candidate_sha} fixture={hermes}")
        print("tmux=_list_tmux_panes mocked to [] in both workers")

        for batch in range(3):
            order = ("baseline", "candidate") if batch % 2 == 0 else ("candidate", "baseline")
            batch_outputs = {}
            for label in order:
                worktree = baseline if label == "baseline" else candidate
                result = _run_batch(
                    worktree, hermes, args.samples_per_batch, args.warmups,
                    "nomatch",
                )
                imported_files[label] = result["agents_file"]
                batch_outputs[label] = result["output"]
                all_samples[label].extend(result["timings"])
                print(f"batch={batch + 1} order={','.join(order)} {label} {_summary(result['timings'])}")

            if batch_outputs["baseline"] != batch_outputs["candidate"]:
                raise RuntimeError("baseline/candidate dataclass output differs")
            if expected_output is None:
                expected_output = batch_outputs["baseline"]
            elif batch_outputs["baseline"] != expected_output:
                raise RuntimeError("collector output changed between batches")

        print(f"baseline_agents_file={imported_files['baseline']}")
        print(f"candidate_agents_file={imported_files['candidate']}")
        print("combined")
        for label in ("baseline", "candidate"):
            print(f"{label} {_summary(all_samples[label])}")
        print("fixture=synthetic: 3 sessions, 6 messages; process names guaranteed absent")
        print("measurement=collector calls only, timed inside imported worker with perf_counter_ns")
        print("limitation=tmux panes explicitly isolated; no matched live-agent / tmux-preview workload")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
