"""The worker the site reads from, and whether it still answers the way the
pages expect.

Two pages fetch a Cloudflare worker at runtime: the homepage Media block and
/media/. Its payload changed twice in a week, gaining `lastAt` and starting to
carry podcast artwork, and neither change would have been noticed here.

Marked `contract` and excluded from the push workflow on purpose. A worker
outage must not stop AK publishing a copy change, so this runs on a schedule
and opens an issue, the way the link check already does.
"""
from __future__ import annotations

import json
import urllib.error
import urllib.request

import pytest

pytestmark = pytest.mark.contract

ENDPOINT = "https://ak-now-playing.akaddo97.workers.dev"
ORIGIN = "https://akaddo97.github.io"


def get(path: str, origin: str = ORIGIN):
    req = urllib.request.Request(ENDPOINT + path,
                                 headers={"Origin": origin,
                                          "User-Agent": "ak-site-tests"})
    with urllib.request.urlopen(req, timeout=25) as r:
        return r, json.loads(r.read().decode("utf-8"))


@pytest.fixture(scope="module")
def now():
    return get("/now")


@pytest.fixture(scope="module")
def history():
    return get("/history?limit=20")


def test_the_site_origin_is_still_allowed(now):
    """The allowlist is what makes every localhost mockup show an empty Media
    section. If the live origin ever falls off it, the section empties for
    real visitors instead."""
    resp, _ = now
    assert resp.headers.get("access-control-allow-origin") == ORIGIN


def test_an_unknown_origin_is_still_refused():
    resp, _ = get("/now", origin="https://example.invalid")
    assert resp.headers.get("access-control-allow-origin") != "https://example.invalid"


def test_now_carries_the_fields_the_homepage_reads(now):
    """index.html reads title, subtitle, art, url, live and at. A field going
    missing shows as a blank row rather than an error."""
    _, data = now
    assert isinstance(data, dict)
    for slot in ("music", "podcast"):
        assert slot in data, f"/now no longer has a {slot} slot"
        item = data[slot]
        if item is None:
            continue
        for field in ("title", "subtitle", "art", "url", "live", "at"):
            assert field in item, f"/now {slot} lost {field}"
        assert isinstance(item["live"], bool)


def test_history_carries_the_fields_the_media_page_reads(history):
    """/media/ reads kind, title, subtitle, art, url, last and lastAt."""
    _, data = history
    items = data.get("items")
    assert isinstance(items, list) and items, "/history returned nothing"
    for item in items:
        for field in ("kind", "title", "subtitle", "art", "url", "last", "lastAt"):
            assert field in item, f"/history lost {field}"
        assert item["kind"] in ("music", "podcast")


def test_a_timestamp_is_a_timestamp_and_not_just_a_day(history):
    """The media page prints an hour and a minute. `last` is a date and
    `lastAt` is the instant; the page falls back to the date if the instant is
    missing, so losing it degrades silently."""
    _, data = history
    stamped = [i for i in data["items"] if i.get("lastAt")]
    assert stamped, "no row carries lastAt"
    assert "T" in stamped[0]["lastAt"]


def test_podcast_rows_carry_artwork(history):
    """detail() used to return out of its episode branch before album_art was
    set, so every podcast row was written with none and the page showed grey
    squares."""
    _, data = history
    pods = [i for i in data["items"] if i["kind"] == "podcast"]
    if not pods:
        pytest.skip("no podcasts in this window")
    without = [i["title"] for i in pods if not i["art"]]
    assert without == [], f"podcast rows with no artwork: {without[:3]}"
