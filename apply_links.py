#!/usr/bin/env python3
"""Make every outbound link on the site a pure function of links.md.

links.md holds one `key: url` line per link. Each link on the site sits on the
line directly below an HTML comment marker naming its key, for example:

    <!-- FORM:MENTOR -->
    <a class="btn" href="...">Volunteer as a mentor</a>

This script rewrites those hrefs to match links.md, and nothing else. It never
touches an anchor that is not directly under a marker.

    python3 apply_links.py                 dry run, the default
    python3 apply_links.py --commit        write the files
    python3 apply_links.py --check         exit 1 if the site and links.md disagree
    python3 apply_links.py --verify-urls   also check each URL returns 200

Stdlib only. Run it from anywhere; paths resolve against this file.
"""
import argparse, pathlib, re, sys

ROOT = pathlib.Path(__file__).resolve().parent
LINKS = ROOT / "links.md"

# key -> marker. Add a row here and in links.md to introduce a new link.
MARKERS = {
    "booking": "FORM:BOOKING",
    "cv": "FORM:CV",
    "mentor": "FORM:MENTOR",
    "cohort": "FORM:COHORT",
    "vibe": "FORM:VIBE",
}

KEY_LINE = re.compile(r"^\s*([a-z][a-z0-9_]*)\s*:\s*(\S+)\s*$")


def normalise(url):
    """Strip the editor/tracking parameter Google appends to a form share link.

    A URL copied from the Forms publish screen ends in ?usp=publish-editor,
    which is an editor artefact and has no business on a public button.
    """
    m = re.match(r"(https://docs\.google\.com/forms/\S*?/viewform)\?usp=\S+$", url)
    return m.group(1) if m else url


def read_links():
    if not LINKS.exists():
        sys.exit(f"missing {LINKS}")
    out, seen = {}, []
    for n, line in enumerate(LINKS.read_text().splitlines(), 1):
        m = KEY_LINE.match(line)
        if not m:
            continue
        key, url = m.group(1), m.group(2)
        if key not in MARKERS:
            continue
        if key in out:
            sys.exit(f"{LINKS}:{n}: '{key}' is set twice; keep one line per key")
        clean = normalise(url)
        if clean != url:
            seen.append(f"  normalised {key}: dropped the editor parameter")
        out[key] = clean
    for note in seen:
        print(note)
    if not out:
        sys.exit(f"{LINKS}: found no 'key: url' lines")
    return out


def pages():
    return sorted(p for p in ROOT.rglob("*.html") if ".git" not in p.parts)


def scan(links):
    """Yield (path, key, current_href, wanted_href, line_no) for every marker."""
    for path in pages():
        text = path.read_text()
        for key, marker in MARKERS.items():
            pat = re.compile(
                r"(<!--\s*" + re.escape(marker) + r"\s*-->\s*\n\s*<a\b[^>]*?\bhref=\")([^\"]*)(\")"
            )
            for m in pat.finditer(text):
                line = text.count("\n", 0, m.start()) + 1
                yield path, key, m.group(2), links.get(key), line


def apply(links, write):
    """Report what differs, then write. Reporting happens first so the count is
    the number of buttons actually changed, not zero because we already wrote."""
    changed = total = 0
    per_key = {k: 0 for k in MARKERS}
    for path, key, cur, want, line in scan(links):
        total += 1
        per_key[key] += 1
        if want is None:
            print(f"  no url  {path.relative_to(ROOT)}:{line}  {key}  (no '{key}:' line in links.md)")
        elif cur != want:
            changed += 1
            print(f"  {'set    ' if write else 'would  '}{path.relative_to(ROOT)}:{line}  {key}  ->  {want}")
    if write:
        for path in pages():
            text = original = path.read_text()
            for key, marker in MARKERS.items():
                if key not in links:
                    continue
                pat = re.compile(
                    r"(<!--\s*" + re.escape(marker) + r"\s*-->\s*\n\s*<a\b[^>]*?\bhref=\")([^\"]*)(\")"
                )
                text = pat.sub(lambda m: m.group(1) + links[key] + m.group(3), text)
            if text != original:
                path.write_text(text)
    return changed, total, per_key


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--commit", action="store_true", help="write the files")
    ap.add_argument("--check", action="store_true", help="exit 1 if the site disagrees with links.md")
    ap.add_argument("--verify-urls", action="store_true", help="check each URL returns 200")
    a = ap.parse_args()

    links = read_links()
    print(f"{LINKS.name}: " + ", ".join(f"{k}" for k in sorted(links)))

    if a.check:
        bad = [(p, k, c, w, n) for p, k, c, w, n in scan(links) if w is not None and c != w]
        for p, k, c, w, n in bad:
            print(f"  drift  {p.relative_to(ROOT)}:{n}  {k}\n         site: {c}\n         file: {w}")
        print(f"check: {len(bad)} button(s) out of sync")
        return 1 if bad else 0

    changed, total, per_key = apply(links, a.commit)
    counts = ", ".join(f"{k} {v}" for k, v in per_key.items() if v)
    print(f"{total} marked button(s): {counts}")
    print(f"{changed} changed" if a.commit else f"{changed} would change (dry run, use --commit)")

    if a.verify_urls:
        import urllib.request
        for key, url in sorted(links.items()):
            if not url.startswith("http"):
                target = ROOT / url.lstrip("/")
                print(f"  {'ok  ' if target.exists() else 'MISS'} {key}  {url}  (local file)")
                continue
            try:
                req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
                with urllib.request.urlopen(req, timeout=20) as r:
                    print(f"  {r.status}  {key}  {url}")
            except Exception as e:  # noqa: BLE001 - a report, not a control path
                print(f"  FAIL {key}  {url}  {e}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
