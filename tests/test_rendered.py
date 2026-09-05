"""What the pages do once a browser has run them.

This is the layer that would have caught the three bugs that actually reached
the live site. All three passed the HTML parse, the house style check and every
`--check` script, because none of those can see what CSS computes to:

  - .np-row set display:flex, which beats the browser's own rule for [hidden],
    so a row the script had hidden still rendered its Music or Podcast label
    with nothing under it, on every load where the worker was unreachable.
  - .rot-slide had the same shape, found only because the first one had just
    been fixed.
  - The About page shipped with no .hero or .shot rules at all, so the
    photograph rendered full width and square instead of small and circular.

The assertions are on computed values rather than screenshots, so an edit to
the copy never turns them red.
"""
from __future__ import annotations

import pytest

from conftest import PAGES, UNLISTED, rel, url_path

WIDTHS = [1280, 390]
HERO_PAGES = ["/", "/about/"]


@pytest.mark.parametrize("width", WIDTHS)
def test_nothing_hidden_is_visible(view, page_file, width):
    """The generic form of the .np-row bug: an element carrying the hidden
    attribute must compute to display:none, whatever CSS says about its class.
    A sweep rather than a list, so it covers whatever is added next."""
    pg = view(page_file, width)
    offenders = pg.evaluate("""() =>
      Array.from(document.querySelectorAll('[hidden]'))
        .filter(el => getComputedStyle(el).display !== 'none')
        .map(el => el.tagName.toLowerCase() + '.' + (el.className || '(no class)'))
    """)
    assert offenders == [], f"{rel(page_file)} at {width}px: {offenders}"


@pytest.mark.parametrize("width", WIDTHS)
def test_the_page_does_not_scroll_sideways(view, page_file, width):
    """A snap track inside a bordered shell is the classic way to give a page a
    horizontal scrollbar."""
    pg = view(page_file, width)
    over = pg.evaluate(
        "() => document.documentElement.scrollWidth - window.innerWidth")
    assert over <= 0, f"{rel(page_file)} at {width}px overflows by {over}px"


@pytest.mark.parametrize("width", WIDTHS)
def test_every_image_loads(view, page_file, width):
    """naturalWidth is 0 for an image that 404'd, which is the only way to tell
    from the outside. Book covers did this twice."""
    pg = view(page_file, width)
    broken = pg.evaluate("""() =>
      Array.from(document.images)
        /* The Music and Podcast rows ship with no src and hidden, and are
           filled by script only when the worker answers. An empty slot that
           nobody can see is not a broken image. */
        .filter(i => i.getAttribute('src'))
        .filter(i => i.offsetParent !== null || getComputedStyle(i).display !== 'none')
        .filter(i => i.complete && i.naturalWidth === 0)
        .map(i => i.getAttribute('src'))
    """)
    assert broken == [], f"{rel(page_file)} at {width}px: {broken}"


def test_the_nav_is_not_left_invisible(view, page_file):
    """The entrance animates from opacity 0. A Web Animation hands the element
    back to the stylesheet when it finishes, but a mistake here strands the
    whole nav invisible and the page looks empty."""
    if "navrow" not in page_file.read_text(encoding="utf-8"):
        pytest.skip("no nav on this page")
    pg = view(page_file, 1280)
    pg.wait_for_timeout(1400)
    faded = pg.evaluate("""() =>
      Array.from(document.querySelectorAll('.navrow a'))
        .filter(a => parseFloat(getComputedStyle(a).opacity) < 0.9)
        .map(a => a.textContent.trim())
    """)
    assert faded == [], f"{rel(page_file)}: nav items left faded: {faded}"


@pytest.mark.parametrize("path", HERO_PAGES)
def test_the_hero_stacks_on_a_phone_and_not_on_a_desktop(view, path):
    """The About page shipped without the rules that do this. Stated as
    behaviour, so it holds however the CSS gets there."""
    wide = view(path, 1280)
    assert len(wide.evaluate(
        "() => getComputedStyle(document.querySelector('.hero')).gridTemplateColumns.split(' ')"
    )) == 2, f"{path} hero is not two columns at 1280px"

    narrow = view(path, 390)
    assert len(narrow.evaluate(
        "() => getComputedStyle(document.querySelector('.hero')).gridTemplateColumns.split(' ')"
    )) == 1, f"{path} hero does not stack at 390px"


def test_the_headshot_is_a_circle(view):
    """Small, round and on the right is what AK asked for twice."""
    for path in HERO_PAGES:
        pg = view(path, 1280)
        box = pg.evaluate("""() => {
          const el = document.querySelector('.hero .shot');
          if (el === null) { return null; }
          const r = el.getBoundingClientRect();
          const cs = getComputedStyle(el);
          return {w: Math.round(r.width), h: Math.round(r.height), radius: cs.borderRadius};
        }""")
        assert box is not None, f"{path} has no headshot"
        assert box["w"] == box["h"], f"{path} headshot is not square: {box}"
        assert "%" in box["radius"], f"{path} headshot is not round: {box}"


# --- the band ---------------------------------------------------------------

def test_every_slide_is_reachable_and_is_a_link(view):
    pg = view("/", 1280)
    slides = pg.evaluate("""() =>
      Array.from(document.querySelectorAll('.rot-slide'))
        .filter(el => el.hidden !== true)
        .map(el => ({href: el.getAttribute('href'), text: el.innerText.trim()}))
    """)
    assert len(slides) >= 3
    assert all(s["href"] and s["text"] for s in slides), slides
    dots = pg.evaluate("() => document.querySelectorAll('.rot-dots button').length")
    assert dots == len(slides), "a dot per slide, or one of them cannot be reached"


def test_the_band_does_not_move_under_reduced_motion(view):
    """Not slower. Not at all. And nothing may become unreachable because of
    it, which is the rule that actually matters."""
    pg = view("/", 1280, reduced_motion="reduce")
    before = pg.evaluate("() => document.getElementById('rotTrack').scrollLeft")
    pg.wait_for_timeout(9000)
    after = pg.evaluate("() => document.getElementById('rotTrack').scrollLeft")
    assert before == after, "the band advanced for a reader who asked it not to"
    dots = pg.evaluate("() => document.querySelectorAll('.rot-dots button').length")
    assert dots >= 3, "the dots are the way through when nothing moves on its own"


def test_a_plain_click_on_a_nav_link_still_navigates(view, site_url):
    """The exit animation holds the page change for 320ms. If it ever fails to
    fire the callback, every link on the site stops working."""
    pg = view("/", 1280)
    # Absolute on the homepage, relative on pages one level down.
    pg.click('.navrow a[href$="/about/"], .navrow a[href="about/"]')
    pg.wait_for_url(f"{site_url}/about/", timeout=5000)
    assert pg.url.endswith("/about/")


# --- the pages that are meant to be quiet ------------------------------------

def test_an_unlisted_page_still_renders(view):
    """Unlisted means unlinked, not broken."""
    for path in sorted(UNLISTED):
        url = "/" + path[: -len("index.html")]
        pg = view(url, 1280)
        assert pg.evaluate("() => document.body.innerText.trim().length") > 40, url
