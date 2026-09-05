"""Structure and consistency, without a browser.

Fast and deterministic, so it runs first and fails first. The theme is drift:
this site keeps several hand-written lists of its own pages, and nothing used
to compare any of them to the pages that actually exist.
"""
from __future__ import annotations

import re
import subprocess
import sys
import tempfile
from html.parser import HTMLParser
from pathlib import Path

import pytest

from conftest import PAGES, ROOT, UNLISTED, rel

VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link",
        "meta", "param", "source", "track", "wbr"}


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def load(name: str):
    """Import one of the site's own scripts, to read its lists rather than
    keeping a second copy of them here."""
    import importlib.util

    spec = importlib.util.spec_from_file_location(name, ROOT / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


# --- the site's own checks, as tests ----------------------------------------

@pytest.mark.parametrize("script", ["apply_links.py", "apply_nav_anim.py"])
def test_the_generators_agree_with_the_pages(script):
    """Each already knows how to check itself. Running them here means a push
    cannot land while the site and its single sources disagree."""
    done = subprocess.run([sys.executable, script, "--check"], cwd=ROOT,
                          capture_output=True, text=True, timeout=120)
    assert done.returncode == 0, done.stdout + done.stderr


# --- the lists, against the filesystem --------------------------------------

def test_every_page_with_a_nav_is_in_apply_nav_anim():
    """learn/apply and learn/mentor both carry a nav and were missing from this
    list for a week, so the entrance animation never ran on either."""
    nav = load("apply_nav_anim")
    listed = set(nav.PAGES)
    with_nav = {rel(p) for p in PAGES if "navrow" in read(p)}
    assert with_nav - listed == set(), "pages with a nav that nobody propagates to"


def test_every_page_is_in_the_sitemap_or_deliberately_not():
    dom = load("apply_domain")
    listed = {r for _, r in dom.SITEMAP_PAGES}
    every = {rel(p) for p in PAGES}
    missing = every - listed - UNLISTED
    assert missing == set(), f"pages in neither the sitemap nor the unlisted set: {missing}"
    assert listed <= every, "the sitemap names a page that does not exist"


def test_the_sitemap_file_matches_that_list():
    """The URLs only.

    apply_domain.py stamps lastmod from each file's last commit date, so a
    sitemap regenerated before its own commit is always one commit behind and
    `--check` can never be green on the day of a change. A date that drifts on
    its own would make this red every day and get the whole suite ignored.
    Which pages are published is the part that matters.
    """
    dom = load("apply_domain")
    sitemap = read(ROOT / "sitemap.xml")
    found = set(re.findall(r"<loc>https?://[^/]+(/[^<]*)</loc>", sitemap))
    assert found == {u for u, _ in dom.SITEMAP_PAGES}


def test_every_published_page_carries_absolute_og_tags():
    dom = load("apply_domain")
    og = {r for _, r in dom.OG_PAGES}
    published = {rel(p) for p in PAGES} - UNLISTED
    assert published - og == set(), "a published page with no absolute og tags"


# --- the nav, across pages --------------------------------------------------

NAV_BLOCK = re.compile(r"<!-- NAV-ANIM:START -->.*?<!-- NAV-ANIM:END -->", re.S)
NAV_ROW = re.compile(r'<div class="navrow">.*?\n  </div>', re.S)


def test_the_nav_script_is_identical_on_every_page():
    blocks = {}
    for p in PAGES:
        m = NAV_BLOCK.search(read(p))
        if m:
            blocks.setdefault(m.group(0), []).append(rel(p))
    assert len(blocks) == 1, f"more than one version of the nav script: {list(blocks.values())}"


def test_the_nav_markup_is_identical_apart_from_which_page_is_current():
    shapes = {}
    for p in PAGES:
        m = NAV_ROW.search(read(p))
        if m is None:
            continue
        # Strip the two things that legitimately differ per page.
        shape = re.sub(r'\s*aria-current="page"', "", m.group(0))
        shape = re.sub(r'href="[^"]*"', 'href=""', shape)
        shapes.setdefault(shape, []).append(rel(p))
    assert len(shapes) == 1, f"the nav differs between pages: {list(shapes.values())}"


# --- links and assets -------------------------------------------------------

HREF = re.compile(r'href="([^"]+)"')
SRC = re.compile(r'src="([^"]+)"')
CSS_URL = re.compile(r"url\(([^)]+)\)")


def resolves(target: str, page: Path) -> bool:
    """Does this internal target point at something that exists?"""
    target = target.split("#")[0].split("?")[0]
    if not target:
        return True
    base = ROOT if target.startswith("/") else page.parent
    candidate = (base / target.lstrip("/")).resolve()
    if candidate.is_dir():
        candidate = candidate / "index.html"
    elif str(candidate).endswith("/"):
        candidate = candidate / "index.html"
    return candidate.exists()


def internal(value: str) -> bool:
    return not value.startswith(("http://", "https://", "data:", "mailto:",
                                 "tel:", "#", "//"))


def test_every_internal_link_resolves(page_file):
    bad = [h for h in HREF.findall(read(page_file))
           if internal(h) and not resolves(h, page_file)]
    assert bad == [], f"{rel(page_file)} links to nothing: {bad}"


def test_every_local_asset_exists(page_file):
    """A book cover pointed at a file nobody had committed and 404'd in
    silence, twice."""
    text = read(page_file)
    refs = [v for v in SRC.findall(text) if internal(v)]
    refs += [v.strip("\"'") for v in CSS_URL.findall(text)
             if internal(v.strip("\"'"))]
    bad = [v for v in refs if not resolves(v, page_file)]
    assert bad == [], f"{rel(page_file)} references missing files: {bad}"


# --- each page on its own ---------------------------------------------------

class _Nesting(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.stack, self.bad = [], []

    def handle_starttag(self, tag, attrs):
        if tag not in VOID:
            self.stack.append((tag, self.getpos()))

    def handle_endtag(self, tag):
        if tag in VOID:
            return
        if not self.stack:
            self.bad.append(f"stray </{tag}> at {self.getpos()}")
            return
        if self.stack[-1][0] != tag:
            self.bad.append(
                f"</{tag}> at {self.getpos()} closes <{self.stack[-1][0]}>"
                f" opened at {self.stack[-1][1]}")
            for i in range(len(self.stack) - 1, -1, -1):
                if self.stack[i][0] == tag:
                    del self.stack[i:]
                    return
            return
        self.stack.pop()


def test_the_html_nests(page_file):
    """A stray regex once deleted a closing div from the nav."""
    p = _Nesting()
    p.feed(read(page_file))
    p.close()
    unclosed = [f"unclosed <{t}> at {pos}" for t, pos in p.stack]
    assert p.bad + unclosed == [], rel(page_file)


def test_the_page_has_a_head_worth_having(page_file):
    text = read(page_file)
    assert "<title>" in text, "no title"
    assert 'name="viewport"' in text, "no viewport meta"
    assert text.count("<h1") == 1, "a page should have exactly one h1"


def test_every_inline_script_parses(page_file):
    """node --check on each, since a syntax error in an inline script is
    invisible to every HTML tool and fatal in a browser."""
    scripts = re.findall(r"<script(?![^>]*\bsrc=)[^>]*>(.*?)</script>",
                         read(page_file), re.S)
    for i, body in enumerate(scripts):
        with tempfile.NamedTemporaryFile("w", suffix=".js", delete=False) as fh:
            fh.write(body)
            tmp = fh.name
        done = subprocess.run(["node", "--check", tmp],
                              capture_output=True, text=True)
        Path(tmp).unlink()
        assert done.returncode == 0, f"{rel(page_file)} script {i}: {done.stderr[:400]}"
