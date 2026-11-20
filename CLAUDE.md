# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

Single-page institutional site for **Rockers 502 MC Guatemala** (a Moto **Club** — "MC", not "MG"/Moto Grupo; that identity change was deliberate). Plain static HTML/CSS/JS: no framework, no package.json, no build step. Hosted on a private S3 bucket behind CloudFront, with `dev` and `prod` environments. All content, code comments, commit messages and docs are in Spanish (Guatemalan/voseo register: "editá", "abrí") — keep it that way.

## Commands

```bash
# Local preview (always use a server, not file://)
cd site && python3 -m http.server 8080

# The only automated check (same one CI runs): fails if any local src/href in
# site/index.html or site/404.html points to a missing file
python3 .github/scripts/verificar_enlaces.py

# Regenerate emblem, favicons and og.jpg from Assets/logo.jpeg (needs Pillow, numpy, scipy)
python3 make_emblem.py

# Manual deploy fallback (normally done by GitHub Actions)
ROCKERS_BUCKET=... ROCKERS_DISTRIBUTION_ID=... ./deploy.sh
```

There are no tests or linters. Manually check: the menu on desktop and mobile, the carousel (arrows + drag), and the footer.

## Architecture

- **`site/` is the only thing published** to the bucket. `site/index.html` is hand-edited source, not generated — what you see is what ships.
- **`site/assets/js/main.js`** is a dependency-free IIFE (ES5 style, `var`). The site must be fully usable without it: JS only removes the `no-js` class and adds the mobile menu, header shadow, entrance animations and carousel arrows (carousel still works by drag/scroll). Hooks are `data-*` attributes (`data-burger`, `data-menu`, `data-header`, …), not classes.
- **`site/assets/css/styles.css`** is organized tokens → base → components → sections → responsive. Colors/fonts are CSS custom properties in `:root` with Spanish names (`--negro`, `--rojo`, `--hueso`, …). Accessibility constraint: red `#C1121F` is never used for paragraph text (contrast), only headings, borders, icons, button backgrounds. `prefers-reduced-motion` must disable all animation.
- **Derived images:** `emblem.webp`, `emblem@2x.webp`, `favicon-512.png`, `apple-touch-icon.png`, `site/favicon.ico` and `og.jpg` all come from `Assets/logo.jpeg` via `make_emblem.py` — don't edit them by hand. The script uses a flood fill from the edges (not a circular mask) because the ROCKERS/GUATEMALA banners stick out past the ring; outputs are square so HTML `width`/`height` stay valid.
- Content photos (`site/assets/img/rodadas/`, `maquinas/`) are WebP, quality 75–80; carousel images 3:2, <150 KB. `moto-1.webp` is the large mosaic tile, the other four are square. Captions/alt text live in `index.html`.

## Deployment

Single workflow `.github/workflows/deploy.yml`: `verificar → dev → prod`. Push to `main` touching `site/**` or `.github/**` deploys dev automatically, then prod waits for reviewer approval on the `prod` GitHub Environment. `workflow_dispatch` with `dev` stops after dev.

- No environment-specific values in code: `AWS_REGION`, `SITE_URL` (Environment variables) and `AWS_ROLE_ARN`, `AWS_S3_BUCKET`, `AWS_CLOUDFRONT_DISTRIBUTION_ID` (Environment secrets) come from each GitHub Environment.
- The dev job overwrites `robots.txt` with `Disallow: /` and deletes `sitemap.xml` before uploading — the committed files are the prod versions.
- Cache policy: `assets/**` uploaded with 1-year `immutable`; HTML with `max-age=0, must-revalidate`; robots/sitemap 1 hour. Every deploy invalidates `/*`. If asset contents change, the invalidation is what refreshes them (filenames are not hashed).
- `deploy.sh` mirrors the prod job's sync/invalidate steps; keep them in sync when changing either.
- AWS auth is OIDC (no keys). `infra/crear-rol.sh <entorno> <bucket> <distribution-id>` creates/updates one IAM role per environment; the trust policy pins `sub` to `repo:fjbatresv/rocker-mc:environment:<entorno>` so dev can't assume the prod role. Details in `infra/README.md`.

## Domain-dependent values

The site assumes `rockers502.gt`. Changing the domain means updating `canonical`, Open Graph tags, JSON-LD in `index.html`, `sitemap.xml` and `robots.txt`.
