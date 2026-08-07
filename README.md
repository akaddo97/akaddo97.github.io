# akaddo97.github.io

A one-page personal site for AK Addo, live at **https://akaddo97.github.io**.

Plain HTML with inline CSS. No framework, no build step, no dependencies, and no JavaScript. The whole site is `index.html` plus one image, which is deliberate: it means the page can be edited by anyone who can read HTML, and it deploys by pushing.

## Editing it

Open `index.html`, change the copy, and push to `main`. GitHub Pages rebuilds within about a minute. To preview locally first, run `python3 -m http.server 8080` from the repo root and open `http://localhost:8080`.

The design tokens live in the `:root` block at the top of the stylesheet, so the palette can be changed in one place. The photo is `ak-addo.jpg`, an 800 by 800 square that the page renders as a circle. Any replacement should be square, or the circle will crop it unevenly.

## Custom domain

Add a `CNAME` file at the repo root containing the bare domain, then point a DNS `ALIAS` or `A` record at GitHub Pages. Nothing else in the repo needs to change.
