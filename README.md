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

## The action rail, and the form links

Every page carries the same fixed rail: home, book a call, prices, CV, bakery. It is a left strip on desktop and a bottom bar below 769px.

Each action that depends on an external link is marked with an HTML comment on the line above it, alone on that line:

| Marker | Links | Points at |
|---|---|---|
| `<!-- FORM:BOOKING -->` | 9 | **Live.** A Google Calendar booking page. |
| `<!-- FORM:CV -->` | 5 | Pending. Falls back to LinkedIn. |
| `<!-- FORM:MENTOR -->` | 1 | Pending. Falls back to LinkedIn. |
| `<!-- FORM:COHORT -->` | 2 | Pending. Falls back to LinkedIn. |

A pending action falls back to the LinkedIn profile, so nothing on the site opens onto a dead end while its form is being built.

The footer is the same on every page: the other three pages of the site, in a fixed order, then LinkedIn, GitHub, and AK Bakes. The only entry ever omitted is the page you are already on. The field specification for each form, and the tested one-command swap that wires one in, live in `docs/scoping/website_forms_spec_2026-08-10.html` in the `aks_claude_data` repo.

## Link check

`.github/workflows/linkcheck.yml` runs every Monday and on demand from the Actions tab. It checks the IMAPS publication URL, which the publisher has moved before, plus the Square and GitHub links. It never fails the build: when something 404s three times in a row it opens a GitHub issue, and comments on that same issue each week the link stays broken.

The design tokens live in the `:root` block at the top of the stylesheet, so the palette can be changed in one place. The photo is `ak-addo.jpg`, an 800 by 800 square that the page renders as a circle. Any replacement should be square, or the circle will crop it unevenly.

## Custom domain

Add a `CNAME` file at the repo root containing the bare domain, then point a DNS `ALIAS` or `A` record at GitHub Pages. Nothing else in the repo needs to change.
