#!/usr/bin/env python3
"""
Batch Chapter Converter — Runs chapter_converter.py on a range of chapters.

Usage:
  # Convert chapters 8 through 15
  python tools/batch_convert.py 8 15

  # Convert a single chapter
  python tools/batch_convert.py 12 12

  # Dry-run (show event plans only, no conversion)
  python tools/batch_convert.py 8 15 --dry-run

  # Resume any interrupted chapters in the range
  python tools/batch_convert.py 8 15 --resume

  # Use a specific model
  python tools/batch_convert.py 8 15 --model claude-sonnet-4-20250514

  # Skip chapters that already have output JSON
  python tools/batch_convert.py 8 15 --skip-existing

Notes:
  - Requires ANTHROPIC_API_KEY environment variable to be set.
  - Chapter N maps to source file  chapter{N}.txt  and chapter-id  2.{N}
  - Output lands in resources/data/chapter_02_{NN}.json
  - A summary is printed at the end showing pass/fail for each chapter.
  - If a chapter fails, subsequent chapters still run (no early abort).
"""

import os
import sys
import subprocess
import argparse
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CONVERTER = PROJECT_ROOT / "tools" / "chapter_converter.py"
SOURCE_DIR = PROJECT_ROOT / "resources" / "source_material" / "book2"
DATA_DIR = PROJECT_ROOT / "resources" / "data"


def output_exists(chapter_num):
    """Check if the output JSON for a chapter already exists."""
    return (DATA_DIR / f"chapter_02_{chapter_num:02d}.json").exists()


def source_exists(chapter_num):
    """Check if the source text for a chapter exists."""
    return (SOURCE_DIR / f"chapter{chapter_num}.txt").exists()


def run_chapter(chapter_num, extra_args):
    """Run chapter_converter.py for a single chapter. Returns True on success."""
    source_file = f"chapter{chapter_num}.txt"
    chapter_id = f"2.{chapter_num}"

    cmd = [
        sys.executable,
        str(CONVERTER),
        source_file,
        "--chapter-id", chapter_id,
    ] + extra_args

    print(f"\n{'='*70}")
    print(f"  CHAPTER {chapter_num}  ({source_file} -> chapter_02_{chapter_num:02d}.json)")
    print(f"  Command: {' '.join(cmd)}")
    print(f"{'='*70}\n")

    result = subprocess.run(cmd, cwd=str(PROJECT_ROOT))
    return result.returncode == 0


def main():
    parser = argparse.ArgumentParser(
        description="Batch-convert a range of chapters using chapter_converter.py"
    )
    parser.add_argument(
        "start", type=int,
        help="First chapter number to convert (e.g. 8)",
    )
    parser.add_argument(
        "end", type=int,
        help="Last chapter number to convert, inclusive (e.g. 15)",
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Pass --dry-run to each chapter (plan only, no conversion)",
    )
    parser.add_argument(
        "--resume", action="store_true",
        help="Pass --resume to each chapter (retry failed events)",
    )
    parser.add_argument(
        "--model", default=None,
        help="Override the Claude model used for conversion",
    )
    parser.add_argument(
        "--skip-existing", action="store_true",
        help="Skip chapters that already have an output JSON file",
    )
    args = parser.parse_args()

    # Validate
    if args.start > args.end:
        print(f"ERROR: start ({args.start}) must be <= end ({args.end})")
        sys.exit(1)

    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("ERROR: Set the ANTHROPIC_API_KEY environment variable first.")
        print("  Windows:  set ANTHROPIC_API_KEY=sk-ant-...")
        print("  Mac/Linux: export ANTHROPIC_API_KEY=sk-ant-...")
        sys.exit(1)

    # Build extra args to forward
    extra = []
    if args.dry_run:
        extra.append("--dry-run")
    if args.resume:
        extra.append("--resume")
    if args.model:
        extra.extend(["--model", args.model])

    # Determine which chapters to process
    chapters = list(range(args.start, args.end + 1))
    skipped = []
    missing = []
    to_process = []

    for ch in chapters:
        if not source_exists(ch):
            missing.append(ch)
        elif args.skip_existing and output_exists(ch):
            skipped.append(ch)
        else:
            to_process.append(ch)

    # Report plan
    total = len(chapters)
    print(f"\n{'='*70}")
    print(f"  BATCH CONVERSION — Chapters {args.start} to {args.end}")
    print(f"{'='*70}")
    print(f"  Total in range:  {total}")
    print(f"  To process:      {len(to_process)}  {to_process}")
    if skipped:
        print(f"  Skipped (exist): {len(skipped)}  {skipped}")
    if missing:
        print(f"  Missing source:  {len(missing)}  {missing}")
    if args.dry_run:
        print(f"  Mode: DRY RUN (plan only)")
    if args.resume:
        print(f"  Mode: RESUME (retry failed events)")
    print()

    if not to_process:
        print("Nothing to process. Done.")
        return

    # Process each chapter
    results = {}
    start_time = time.time()

    for i, ch in enumerate(to_process, 1):
        print(f"\n>>> Processing {i}/{len(to_process)} <<<")
        ch_start = time.time()
        success = run_chapter(ch, extra)
        ch_elapsed = time.time() - ch_start
        results[ch] = ("PASS" if success else "FAIL", ch_elapsed)

    total_elapsed = time.time() - start_time

    # Summary
    print(f"\n\n{'='*70}")
    print(f"  BATCH SUMMARY")
    print(f"{'='*70}")
    passed = sum(1 for s, _ in results.values() if s == "PASS")
    failed = sum(1 for s, _ in results.values() if s == "FAIL")

    for ch in sorted(results):
        status, elapsed = results[ch]
        mins = int(elapsed // 60)
        secs = int(elapsed % 60)
        marker = "OK" if status == "PASS" else "FAILED"
        print(f"  Chapter {ch:>2}:  {marker:<8}  ({mins}m {secs}s)")

    if skipped:
        for ch in skipped:
            print(f"  Chapter {ch:>2}:  SKIPPED  (output already exists)")
    if missing:
        for ch in missing:
            print(f"  Chapter {ch:>2}:  MISSING  (no source file)")

    total_mins = int(total_elapsed // 60)
    total_secs = int(total_elapsed % 60)
    print(f"\n  Passed: {passed}  |  Failed: {failed}  |  Total time: {total_mins}m {total_secs}s")

    if failed:
        print(f"\n  TIP: Re-run with --resume to retry failed chapters:")
        fail_nums = [ch for ch in sorted(results) if results[ch][0] == "FAIL"]
        print(f"    python tools/batch_convert.py {fail_nums[0]} {fail_nums[-1]} --resume")
        sys.exit(1)

    print("\n  All chapters converted successfully!")


if __name__ == "__main__":
    main()
