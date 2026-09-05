"""Shared fixtures: the pages, a real server, and a real browser.

Two things here are load-bearing and were both learned by getting them wrong.

The pages are served over http rather than opened as file://. Absolute paths
such as /ak-addo.jpg resolve to the filesystem root under file:// and the image
silently fails, which reads as a broken page when the page is fine.

The browser is Playwright rather than `chrome --headless --screenshot`.
--window-size does not give headless Chrome a matching layout viewport: at 390
it lays the page out far wider and crops, so every page looks clipped on the
right whether or not it overflows. Playwright sets a real viewport, and it can
hand a computed style back, which a screenshot cannot.
"""
from __future__ import annotations

import http.server
import socket
import threading
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent

# Pages deliberately kept out of the sitemap, each carrying noindex. Three are
# gated behind a form and one is reached only by clicking Media on the
# homepage. test_publication.py asserts the noindex is really there, so this
# set cannot be used to quietly hide a page from the sitemap.
UNLISTED = {
    "cv/index.html",
    "learn/apply/index.html",
    "learn/mentor/index.html",
    "media/index.html",
}


def page_files() -> list[Path]:
    """Every page the site publishes.

    From git rather than a glob: what is committed is what GitHub Pages serves,
    and a glob also walks .venv, which contains Playwright's own bundled HTML
    and made the suite fail on someone else's markup.
    """
    import subprocess

    out = subprocess.run(["git", "ls-files", "*index.html"], cwd=ROOT,
                         capture_output=True, text=True, check=True).stdout
    return sorted(ROOT / line for line in out.split() if line)


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT))


def url_path(path: Path) -> str:
    """The URL a page is served at: about/index.html becomes /about/."""
    r = rel(path)
    return "/" if r == "index.html" else "/" + r[: -len("index.html")]


PAGES = page_files()
PAGE_IDS = [rel(p) for p in PAGES]


@pytest.fixture(params=PAGES, ids=PAGE_IDS)
def page_file(request) -> Path:
    return request.param


class _Quiet(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *args):  # noqa: A003
        pass


@pytest.fixture(scope="session")
def site_url() -> str:
    """The whole repo, served, for the length of the session."""
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        port = s.getsockname()[1]

    def handler(*args, **kwargs):
        return _Quiet(*args, directory=str(ROOT), **kwargs)

    server = http.server.ThreadingHTTPServer(("127.0.0.1", port), handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{port}"
    finally:
        server.shutdown()
        server.server_close()


@pytest.fixture(scope="session")
def browser():
    pw = pytest.importorskip("playwright.sync_api")
    with pw.sync_playwright() as p:
        b = p.chromium.launch()
        try:
            yield b
        finally:
            b.close()


@pytest.fixture
def view(browser, site_url):
    """open(page_path, width) -> a loaded Playwright page at that viewport."""
    made = []

    def open_at(path: Path | str, width: int = 1280, reduced_motion: str = "no-preference"):
        ctx = browser.new_context(viewport={"width": width, "height": 900},
                                  reduced_motion=reduced_motion)
        made.append(ctx)
        pg = ctx.new_page()
        target = path if isinstance(path, str) else url_path(path)
        pg.goto(site_url + target, wait_until="networkidle")
        return pg

    yield open_at
    for ctx in made:
        ctx.close()


def pytest_configure(config):
    config.addinivalue_line(
        "markers", "contract: talks to the live worker; not run on a push")
