# Landing de portafolio — plan de implementación

> **Para agentes (Codex u otro):** ejecutá el plan tarea por tarea, en orden, marcando los `- [ ]`. Si tenés las skills de superpowers, usá `superpowers:executing-plans`. Cada tarea termina en un commit propio en la rama `landing-portafolio` (sin push). Leé `CLAUDE.md` y el spec antes de empezar.

**Goal:** Publicar en `https://rockers.fjbatresv.com/` (ES) y `/en/` (EN) una landing estática que cuenta el sitio de Rockers 502 MC como caso de estudio de ingeniería y cierra con dos salidas de contacto.

**Architecture:** Carpeta `landing/` sin build ni dependencias, con su propio CSS (tokens copiados del club). Los verificadores Python existentes pasan a trabajar por *destino* (`site` o `landing`), y el job requerido "Verificar el sitio" revisa ambos. Un workflow nuevo, `landing.yml`, publica `landing/` en GitHub Pages.

**Tech Stack:** HTML, CSS, SVG en línea, Python 3 (solo stdlib, `unittest`), GitHub Actions, GitHub Pages. Pillow solo en local para generar imágenes una vez (ya se usa en `make_emblem.py`), nunca en CI.

**Spec:** `docs/superpowers/specs/2026-11-21-landing-portafolio-design.md`. Ganan el spec y este plan, en ese orden, si algo choca.

## Global Constraints

- Sin `package.json`, sin build, sin librerías Python fuera de stdlib en CI.
- HTML de `landing/`: sin `style="…"`, sin handlers `on*=`, sin `<script>` salvo `type="application/ld+json"`. Sin JS.
- CSP de la landing, en `<meta http-equiv="Content-Security-Policy">` de cada página, exactamente: `default-src 'none'; script-src 'self'; style-src 'self' https://fonts.googleapis.com; font-src https://fonts.gstatic.com; img-src 'self' data:; base-uri 'none'; form-action 'none'; upgrade-insecure-requests`
- Colores: `--negro:#0A0A0B`, `--negro-elev:#141416`, `--rojo:#C1121F`, `--rojo-txt:#EA4650`, y el resto que necesités copiado de `site/assets/css/styles.css`. `#C1121F` nunca para texto de párrafo. Fuentes: Oswald, Barlow, Barlow Condensed (Google Fonts, mismos pesos que `site/`).
- `@media (prefers-reduced-motion: reduce)` apaga toda animación y transición.
- Contacto: `mailto:fjbatresv@gmail.com?subject=Oportunidad%20laboral` (equipo) y `mailto:fjbatresv@gmail.com?subject=Proyecto%20web` (proyecto); en `/en/`: `Job%20opportunity` y `Web%20project`. Más `https://fjbatresv.com`. Nada de LinkedIn ni formulario.
- Relación con el club: Javier es **miembro** y lo hizo **de forma voluntaria, con aprobación del club**. Nunca "cliente" ni "encargo".
- Titular: "Un sitio chico. Ingeniería grande." / "A small site. Serious engineering." Botones del hero: "Trabajemos juntos" / "Let's work together" (ancla `#contacto`) y "Ver código" / "View the code" (repo). Cierre: "¿Te sumás a la rodada?" / "Ride with us?".
- Todo número publicado se mide con el comando que da la Tarea 3; nada de "enterprise-grade" ni métricas no medidas.
- Actions fijadas por SHA, exactamente:
  - `actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1 # v7.0.1`
  - `actions/configure-pages@45bfe0192ca1faeb007ade9deae92b16b8254a0d # v6.0.0`
  - `actions/upload-pages-artifact@fc324d3547104276b827a68afc52ff2a11cc49c9 # v5.0.0`
  - `actions/deploy-pages@368f82528645a54fb793d4d04e342629a3f51346 # v5.0.1`
- Textos de commits, comentarios y la página ES en español con voseo; la página EN en inglés.
- URLs de evidencia: repo `https://github.com/fjbatresv/rocker-mc`; archivos como `https://github.com/fjbatresv/rocker-mc/blob/main/<ruta>`; PR #2 `https://github.com/fjbatresv/rocker-mc/pull/2`; PR #3 `…/pull/3`; favicon `…/commit/6fd1ff1`; sitio del club `https://rockers502mc.com.gt/`.

## Review Focus

