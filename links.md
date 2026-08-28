# Site links: the one file

Every outbound link on the site that is likely to change lives here and nowhere
else. Edit a URL below, run `python3 apply_links.py --commit`, and every button
on every page follows. Nothing else needs touching.

Format: one `key: url` line per link. Anything that is not a `key: url` line is
ignored, so notes and headings are safe to write anywhere in this file.

    booking: https://calendar.app.google/9MuKtzaxZCC6NXULA
    cv: /cv/
    mentor: https://forms.gle/9TQKPCNVHnF6iqqbA
    cohort: https://docs.google.com/forms/d/e/1FAIpQLSetZTijhq0l2xNujow4Qc9kulguoO5PSRlpVX6grZopnp9rPg/viewform?usp=dialog
    cvfile: /AK_Addo_CV.pdf

## What each key is

- `booking` is the appointment scheduler. Twelve buttons: the footer on all
  seven pages, the hero and the closing block on the prices page, the closing
  block on the build and fluency pages, and the Start here block on the homepage.
- `cv` is where the CV button goes. Eight buttons: the nav on all seven pages,
  and the Start here block on the homepage. A path such as `/AK_Addo_CV.pdf`
  works here as well as a full URL, if the CV is served from this repo.
- `mentor` is the mentor signup form. One button, the fallback link on
  `/learn/mentor/`, under the form that posts into it.
- `cohort` is the cohort application. One button, the fallback link on
  `/learn/apply/`, under the form that posts into it.
- `cvfile` is the CV document itself, as opposed to `cv` which is the page that
  asks for it. One link, on `/cv/`, revealed after the form is answered. The
  page reads the address off that one anchor rather than keeping its own copy,
  so moving the CV to Drive or anywhere else is a one-line edit here.

## How to change a link

    cd ~/Projects/ak-site
    python3 apply_links.py                 # dry run, shows every button it would change
    python3 apply_links.py --commit        # writes the files
    python3 apply_links.py --check         # exits 1 if the site and this file disagree
    python3 apply_links.py --verify-urls   # also checks each URL returns 200

Then `git add -A && git commit && git push` as usual.

Anything still pointing at LinkedIn is a deliberate fallback, so no button on
the site ever dead-ends while a form is being built.
