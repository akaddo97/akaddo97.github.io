#!/usr/bin/env python3
"""Point cv/index.html at a Google Form, by reading the form itself.

The CV page posts its four answers into a Google Form. That needs the form's
response endpoint and the numeric entry id of each question. Both are published
in the form's own page, so nobody should be copying them out of a minified blob
by hand.

    python3 cv_form_wire.py <form-share-url>            # show what it found
    python3 cv_form_wire.py <form-share-url> --write    # write it into cv/index.html

The form needs one question per field. Titles are matched loosely, so "Company
or organisation" and "Company/Organisation" both work. Anything it cannot match
is reported and left empty, and an empty field is simply not sent.

Stdlib only.
"""
import argparse, json, pathlib, re, sys, urllib.request

ROOT = pathlib.Path(__file__).resolve().parent
PAGE = ROOT / "cv/index.html"

# field -> the words that identify its question, in priority order
WANTED = {
    "name": ["name"],
    "email": ["email"],
    "company": ["company", "organisation", "organization", "employer"],
    "purpose": ["cv for", "what is this for", "purpose", "reason", "what for"],
    "linkedin": ["linkedin"],
}

# Google's own "collect email addresses" is not a question and has no entry id.
# It is posted under this fixed name instead.
EMAIL_FIELD = "emailAddress"


def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read().decode("utf-8", "replace")


def load_data(html):
    m = re.search(r"FB_PUBLIC_LOAD_DATA_\s*=\s*(\[.*?\]);\s*</script>", html, re.S)
    if not m:
        sys.exit("could not find the form data on that page; is the URL the public /viewform link?")
    return json.loads(m.group(1))


def questions(data):
    """[(title, entry_id)] in page order, for every answerable question."""
    out = []
    for item in (data[1][1] or []):
        title = (item[1] or "").strip()
        entries = item[4] if len(item) > 4 else None
        if not entries:
            continue
        for e in entries:
            if e and e[0]:
                out.append((title, f"entry.{e[0]}"))
    return out


def choices(data, entry_id):
    """The exact option strings for a given entry id, or [] if it is free text."""
    for item in (data[1][1] or []):
        for e in (item[4] or []) if len(item) > 4 and item[4] else []:
            if e and e[0] and f"entry.{e[0]}" == entry_id:
                return [o[0] for o in (e[1] or []) if o and o[0]]
    return []


def page_select_options():
    """The options actually offered by the select on the CV page."""
    html = PAGE.read_text()
    block = re.search(r'<select id="cvPurpose".*?</select>', html, re.S)
    if not block:
        return []
    opts = re.findall(r"<option(?: value=\"([^\"]*)\")?>(.*?)</option>", block.group(0))
    return [(v if v else txt).strip() for v, txt in opts if (v if v else txt).strip()]


def match(qs):
    found, used = {}, set()
    for field, words in WANTED.items():
        hit = None
        for word in words:
            for title, entry in qs:
                if entry in used:
                    continue
                if word in title.lower():
                    hit = (title, entry)
                    break
            if hit:
                break
        if hit:
            used.add(hit[1])
            found[field] = hit
    return found


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("url", help="the form's public /viewform share link")
    ap.add_argument("--write", action="store_true", help="write the result into cv/index.html")
    a = ap.parse_args()

    url = re.sub(r"\?usp=\S+$", "", a.url)
    if "/viewform" not in url:
        sys.exit("that does not look like a /viewform link")
    endpoint = url.replace("/viewform", "/formResponse")

    html = fetch(url)
    data = load_data(html)
    qs = questions(data)
    # Google's own email collection renders an email box with this placeholder
    # and no entry id, so it has to be detected from the page rather than the items.
    email_collected = "Your email" in html
    print(f"{len(qs)} question(s) on the form:")
    for title, entry in qs:
        print(f"  {entry:<22} {title!r}")

    found = match(qs)
    print("\nmapping:")
    fields = {}
    for field in WANTED:
        if field in found:
            title, entry = found[field]
            fields[field] = entry
            print(f"  {field:<9} -> {entry:<22} ({title!r})")
        elif field == "email" and email_collected:
            fields[field] = EMAIL_FIELD
            print(f"  {field:<9} -> {EMAIL_FIELD:<22} (Google's own email collection)")
        else:
            fields[field] = ""
            print(f"  {field:<9} -> NOT FOUND, will not be sent")

    # A radio value the form does not recognise is recorded as nothing at all,
    # silently. So the page's options must match the form's, exactly.
    problems = []
    if fields.get("purpose"):
        want = choices(data, fields["purpose"])
        have = page_select_options()
        have = [o for o in have if o != "Pick one"]
        if want and sorted(want) != sorted(have):
            problems.append("purpose options differ:\n    form: " + " | ".join(want)
                            + "\n    page: " + " | ".join(have))
    if problems:
        print("\nMISMATCH")
        for p_ in problems:
            print("  " + p_)
    else:
        print("\noptions match the page")

    block = (
        'var FORM = {\n'
        f'  ENDPOINT: "{endpoint}",\n'
        '  FIELDS: { '
        + ", ".join(f'{k}: "{v}"' for k, v in fields.items())
        + ' }\n};'
    )
    print("\n" + block)

    if not a.write:
        print("\n(nothing written; re-run with --write)")
        return 0

    text = PAGE.read_text()
    pat = re.compile(r"var FORM = \{.*?\};", re.S)
    if not pat.search(text):
        sys.exit(f"could not find the FORM block in {PAGE}")
    PAGE.write_text(pat.sub(lambda _: block, text, count=1))
    print(f"\nwrote {PAGE}")
    missing = [k for k, v in fields.items() if v == ""]
    if missing:
        print("still unmapped: " + ", ".join(missing))
    return 0


if __name__ == "__main__":
    sys.exit(main())