1. **Una 404 en ruta anidada** (`/en/no/existe`): GitHub Pages sirve `404.html` en esa URL; con rutas relativas el CSS se rompe. → Tarea 2: `test_404_usa_rutas_absolutas` y la verificación en navegador.
2. **Celular de 360 px**: sin scroll horizontal y diagrama legible. → Tarea 3, paso de navegador con `scrollWidth`.
3. **Fuentes o imágenes bloqueadas por la CSP del `<meta>`**: consola sin violaciones en `/`, `/en/` y la 404. → Tareas 2 y 4, paso de navegador.
4. **`hreflang` no recíproco o canonical cruzado** (que `/en/` declare canonical `/`): Google ignora ambos. → Tarea 4: `test_hreflang_reciproco` y `test_canonical_por_pagina`.
5. **El verificador de `site/` se relaja sin querer** al parametrizarlo. → Tarea 1: los 9 tests actuales siguen pasando sin cambiar sus aserciones.

---

### Tarea 1: Verificadores por destino

**Files:**
- Modify: `.github/scripts/verificar_seguridad.py`, `.github/scripts/verificar_enlaces.py`
- Modify: `.github/scripts/test_verificar_seguridad.py`
- Create: `.github/scripts/test_verificar_enlaces.py`
- Modify: `.github/workflows/deploy.yml` (step "Las URLs del sitio coinciden con SITE_URL": agregar `--destino site`)

**Interfaces:**
- Produces, en `verificar_seguridad.py`:
  - `@dataclass(frozen=True) class Destino: raiz: str; sitio: str; canonicas: tuple[tuple[str, str], ...]; paginas: tuple[str, ...]; prohibidos: tuple[str, ...]; csp_meta: str | None`
    - `canonicas`: pares (página relativa a `raiz`, ruta pública), p. ej. `(('index.html', '/'),)`.
    - `paginas`: todas las páginas HTML relativas a `raiz` que se revisan (incluida la 404).
  - `DESTINOS: dict[str, Destino]` con:
    - `'site'`: `Destino('site', 'https://rockers502mc.com.gt', (('index.html', '/'),), ('index.html', '404.html'), ('rockers502.gt', 'rockers.fjbatresv.com'), None)`
    - `'landing'`: `Destino('landing', 'https://rockers.fjbatresv.com', (('index.html', '/'), ('en/index.html', '/en/')), ('index.html', 'en/index.html', '404.html'), ('rockers502.gt',), CSP_LANDING)` con `CSP_LANDING` = la CSP de *Global Constraints*.
  - `problemas_url(raiz: str, sitio: str, canonicas=(('index.html', '/'),), prohibidos=('rockers502.gt', 'rockers.fjbatresv.com')) -> list[str]`: misma firma posicional de hoy. Para cada par de `canonicas`: canonical y `og:url` = `sitio + ruta`, `og:image` empieza por `sitio + '/'`. Sitemap: lista de `<loc>` = `[sitio + ruta for _, ruta in canonicas]` en ese orden. Robots, prohibidos y "404 sin canonical" igual que hoy.
  - `problemas_csp_meta(html: str, pagina: str, csp: str) -> list[str]`: 1 problema si falta el `<meta http-equiv="Content-Security-Policy">` o su `content` no es exactamente `csp`.
  - `verificar(destino: Destino, sitio: str | None = None) -> list[str]`: corre CSP en línea, enlaces externos, `csp_meta` (si no es `None`) sobre `paginas`, y `problemas_url`.
  - CLI: `verificar_seguridad.py [--destino site|landing|todos] [--sitio URL]`. Default `--destino site` (no cambia lo que hace CI hoy). `--sitio` solo se acepta con un destino concreto; con `todos` sale con error de uso.
- Produces, en `verificar_enlaces.py`:
  - `PAGINAS_POR_DESTINO: dict[str, tuple[str, ...]]` = `{'site': ('site/index.html', 'site/404.html'), 'landing': ('landing/index.html', 'landing/en/index.html', 'landing/404.html')}`
  - `rotos(pagina: str, raiz: str) -> tuple[int, list[str]]`: (revisados, faltantes). Una ruta que empieza con `/` se resuelve desde `raiz`; una relativa, desde la carpeta de la página. Una ruta que resuelve fuera de `raiz` cuenta como faltante.
  - CLI: `verificar_enlaces.py [--destino site|landing|todos]`, default `site`. Misma salida que hoy.

