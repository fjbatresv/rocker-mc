# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

Single-page institutional site for **Rockers 502 MC Guatemala** (a Moto **Club** — "MC", not "MG"/Moto Grupo; that identity change was deliberate). Plain static HTML/CSS/JS: no framework, no package.json, no build step. Hosted on a private S3 bucket behind CloudFront, with `dev` and `prod` environments. All content, code comments, commit messages and docs are in Spanish (Guatemalan/voseo register: "editá", "abrí") — keep it that way.

## Commands

```bash
# Local preview (always use a server, not file://)
cd site && python3 -m http.server 8080

# Tests and destination-aware checks (default target is site)
python3 -m unittest discover -s .github/scripts -p 'test_*.py' -v
python3 .github/scripts/verificar_enlaces.py --destino todos
python3 .github/scripts/verificar_seguridad.py --destino todos

# Regenerate emblem, favicons and og.jpg from Assets/logo.jpeg (needs Pillow, numpy, scipy)
python3 make_emblem.py

# Manual deploy fallback (normally done by GitHub Actions)
ROCKERS_BUCKET=... ROCKERS_DISTRIBUTION_ID=... ./deploy.sh
```

Run the standard-library unit tests and both destination-aware verifiers before publishing. Manually check the club site's menu, carousel, and footer; the landing must also work at narrow widths and with reduced motion.

## Architecture

- **`site/` is published to the AWS bucket; `landing/` is published separately to GitHub Pages.** Both are hand-edited static HTML, not generated.
- **`landing/`** is the portfolio case study at `rockers.fjbatresv.com`. It has Spanish at `/` and English at `/en/`, no JavaScript or build step, and a CSP in a `<meta>` because GitHub Pages does not support custom response headers. `frame-ancestors` cannot be enforced from a CSP meta tag. Keep local links in `landing/404.html` absolute so nested missing paths load its CSS. Javier is a club member and built the club site voluntarily with the club's approval; never describe the relationship as client work or a paid commission. The Python verifiers accept `--destino site|landing|todos` (default `site`); CI checks both destinations.
- **`site/assets/js/main.js`** is a dependency-free IIFE (ES5 style, `var`). The site must be fully usable without it: JS only removes the `no-js` class and adds the mobile menu, header shadow, entrance animations and carousel arrows (carousel still works by drag/scroll). Hooks are `data-*` attributes (`data-burger`, `data-menu`, `data-header`, …), not classes.
- **`site/assets/css/styles.css`** is organized tokens → base → components → sections → responsive. Colors/fonts are CSS custom properties in `:root` with Spanish names (`--negro`, `--rojo`, `--hueso`, …). Accessibility constraint: red `#C1121F` is never used for paragraph text (contrast), only headings, borders, icons, button backgrounds. `prefers-reduced-motion` must disable all animation.
- **Derived images:** `emblem.webp`, `emblem@2x.webp`, `favicon-512.png`, `apple-touch-icon.png`, `site/favicon.ico` and `og.jpg` all come from `Assets/logo.jpeg` via `make_emblem.py` — don't edit them by hand. The script uses a flood fill from the edges (not a circular mask) because the ROCKERS/GUATEMALA banners stick out past the ring; outputs are square so HTML `width`/`height` stay valid.
- Content photos (`site/assets/img/rodadas/`, `maquinas/`) are WebP, quality 75–80; carousel images 3:2, <150 KB. `moto-1.webp` is the large mosaic tile, the other four are square. Captions/alt text live in `index.html`.

## Deployment

Two workflows publish independently: `.github/workflows/deploy.yml` sends `site/` to AWS after verification, and `.github/workflows/landing.yml` sends `landing/` to GitHub Pages after its checks. The AWS workflow uses `verificar → desplegar` in the GitHub Environment `dev`. That name stays because the IAM role trust policy pins `sub` to `repo:fjbatresv/rocker-mc:environment:dev`; the deployed site is public and indexable. Pushes to `main` touching the site, workflow or scripts deploy; pull requests only run verification. `workflow_dispatch` deploys only when launched from `main`.

- No environment-specific values in code: `AWS_REGION`, `SITE_URL` (Environment variables) and `AWS_ROLE_ARN`, `AWS_S3_BUCKET`, `AWS_CLOUDFRONT_DISTRIBUTION_ID` (Environment secrets) come from each GitHub Environment.
- Cache policy: `assets/**` uploaded with 1-year `immutable`; HTML with `max-age=0, must-revalidate`; robots/sitemap 1 hour. Every deploy invalidates `/*`. If asset contents change, the invalidation is what refreshes them (filenames are not hashed).
- `deploy.sh` mirrors the prod job's sync/invalidate steps; keep them in sync when changing either.
- AWS auth is OIDC (no keys). `infra/crear-rol.sh <entorno> <bucket> <distribution-id>` creates/updates one IAM role per environment; the trust policy pins `sub` to `repo:fjbatresv/rocker-mc:environment:<entorno>` so dev can't assume the prod role. Details in `infra/README.md`.

## Domain-dependent values

The official AWS site is `rockers502mc.com.gt`; `SITE_URL` in the `dev` Environment must be `https://rockers502mc.com.gt`. `rockers.fjbatresv.com` serves the portfolio landing from GitHub Pages. `site/` remains on `rockers502mc.com.gt`. If the AWS domain changes, update `SITIO` in `.github/scripts/verificar_seguridad.py` and run the verifier; it lists every file that needs updating.
