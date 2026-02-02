#!/usr/bin/env python3
"""
compare_line_counts.py

Scan two result directories (one for UniParser, one for Drain) and compare the number of lines
for each dataset file named like: {dataset}.log_templates.csv

Default directory layout expected (as provided):
    result/result_UniParser_2k/{dataset}.log_templates.csv
    result/result_Drain_2k/{dataset}.log_templates.csv

Usage examples:
    python compare_line_counts.py
    python compare_line_counts.py --base result --parser1 UniParser --parser2 Drain --suffix .log_templates.csv
    python compare_line_counts.py --ignore-header --out differences.csv

Options:
    --base           Base folder containing the result_* folders (default: "result")
    --parser1        Name of first parser folder token (default: "UniParser")
    --parser2        Name of second parser folder token (default: "Drain")
    --suffix         File suffix (default: ".log_templates.csv")
    --ignore-header  Subtract 1 from each file's line count (useful if files include a single header row)
    --only-diff      Show only datasets where counts differ
    --out            Optional CSV path to save the comparison (columns: dataset, parser1_count, parser2_count, diff)

The script is defensive: it reports datasets that exist only for one parser, and continues when files cannot be read.
"""

import argparse
import os
import glob
import csv
import sys
from typing import Dict, Tuple


def count_lines(path: str) -> int:
    """Efficiently count newline characters in a file (binary mode)."""
    try:
        with open(path, "rb") as f:
            # read in chunks
            count = 0
            for chunk in iter(lambda: f.read(1024 * 1024), b""):
                count += chunk.count(b"\n")
        return count
    except Exception as e:
        print(f"WARNING: failed to read {path}: {e}", file=sys.stderr)
        return -1


def scan_parser(base: str, parser_token: str, suffix: str) -> Dict[str, str]:
    """Return mapping dataset -> filepath for files in the parser directory.
    Expects files named <dataset>{suffix}.
    """
    folder = os.path.join(base, f"result_{parser_token}_2k")
    if not os.path.isdir(folder):
        # try alternative without the "result_" prefix in case of slightly different layout
        alt = os.path.join(base, parser_token)
        if os.path.isdir(alt):
            folder = alt
        else:
            # return empty mapping but warn
            print(f"WARNING: parser folder not found: {folder}", file=sys.stderr)
            return {}

    pattern = os.path.join(folder, f"*{suffix}")
    paths = glob.glob(pattern)
    mapping = {}
    for p in paths:
        name = os.path.basename(p)
        if not name.endswith(suffix):
            continue
        dataset = name[: -len(suffix)]
        mapping[dataset] = p
    return mapping


def main():
    p = argparse.ArgumentParser(description="Compare line counts between two parser result folders")
    p.add_argument("--base", default="result", help="Base folder containing the result_* folders")
    p.add_argument("--parser1", default="UniParser", help="First parser token (default: UniParser)")
    p.add_argument("--parser2", default="Drain", help="Second parser token (default: Drain)")
    p.add_argument("--suffix", default=".log_templates.csv", help="File suffix (default: .log_templates.csv)")
    p.add_argument("--ignore-header", action="store_true", help="Subtract 1 from each file's line count (if there's a header row)")
    p.add_argument("--only-diff", action="store_true", help="Show only datasets where counts differ")
    p.add_argument("--out", default=None, help="Optional CSV output path for the comparison results")

    args = p.parse_args()

    m1 = scan_parser(args.base, args.parser1, args.suffix)
    m2 = scan_parser(args.base, args.parser2, args.suffix)

    all_datasets = sorted(set(m1.keys()) | set(m2.keys()))
    if not all_datasets:
        print("No dataset files found. Check your base path, parser names and suffix.")
        return

    rows = []  # list of tuples (dataset, c1, c2, diff)
    for ds in all_datasets:
        p1 = m1.get(ds)
        p2 = m2.get(ds)
        c1 = count_lines(p1) if p1 else None
        c2 = count_lines(p2) if p2 else None
        if c1 is None:
            c1_display = "MISSING"
            c1_val = -1
        else:
            c1_display = str(c1 - (1 if args.ignore_header and c1 > 0 else 0))
            c1_val = int(c1_display) if c1_display != "MISSING" else -1
        if c2 is None:
            c2_display = "MISSING"
            c2_val = -1
        else:
            c2_display = str(c2 - (1 if args.ignore_header and c2 > 0 else 0))
            c2_val = int(c2_display) if c2_display != "MISSING" else -1
        diff = None
        if c1 is None or c2 is None:
            diff = "N/A"
        else:
            diff = str(c1_val - c2_val)
        rows.append((ds, c1_display, c2_display, diff))

    # print human readable table
    col_names = ("dataset", args.parser1, args.parser2, "diff")
    widths = [max(len(str(r[i])) for r in rows + [col_names]) for i in range(4)]

    header = " | ".join(name.ljust(widths[i]) for i, name in enumerate(col_names))
    sep = "-+-".join("-" * widths[i] for i in range(4))
    print(header)
    print(sep)
    for ds, c1d, c2d, diff in rows:
        if args.only_diff and diff == "0":
            continue
        print(" | ".join(str(x).ljust(widths[i]) for i, x in enumerate((ds, c1d, c2d, diff))))

    # optionally write CSV
    if args.out:
        try:
            with open(args.out, "w", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(["dataset", args.parser1, args.parser2, "diff"])
                for r in rows:
                    writer.writerow(r)
            print(f"Wrote comparison to {args.out}")
        except Exception as e:
            print(f"Failed to write CSV {args.out}: {e}", file=sys.stderr)


if __name__ == "__main__":
    main()