- [x] **Paso 1: Tests nuevos (que fallen)**
  - En `test_verificar_seguridad.py` agregá:
    - `test_landing_dos_locs`: una raíz con `index.html` (canonical `…/`), `en/index.html` (canonical `…/en/`), sitemap con los dos `<loc>` → `problemas_url(raiz, 'https://rockers.fjbatresv.com', canonicas=DESTINOS['landing'].canonicas, prohibidos=DESTINOS['landing'].prohibidos) == []`. Con un solo `<loc>` → ≥1 problema.
    - `test_landing_puede_enlazar_al_club`: un `href="https://rockers502mc.com.gt/"` en la landing → 0 problemas.
    - `test_csp_meta`: con el `<meta>` exacto → `[]`; sin `<meta>` → 1; con `'unsafe-inline'` agregado → 1.
    - `test_destinos_por_defecto`: `DESTINOS['site'].sitio == 'https://rockers502mc.com.gt'` y `'rockers.fjbatresv.com' in DESTINOS['site'].prohibidos`.
  - Creá `test_verificar_enlaces.py` con `test_ruta_relativa_desde_subcarpeta` (`en/index.html` con `../assets/a.css` existente → 0 faltantes), `test_ruta_absoluta_desde_raiz` (`/assets/a.css` → 0) y `test_ruta_que_escapa_de_la_raiz` (`../../x` → 1 faltante).
- [x] **Paso 2:** `python3 -m unittest discover -s .github/scripts -p 'test_*.py' -v` → fallan solo los nuevos.
- [x] **Paso 3:** Implementá las interfaces de arriba. No cambies las aserciones de los 9 tests existentes.
- [x] **Paso 4:** Corré los tests (todos pasan), `python3 .github/scripts/verificar_seguridad.py` y `python3 .github/scripts/verificar_enlaces.py` (mismas salidas exitosas que hoy), y `python3 .github/scripts/verificar_seguridad.py --destino site --sitio https://rockers502mc.com.gt/` (sin problemas).
- [x] **Paso 5:** En `deploy.yml`, el step de `SITE_URL` pasa a `python3 .github/scripts/verificar_seguridad.py --destino site --sitio "$SITE_URL"`. Corré actionlint (`docker run --rm -v "$PWD:/repo" -w /repo rhysd/actionlint:latest`).
- [x] **Paso 6: Commit:** `Verificadores por destino: site y landing`

### Tarea 2: Esqueleto de la landing (ES)

**Files:**
- Create: `landing/index.html`, `landing/404.html`, `landing/assets/css/landing.css`, `landing/robots.txt`, `landing/sitemap.xml`, `landing/favicon.ico`, `landing/assets/img/apple-touch-icon.png`, `landing/assets/img/og.jpg`
- Test: `.github/scripts/test_verificar_enlaces.py` (`test_404_usa_rutas_absolutas`)

**Interfaces:**
- Consumes: `DESTINOS['landing']`, `verificar(...)`, `rotos(...)` (Tarea 1).
- Produces: el layout y las clases CSS que usan las Tareas 3 y 4. El `index.html` de esta tarea tiene encabezado, hero, una sección `#contacto` (el cierre) y pie. Las secciones 3 a 7 del spec quedan como `<section>` vacías con su `id` (`proyecto`, `decisiones`, `arquitectura`, `proceso`, `stack`) para llenar en la Tarea 3.

- [ ] **Paso 1:** Test `test_404_usa_rutas_absolutas` en `test_verificar_enlaces.py`: todo `src`/`href` local de `landing/404.html` empieza con `/`. Agregá la función `rutas_relativas(html: str) -> list[str]` en `verificar_enlaces.py` y hacé que el CLI la aplique a `landing/404.html` con `--destino landing`. Corré: falla porque la landing no existe.
- [ ] **Paso 2:** Escribí `landing.css` (tokens → base → componentes → secciones → responsive, como `site/`), `index.html` con `lang="es"`, la CSP en `<meta>`, link de salto a `#contenido`, `title` "Caso de estudio: sitio de Rockers 502 MC — Javier Batres", `meta description` que lo presente como caso de estudio (no como el sitio del club), canonical y `og:url` = `https://rockers.fjbatresv.com/`, `og:image` = `https://rockers.fjbatresv.com/assets/img/og.jpg`, JSON-LD `TechArticle` con `about` = `{"@type":"WebSite","url":"https://rockers502mc.com.gt/"}` y `author` = `{"@type":"Person","name":"Javier Batres","url":"https://fjbatresv.com"}`. `404.html` con `noindex`, sin canonical, rutas absolutas y enlace a `/` y `/en/`. `robots.txt` con `Allow: /` y `Sitemap: https://rockers.fjbatresv.com/sitemap.xml`. `sitemap.xml` con `/` y `/en/` (la Tarea 4 crea `/en/`; mientras tanto el verificador de la landing fallará solo por eso: está bien, no lo corras en CI hasta la Tarea 5).
- [ ] **Paso 3:** Imágenes, generadas en local con Pillow (no las agregues a CI): `og.jpg` 1200×630, ≤200 KB, fondo `--negro`, emblema (`site/assets/img/emblem@2x.webp`) y el titular; `favicon.ico` y `apple-touch-icon.png` copiados de `site/`.
- [ ] **Paso 4:** Corré los tests y `python3 .github/scripts/verificar_enlaces.py --destino landing` (falla solo por `landing/en/index.html` ausente) y `python3 .github/scripts/verificar_seguridad.py --destino landing` (falla solo por canonical/sitemap de `/en/`).
- [ ] **Paso 5: Navegador.** Serví `landing/` con un servidor que devuelva `landing/404.html` con status 404 para rutas inexistentes. Abrí `/` y `/en/no/existe`. Esperado: estilos y fuentes cargados en ambas, consola sin violaciones de CSP. Si no tenés navegador headless, decilo en el reporte; lo verifica el coordinador.
- [ ] **Paso 6: Commit:** `Esqueleto de la landing de portafolio`

