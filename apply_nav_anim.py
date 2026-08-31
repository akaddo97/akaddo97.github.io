#!/usr/bin/env python3
"""Make the nav animation on every page a pure function of nav_anim.js.

The effect used to live inline on the homepage only, which is why clicking
[AI fluency] took you to a page whose nav did not move at all. It now runs on
every page and unpacks out of that page's own nav item, so it has to be the
same code in five places. One file, propagated, on the apply_links.py pattern.

Each page carries the block between two markers:

    <!-- NAV-ANIM:START -->
    <script> ... </script>
    <!-- NAV-ANIM:END -->

A page with a .navrow and no markers gets the block inserted before </body>.
A page with no nav (media/) is skipped and reported as such.

    python3 apply_nav_anim.py            dry run, the default
    python3 apply_nav_anim.py --commit   write the files
    python3 apply_nav_anim.py --check    exit 1 if a page and nav_anim.js differ

Stdlib only. Run it from anywhere; paths resolve against this file.
"""
import argparse, pathlib, re, sys

ROOT = pathlib.Path(__file__).resolve().parent
SOURCE = ROOT / "nav_anim.js"
START = "<!-- NAV-ANIM:START -->"
END = "<!-- NAV-ANIM:END -->"
BLOCK = re.compile(re.escape(START) + r".*?" + re.escape(END), re.S)

PAGES = ["index.html", "build/index.html", "learn/index.html",
         "pricing/index.html", "cv/index.html", "media/index.html"]


def block():
    js = SOURCE.read_text().rstrip("\n")
    return START + "\n<script>\n" + js + "\n</script>\n" + END


def apply_to(text, want):
    """Return the page with the block in it, or None if it has no nav."""
    if BLOCK.search(text):
        return BLOCK.sub(lambda m: want, text, count=1)
    if "navrow" not in text:
        return None
    if "</body>" not in text:
        return None
    return text.replace("</body>", want + "\n</body>", 1)


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--commit", action="store_true", help="write the files")
    ap.add_argument("--check", action="store_true", help="exit 1 on drift")
    args = ap.parse_args()

    if not SOURCE.exists():
        sys.exit(f"missing {SOURCE}")
    want = block()

    changed, skipped = [], []
    for rel in PAGES:
        path = ROOT / rel
        if not path.exists():
            sys.exit(f"missing {path}")
        text = path.read_text()
        out = apply_to(text, want)
        if out is None:
            skipped.append(rel)
            continue
        if out == text:
            print(f"  ok       {rel}")
            continue
        changed.append(rel)
        verb = "install" if BLOCK.search(text) is None else "update"
        print(f"  {verb:<8} {rel}")
        if args.commit:
            path.write_text(out)

    for rel in skipped:
        print(f"  no nav   {rel}")

    if args.check and changed:
        print(f"\n{len(changed)} page(s) differ from nav_anim.js. "
              "Run apply_nav_anim.py --commit.")
        return 1
    if changed and not args.commit:
        print(f"\nDry run. {len(changed)} page(s) would change. "
              "Add --commit to write.")
    elif args.commit:
        print(f"\nWrote {len(changed)} page(s).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
