#!/usr/bin/env python3
"""
Query start.spring.io for available dependencies.

Usage:
  python3 search-deps.py              # show all dependencies
  python3 search-deps.py security     # filter by keyword (name, id, or description)
  python3 search-deps.py --versions   # show only Boot and Java version options
"""
import json
import sys
import urllib.request

INITIALIZR_URL = "https://start.spring.io"


def fetch_metadata():
    req = urllib.request.Request(INITIALIZR_URL, headers={"Accept": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.load(resp)
    except Exception as e:
        print(f"Error: could not reach {INITIALIZR_URL} — {e}", file=sys.stderr)
        sys.exit(1)


def print_versions(data):
    print("=== Spring Boot versions ===")
    for v in data["bootVersion"]["values"]:
        tag = "  ← default" if v["id"] == data["bootVersion"]["default"] else ""
        print(f"  {v['id']:<20} {v.get('name', '')}{tag}")

    print("\n=== Java versions ===")
    for v in data["javaVersion"]["values"]:
        tag = "  ← default" if v["id"] == data["javaVersion"]["default"] else ""
        print(f"  {v['id']}{tag}")


def print_deps(data, search: str):
    boot = data["bootVersion"]["default"]
    java = data["javaVersion"]["default"]
    print(f"Spring Boot: {boot}  |  Java default: {java}\n")

    total = 0
    for group in data["dependencies"]["values"]:
        matches = [
            d for d in group["values"]
            if not search
            or search in d["name"].lower()
            or search in d["id"].lower()
            or search in d.get("description", "").lower()
        ]
        if not matches:
            continue

        print(f"── {group['name']}")
        for dep in matches:
            print(f"   {dep['id']:<32} {dep['name']}")
            desc = dep.get("description", "")
            if desc:
                # Wrap description at 76 chars, indented to align under name
                indent = "   " + " " * 32 + " "
                words, line = [], ""
                for word in desc.split():
                    if len(line) + len(word) + 1 > 76:
                        print(f"{indent}{line}")
                        line = word
                    else:
                        line = f"{line} {word}".lstrip()
                if line:
                    print(f"{indent}{line}")

            links = dep.get("_links", {})
            if links:
                print(f"   {'':32}  Links:")
                for rel, entries in links.items():
                    if isinstance(entries, dict):
                        entries = [entries]
                    for entry in entries:
                        title = entry.get("title", rel)
                        href = entry.get("href", "")
                        if not entry.get("templated"):
                            print(f"   {'':32}    [{rel}] {title}")
                            print(f"   {'':32}          {href}")

            total += 1
        print()

    if search and total == 0:
        print(f"No dependencies matched '{search}'.")


def main():
    args = sys.argv[1:]
    data = fetch_metadata()

    if "--versions" in args:
        print_versions(data)
    else:
        search = args[0].lower() if args else ""
        print_deps(data, search)


if __name__ == "__main__":
    main()
