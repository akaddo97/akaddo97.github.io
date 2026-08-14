# akaddo97.github.io

A one-page personal site for AK Addo, live at **https://akaddo97.github.io**.

Plain HTML with inline CSS. No framework, no build step, and no dependencies, which is deliberate: it means any page can be edited by anyone who can read HTML, and it deploys by pushing.

Four pages, each a self-contained `index.html`:

| Path | What it is |
|---|---|
| `/` | Bio, the two-colour split, the AK Bakes block, the evidence block, the outcome-named offerings, and the three actions. |
| `/build/` | Bespoke tech products. Example products named by outcome. |
| `/learn/` | AI fluency. Curriculum graph, anonymised cohort roster, mentoring, and the vibe-coding track. |
| `/pricing/` | Services and prices. The free first rung, the five-stage method, and the published ladder. |

## Editing it

Open the page, change the copy, and push to `main`. GitHub Pages rebuilds within about a minute. To preview locally first, run `python3 -m http.server 8080` from the repo root and open `http://localhost:8080`.

Every page also carries an edit-in-place toolbar, hidden from public visitors and shown when the URL has `?edit=1` on it. Edits save to that browser only and never reach the published page. Use "Save a copy" to download an edited version.

## The rail

The rail is the site's only navigation. There is no footer: it repeated the same links, so it was removed. Nine items in three groups, separated by rules:

1. **Pages.** Home, Bespoke tech products, AI fluency, Services and prices. The current page is marked with `aria-current="page"` and a yellow indicator. The CV page at `/cv/` carries the same rail and is marked current there, but is not one of the four listed pages.
2. **Actions.** Book 30 minutes (the accent-coloured primary), Download a CV.
3. **Elsewhere.** LinkedIn, GitHub, AK Bakes.

A 64px left strip from 769px up, where the full label appears as a tooltip on hover, and a bottom bar below that, where a short label sits under each icon. The short labels exist because nine items across 390px leaves 43px each, which the full names do not fit. Both are in the markup, as `.rail-label` and `.rail-short`; each link also carries the full name as its `aria-label`. On a short desktop window the strip scrolls internally rather than clipping.

Each action that depends on an external link is marked with an HTML comment on the line above it, alone on that line:

| Marker | Links | Points at |
|---|---|---|
| `<!-- FORM:BOOKING -->` | 10 | **Live.** A Google appointment schedule. |
| `<!-- FORM:CV -->` | 6 | **Live.** Points at `/cv/`, the gate page. |
| `<!-- FORM:MENTOR -->` | 1 | **Live.** The mentor signup form. |
| `<!-- FORM:COHORT -->` | 1 | **Live.** The AI fluency participant signup. |

Eighteen marked buttons in total, all live as of 2026-08-13. The LinkedIn fallback pattern remains available for any future marker: a pending action points at the LinkedIn profile so nothing on the site opens onto a dead end while its form is being built.

**Do not edit these by hand.** Every URL lives in `links.md`, and `apply_links.py` writes it to every button. `python3 apply_links.py` shows what would change, `--commit` writes, `--check` exits 1 if the site and `links.md` have drifted apart. The field specification for each form lives in `docs/scoping/google_forms_build_sheet_2026-08-11.html` in the `aks_claude_data` repo.

## The CV page

`/cv/` asks for a name, email, company, and purpose, posts them into a Google Form in the background, and downloads `AK_Addo_CV.pdf` from this repo. The form endpoint and its field ids are filled in by `cv_form_wire.py <form-url> --write`, which reads them out of the published form rather than anyone transcribing them.

Two things worth knowing. The post is `no-cors` and fire-and-forget, because Google sends no CORS headers on `formResponse`, so a failed write is invisible to the page; the download never waits on it. And the PDF path is in the page source, so this is a courtesy gate rather than a lock. While the endpoint is empty the page still downloads the CV and simply skips the capture, so the button is never dead.

## Link check

`.github/workflows/linkcheck.yml` runs every Monday and on demand from the Actions tab. It checks the IMAPS publication URL, which the publisher has moved before, plus the Square and GitHub links. It never fails the build: when something 404s three times in a row it opens a GitHub issue, and comments on that same issue each week the link stays broken.

The design tokens live in the `:root` block at the top of the stylesheet, so the palette can be changed in one place. The photo is `ak-addo.jpg`, an 800 by 800 square that the page renders as a circle. Any replacement should be square, or the circle will crop it unevenly.

## Custom domain

Add a `CNAME` file at the repo root containing the bare domain, then point a DNS `ALIAS` or `A` record at GitHub Pages. Nothing else in the repo needs to change.
