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

## What each key is

- `booking` is the appointment scheduler. Ten buttons: the footer on all five
  pages, the hero and the closing block on the prices page, the closing block on
  the build and fluency pages, and the Start here block on the homepage.
- `cv` is where the CV button goes. Six buttons: the nav on all five pages, and
  the Start here block on the homepage. A path such as `/AK_Addo_CV.pdf` works
  here as well as a full URL, if the CV is served from this repo.
- `mentor` is the mentor signup form. One button, in the mentor section of the
  fluency page.
- `cohort` is the cohort application. One button, under the roster on the
  fluency page.

## How to change a link

    cd ~/Projects/ak-site
    python3 apply_links.py                 # dry run, shows every button it would change
    python3 apply_links.py --commit        # writes the files
    python3 apply_links.py --check         # exits 1 if the site and this file disagree
    python3 apply_links.py --verify-urls   # also checks each URL returns 200

Then `git add -A && git commit && git push` as usual.

Anything still pointing at LinkedIn is a deliberate fallback, so no button on
the site ever dead-ends while a form is being built.
