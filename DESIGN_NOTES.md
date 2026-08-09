# Design notes

For Jasmine Boatswain. This is a jumping-off point, not a finished design. Everything here is a decision that can be reversed, and the reasoning is written down so you can see what was deliberate and what was just the fastest thing that worked.

## What the site is for

Two audiences arrive here, and they want different things.

Someone AK has just met opens the link to find out who he is. They read the bio and leave. Someone reviewing a grant or residency application opens it having just read his essays, gives it somewhere between thirty and ninety seconds, and is asking one question: is this real. They answer it by reaching running code, which is why the "Work you can check" block exists and why it links four public repos and a paper rather than describing them.

The page is a signpost, not a showcase. The strongest asset AK has is the `sponge` repo, and the site's job is to be the shortest path to it.

## Structure

Single centred column, 620px max. Photo, name, role, bio, then three blocks in this order:

1. **What I do**, a two-colour split. Bespoke tech products on near-black, AI fluency on the panel cream. These are the two commercial offerings and they are deliberately equal in weight.
2. **Work you can check**, the evidence layer. Prose, then repos, then the publication.
3. **Baking**, a cocoa block, sitting alone after everything else.

There is an empty slot marked in an HTML comment between blocks 2 and 3. One short piece of AK's own writing goes there. He writes it, nobody drafts it for him.

## Why baking is where it is

AK's instruction was that baking should be present but less prominent than the other two. Four treatments were built and compared before landing here: equal cards with baking muted, three cards with one lighter, editorial rows with baking last, and this one. They are all still in `options/` if you want to see the range.

This version demotes baking by **separating it rather than shrinking it**. It is not a third item in the offerings grid, it is its own thing further down the page, in its own palette. That way it reads as a different world rather than as a weaker service, which matters because AK considers the baking a differentiator rather than a hobby to apologise for.

The cocoa block is the only place on the page using that palette, which is what makes it pop against the cream without needing to be large.

## Palette

Shared anchors across AK's properties, from the AK Bakes rebrand scope:

| Token | Hex | Use |
|---|---|---|
| `--bg` | `#FAF8F2` | Page cream |
| `--ink` | `#1A1A1A` | Text, and the dark half of the split |
| `--accent` | `#F5C518` | Yellow, link underlines and accent bars |
| `--panel` | `#F0EDE3` | The cream half of the split |
| `--rule` | `#E4DFD2` | Hairlines |
| `--cocoa` | `#4A2E1C` | Baking block |
| `--amber` | `#D99A2B` | Baking accent |

Cocoa and amber are the AK Bakes side of the same system rather than an invented brown. The warm brown was left unspecified in the rebrand scope, so `#4A2E1C` is a choice, not a given, and it is yours to change. Cream on cocoa measures 11.6:1, so there is a lot of headroom if you want to lighten it.

## Constraints worth knowing before you change things

**No prices anywhere.** There is a five-package services menu with published anchors elsewhere in AK's material. It is deliberately not on this site. A reviewer who lands on a price list reads him as a consultant selling packages, and the pricing itself is still unsettled.

**No client names, ever.** Two clients are referred to publicly as "an insurance company in Ghana" and "a British defense-tech startup". Do not sharpen those and do not add a logo wall.

**No names from the teaching cohort.** Lanes only. Those are real private individuals.

**Register:** no em-dashes, no exclamation marks, Oxford comma, British spelling. AK's copy is his own; treat the words as fixed unless he changes them.

## Technical

Plain HTML with inline CSS. No framework, no build step, no dependencies, no JavaScript on the homepage. It deploys by pushing to `main`, and GitHub Pages serves it within about a minute.

Preview locally with `python3 -m http.server 8080` from the repo root.

`options/` carries the four alternatives and is marked `noindex`. Those pages each ship a small Edit toolbar so AK can rewrite copy in the browser and download a copy. The live homepage deliberately has no toolbar, because it would show an Edit button to every visitor.

Responsive behaviour is one breakpoint at 520px, where the split stacks. Checked for horizontal overflow at 320, 390, 520, 768, and 1280px.

## Known rough edges

The photo is a single 800px square. There is no smaller variant for mobile and no `srcset`.

The favicon is an inline SVG of the letters AK, functional rather than designed.

There is no contact form. Everything routes to LinkedIn, which was a deliberate choice to avoid publishing an email address, but it is the weakest part of the page.

The site has no shared stylesheet. Each page carries its own inline CSS, which was right for building four variants quickly and is wrong for a site that is going to grow. Extracting the tokens into one stylesheet is the obvious first refactor.
