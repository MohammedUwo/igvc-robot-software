#!/usr/bin/env python3
import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description="Batch generate IGVC dynamic courses")
    parser.add_argument("--scenario", default="normal")
    parser.add_argument("--count", type=int, default=100)
    parser.add_argument("--start-seed", type=int, default=1)
    args = parser.parse_args()
    failures = []
    sdf_parse_failures = 0
    for i in range(args.count):
        seed = args.start_seed + i
        cmd = [sys.executable, "scripts/generate_course.py", "--seed", str(seed), "--scenario", args.scenario]
        result = subprocess.run(cmd, cwd=ROOT, text=True, capture_output=True)
        if result.returncode != 0 or "Validation: PASS" not in result.stdout:
            failures.append({"seed": seed, "stdout": result.stdout, "stderr": result.stderr})
    valid = args.count - len(failures)
    log_path = ROOT / "generated" / f"batch_failures_{args.scenario}.log"
    log_path.parent.mkdir(exist_ok=True)
    with open(log_path, "w", encoding="utf-8") as f:
        for failure in failures:
            f.write(f"seed: {failure['seed']}\n")
            f.write(failure["stdout"])
            f.write(failure["stderr"])
            f.write("\n---\n")
    print(f"{valid} valid worlds generated")
    print(f"{len(failures)} validation failures")
    print(f"{sdf_parse_failures} SDF parse failures")
    print(f"failed seeds logged: {log_path}")
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
