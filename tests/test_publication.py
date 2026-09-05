"""What must never be true of a public repository.

Every assertion here passes today. That is the point: these are properties the
site currently has, written down so that losing one is a failing build rather
than something noticed months later by someone who is not AK.

The rules come from DESIGN_NOTES.md and from AK's own to-do list, which are the
places they were previously written as prose and enforced by memory.
"""
from __future__ import annotations

import re
import subprocess

import pytest

from conftest import PAGES, ROOT, UNLISTED, rel


def tracked() -> list[str]:
    """Everything git would publish. GitHub Pages serves the branch, so a file
    being committed is the same thing as it being on the internet."""
    out = subprocess.run(["git", "ls-files"], cwd=ROOT,
                         capture_output=True, text=True, check=True).stdout
    return [line for line in out.splitlines() if line]


def page_text() -> dict[str, str]:
    return {rel(p): p.read_text(encoding="utf-8") for p in PAGES}


# --- the CV ------------------------------------------------------------------

def test_no_cv_document_is_committed():
    """AK's to-do: publish the public CV only, never inputs/AK_ADDO_CV.pdf,
    which carries his phone number, his email and his Army service. The CV goes
    out through a form and lives on Drive, reached by the cvfile link. The repo
    should hold no copy of either, and its history was purged once already."""
    suspects = [f for f in tracked()
                if f.lower().endswith((".pdf", ".doc", ".docx"))
                or re.search(r"(?i)\bcv\b.*\.(pdf|docx?|pages)$", f)]
    assert suspects == [], f"a document that should not be in a public repo: {suspects}"


# --- names ------------------------------------------------------------------

# DESIGN_NOTES.md: two clients are referred to publicly as "an insurance company
# in Ghana" and "a British defense-tech startup", and the teaching cohort is
# referred to by lane, never by name. These are real private people and
# companies, so the rule is enforced rather than remembered.
FORBIDDEN_NAMES = [
    "Aevlyn", "PriView", "Stratable", "Cockpit Theatre",
    "Akuchi", "Delina", "Rebecca", "Lynette", "Koko",
]


@pytest.mark.parametrize("name", FORBIDDEN_NAMES)
def test_no_client_or_cohort_name_appears_on_the_site(name):
    found = [path for path, text in page_text().items()
             if re.search(rf"\b{re.escape(name)}\b", text, re.I)]
    assert found == [], f"{name} appears on {found}"


# --- contact details and secrets --------------------------------------------

SECRETS = {
    "an API key or token": r"(?i)\b(api[_-]?key|secret[_-]?key|access[_-]?token)\b\s*[:=]",
    "an AWS key": r"\bAKIA[0-9A-Z]{16}\b",
    "a private key block": r"-----BEGIN [A-Z ]*PRIVATE KEY-----",
    "a bearer token": r"(?i)\bbearer\s+[A-Za-z0-9._-]{20,}",
}


@pytest.mark.parametrize("what,pattern", list(SECRETS.items()),
                         ids=list(SECRETS))
def test_no_secret_is_published(what, pattern):
    found = [path for path, text in page_text().items()
             if re.search(pattern, text)]
    assert found == [], f"{what} on {found}"


def test_no_personal_contact_details_are_published():
    """The site routes everything to a booking link and LinkedIn, which
    DESIGN_NOTES calls a deliberate choice to avoid publishing an address."""
    email = re.compile(r"[\w.+-]+@[\w-]+\.[\w.]+")
    phone = re.compile(r"(?:\+44|\b07)\d[\d ]{7,}")
    for path, text in page_text().items():
        # schema.org and og markup legitimately mention domains, not addresses.
        emails = [e for e in email.findall(text)
                  if not e.endswith((".png", ".jpg", ".svg"))]
        assert emails == [], f"an email address on {path}: {emails}"
        assert phone.findall(text) == [], f"a phone number on {path}"


# --- listed and unlisted ----------------------------------------------------

def test_unlisted_pages_really_are_unlisted():
    """Three form pages and the media page are kept out of the sitemap. Each
    must actually say noindex, so conftest's UNLISTED set cannot be used to
    quietly drop a page out of the sitemap while it stays crawlable."""
    sitemap = (ROOT / "sitemap.xml").read_text(encoding="utf-8")
    for path, text in page_text().items():
        if path not in UNLISTED:
            continue
        assert '<meta name="robots" content="noindex">' in text, f"{path} is not noindex"
        url = "/" if path == "index.html" else "/" + path[: -len("index.html")]
        assert f"<loc>https://akaddo97.github.io{url}</loc>" not in sitemap, \
            f"{path} is unlisted but in the sitemap"


def test_listed_pages_are_not_accidentally_hidden():
    """The opposite mistake: a noindex left on a page that is meant to be
    found. Both directions are one word apart."""
    for path, text in page_text().items():
        if path in UNLISTED:
            continue
        assert "noindex" not in text, f"{path} is in the sitemap but says noindex"


def test_robots_txt_points_at_the_sitemap():
    robots = (ROOT / "robots.txt").read_text(encoding="utf-8")
    assert "Sitemap: https://akaddo97.github.io/sitemap.xml" in robots


# --- the repo itself ---------------------------------------------------------

def test_the_dev_environment_is_not_published():
    """Playwright and pytest are test-only. Nothing under .venv should ever be
    committed: it is 90MB of someone else's code, and it made the first run of
    this very suite fail on Playwright's own bundled HTML."""
    leaked = [f for f in tracked()
              if f.startswith((".venv/", "__pycache__/", ".pytest_cache/"))]
    assert leaked == [], f"development files committed: {leaked[:5]}"
