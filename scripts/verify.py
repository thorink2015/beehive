"""Sanity-check the beehiiv connection and list recent posts. Reads only.

Usage:
    python scripts/verify.py
"""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent))
from beehiiv_client import list_posts


def main() -> None:
    data = list_posts(limit=5).get("data", [])
    if not data:
        print("Connected, but no posts found yet.")
        return
    print("Connected. Most recent posts:")
    for p in data:
        print(f"  - {p.get('title', '(untitled)')}  [{p.get('status', '?')}]  id={p.get('id')}")


if __name__ == "__main__":
    main()
