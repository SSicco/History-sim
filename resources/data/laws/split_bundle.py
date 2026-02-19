#!/usr/bin/env python3
"""
Split the laws_bundle.json into individual law JSON files.
Run from the laws directory:
  cd resources/data/laws
  python split_bundle.py
"""

import json
import os
import sys

BUNDLE_FILE = "laws_bundle.json"
OUTPUT_DIR = "."  # Current directory

def main():
    if not os.path.exists(BUNDLE_FILE):
        print(f"ERROR: {BUNDLE_FILE} not found in current directory")
        print(f"Make sure you're running this from the laws/ directory")
        sys.exit(1)
    
    with open(BUNDLE_FILE, 'r', encoding='utf-8') as f:
        bundle = json.load(f)
    
    print(f"Reading {len(bundle)} files from bundle...")
    
    for fname, data in bundle.items():
        outpath = os.path.join(OUTPUT_DIR, fname)
        with open(outpath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        size = os.path.getsize(outpath)
        print(f"  + {fname}: {size:,} bytes")
    
    print(f"\nDone! {len(bundle)} files written to {os.path.abspath(OUTPUT_DIR)}")
    print("You can now delete laws_bundle.json and split_bundle.py")

if __name__ == "__main__":
    main()