### Tarea 3: Contenido en español

**Files:**
- Modify: `landing/index.html`, `landing/assets/css/landing.css`
- Create: `landing/assets/img/sitio-club.webp`

**Interfaces:**
- Consumes: layout y `id` de secciones de la Tarea 2.
- Produces: el texto ES final que la Tarea 4 traduce.

- [ ] **Paso 1: Medí los datos** y anotalos en el reporte final con el comando y su salida:
  - Código fuente: `wc -c site/index.html site/404.html site/assets/css/styles.css site/assets/js/main.js` → total en KB (÷1024, redondeado).
  - Peso y archivos de `site/`: `du -sh site && find site -type f | wc -l`.
  - Dependencias: `ls package.json requirements.txt 2>/dev/null | wc -l` → `0`.
  - Contraste de `--rojo-txt` sobre `--negro` con la fórmula WCAG 2.x (stdlib) → `5.17:1`.
  - Favicon: `git show --stat 6fd1ff1`.
- [ ] **Paso 2: Captura** del sitio del club (`https://rockers502mc.com.gt/`, 1440×900, solo el primer pantallazo) como `sitio-club.webp`, ≤150 KB, con `width`/`height` en el HTML y `alt` descriptivo.
- [ ] **Paso 3: Secciones**, en el orden y con el contenido del spec (*Estructura de la página*, puntos 2 a 9): hero con franja de 3 datos medidos; "El proyecto" (miembro, voluntario, con aprobación; restricciones reales); 5 tarjetas de decisiones, cada una con porqué técnico, "qué gana quien tiene un sitio así" y enlaces de evidencia de *Global Constraints*; arquitectura; proceso con agentes de IA (incluye el caso PR #2 → PR #3 y enlace a `docs/superpowers/plans/`); stack; cierre `#contacto` con los dos bloques y sus `mailto:`; pie.
- [ ] **Paso 4: Diagrama SVG** en línea en `#arquitectura`, con `role="img"`, `<title>` y `<desc>`. Muestra: `PR → Verificar el sitio`; `push a main → verificar → desplegar (OIDC) → S3 privado → CloudFront + cabeceras → visitante`; y aparte `landing/ → GitHub Pages → rockers.fjbatresv.com`. Responsivo: horizontal desde 768 px; en angosto, vertical (dos SVG alternados con `@media`, o uno con `viewBox` vertical; a tu criterio). Colores con tokens vía `currentColor`/clases, sin `style=""`.
- [ ] **Paso 5:** `python3 -m unittest discover -s .github/scripts -p 'test_*.py'` y `python3 .github/scripts/verificar_enlaces.py --destino landing` (falla solo por `/en/`).
- [ ] **Paso 6: Navegador** a 360 px y 1440 px: `document.documentElement.scrollWidth <= window.innerWidth` en ambos; diagrama legible a 360 px; navegación completa con teclado y foco visible; con `prefers-reduced-motion: reduce` no hay animaciones. Si no tenés navegador, decilo.
- [ ] **Paso 7: Commit:** `Contenido en español de la landing`

### Tarea 4: Versión en inglés

**Files:**
- Create: `landing/en/index.html`
- Modify: `landing/index.html` (hreflang y selector de idioma)
- Test: `.github/scripts/test_verificar_seguridad.py`

**Interfaces:**
- Consumes: texto ES (Tarea 3), `problemas_url` con `canonicas` (Tarea 1).
- Produces: `problemas_hreflang(raiz: str, sitio: str, canonicas) -> list[str]` en `verificar_seguridad.py`, llamado por `verificar()` cuando el destino tiene más de una canónica.

- [ ] **Paso 1: Tests** `test_hreflang_reciproco` (cada página de `canonicas` declara `<link rel="alternate" hreflang="es" href=sitio+'/'>`, `hreflang="en"` → `sitio+'/en/'`, y `hreflang="x-default"` → `sitio+'/'`; si falta uno → ≥1 problema) y `test_canonical_por_pagina` (`en/index.html` con canonical `sitio+'/'` → ≥1 problema). Corré: fallan.
- [ ] **Paso 2:** Implementá `problemas_hreflang`. Escribí `landing/en/index.html` (`lang="en"`, traducción fiel, mismos datos y enlaces, rutas relativas `../assets/…`, `mailto:` con asuntos en inglés, `og:locale` `en_US`; en ES `es_GT`). Agregá los tres `hreflang` a ambas páginas y el selector ES/EN en el encabezado (`aria-current="page"` en el idioma actual).
- [ ] **Paso 3:** Todo verde: tests, `verificar_enlaces.py --destino todos`, `verificar_seguridad.py --destino todos`.
- [ ] **Paso 4: Navegador** en `/en/`: consola sin violaciones de CSP, 360 px sin scroll horizontal.
- [ ] **Paso 5: Commit:** `Versión en inglés de la landing`

### Tarea 5: CI, despliegue a Pages y documentación

**Files:**
- Modify: `.github/workflows/deploy.yml` (job `verificar`)
- Create: `.github/workflows/landing.yml`
- Modify: `README.md`, `CLAUDE.md`

**Interfaces:**
- Consumes: CLIs con `--destino` (Tareas 1–4).
- Produces: el job requerido "Verificar el sitio" cubre `landing/`; workflow `Publicar la landing`.

- [ ] **Paso 1:** En el job `verificar` de `deploy.yml`, los steps de enlaces y seguridad pasan a `--destino todos`, y "Archivos críticos presentes" suma `landing/index.html landing/en/index.html landing/404.html landing/assets/css/landing.css`. El `on.push.paths` de `deploy.yml` **no** incluye `landing/**` (un cambio en la landing no debe redesplegar AWS).
- [ ] **Paso 2:** `landing.yml`, `name: Publicar la landing`:
  - `on`: `push` a `main` con `paths: ['landing/**', '.github/workflows/landing.yml']`; `workflow_dispatch`.
  - `permissions: contents: read` en la raíz. `concurrency: { group: pages, cancel-in-progress: false }`.
  - Job `verificar` (`name: Verificar la landing`): checkout (`persist-credentials: false`), tests, `verificar_enlaces.py --destino landing`, `verificar_seguridad.py --destino landing`.
  - Job `publicar` (`name: Publicar en GitHub Pages`): `needs: verificar`; `if: github.ref == 'refs/heads/main'`; `permissions: { pages: write, id-token: write }`; `environment: { name: github-pages, url: ${{ steps.deployment.outputs.page_url }} }`; steps: checkout, `configure-pages`, `upload-pages-artifact` con `path: landing`, `deploy-pages` con `id: deployment`.
- [ ] **Paso 3:** actionlint sin errores; `grep -nE 'uses: [^@]+@v[0-9]' .github/workflows/*.yml` vacío.
- [ ] **Paso 4:** `README.md`: sección "Landing de portafolio" (qué es, dónde vive, cómo previsualizar con `cd landing && python3 -m http.server 8081`, cómo se publica, que "Enforce HTTPS" se activa en Settings → Pages tras el primer deploy). `CLAUDE.md`: describir `landing/`, sus restricciones (CSP en `<meta>` porque Pages no permite cabeceras, y por eso `frame-ancestors` no aplica; sin JS, rutas absolutas en la 404, relación voluntaria con el club) y los verificadores por destino.
- [ ] **Paso 5: Commit:** `Publicar la landing en GitHub Pages`

## Después del merge (coordinador / Javier)

1. Confirmar que "Publicar la landing" termine en verde y que `https://rockers.fjbatresv.com/` y `/en/` respondan 200.
2. Activar "Enforce HTTPS" en Settings → Pages (`gh api -X PUT repos/fjbatresv/rocker-mc/pages -F https_enforced=true`).
3. Search Console: agregar la propiedad `rockers.fjbatresv.com` y enviar el sitemap.
4. Si ya está aplicada la Tarea 5 del plan anterior (Actions restringidas), comprobar que las cuatro actions de Pages pasan la lista permitida (son de GitHub, deberían).
