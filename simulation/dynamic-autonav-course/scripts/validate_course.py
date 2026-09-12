#!/usr/bin/env python3
import argparse
import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
from course_lib import validate_metadata


def main():
    parser = argparse.ArgumentParser(description="Validate generated IGVC course metadata")
    parser.add_argument("metadata")
    args = parser.parse_args()
    path = Path(args.metadata)
    if not path.is_absolute():
        path = Path.cwd() / path
    if not path.exists():
        print(f"Metadata file not found: {path}", file=sys.stderr)
        return 1
    metadata = yaml.safe_load(path.read_text())
    checks = validate_metadata(metadata)
    print(f"Validation report for seed {metadata['seed']}")
    print(f"Scenario: {metadata['scenario']}")
    print()
    for name, ok, msg in checks:
        print(f"[{'PASS' if ok else 'FAIL'}] {name}")
        if msg and not ok:
            print(f"       {msg}")
    passed = all(ok for _, ok, _ in checks)
    print()
    print(f"Validation: {'PASS' if passed else 'FAIL'}")
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
