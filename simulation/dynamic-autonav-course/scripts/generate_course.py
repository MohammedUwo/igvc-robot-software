#!/usr/bin/env python3
import argparse
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from course_lib import generate_layout, validate_metadata, write_outputs


def main():
    parser = argparse.ArgumentParser(description="Generate a seeded IGVC dynamic AutoNav Gazebo world")
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--scenario", default="normal")
    parser.add_argument("--max-attempts", type=int, default=100)
    parser.add_argument("--template", default="oval_with_chicane")
    args = parser.parse_args()
    seed = args.seed if args.seed is not None else random.SystemRandom().randint(1, 999999999)
    try:
        metadata = generate_layout(seed, args.scenario, args.max_attempts, args.template)
        world_path, meta_path, preview_path = write_outputs(metadata)
        checks = validate_metadata(metadata)
        passed = all(p for _, p, _ in checks) and metadata["validation"].get("sdf_check") == "passed"
        metadata["validation"]["passed"] = bool(passed)
        # Rewrite metadata after validation finalization.
        import yaml
        meta_path.write_text(yaml.safe_dump(metadata, sort_keys=False, default_flow_style=False), encoding="utf-8")
        print(f"Generated course seed: {seed}")
        print(f"Scenario: {args.scenario}")
        print(f"Template: {args.template}")
        print(f"World: {world_path.relative_to(Path.cwd()) if world_path.is_absolute() else world_path}")
        print(f"Metadata: {meta_path.relative_to(Path.cwd()) if meta_path.is_absolute() else meta_path}")
        print(f"Preview: {preview_path.relative_to(Path.cwd()) if preview_path.is_absolute() else preview_path}")
        print(f"Validation: {'PASS' if passed else 'FAIL'}")
        if not passed:
            for name, ok, msg in checks:
                if not ok:
                    print(f"FAILED: {name} {msg}")
            return 1
        return 0
    except Exception as exc:
        print(str(exc), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
