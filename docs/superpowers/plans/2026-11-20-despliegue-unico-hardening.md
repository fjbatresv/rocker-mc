# Despliegue único en AWS + hardening — plan de implementación

> **Para agentes (Codex u otro):** ejecutá el plan tarea por tarea, en orden, marcando los `- [ ]`. Si tenés las skills de superpowers, usá `superpowers:executing-plans`. Cada tarea termina en un commit propio en la rama `hardening-seo-ux`. Leé `CLAUDE.md` antes de empezar: el repo está en español (voseo) y no tiene build.

**Goal:** Dejar un solo despliegue a AWS (el Environment `dev`), público e indexable en `https://rockers.fjbatresv.com/`, con el workflow, la infraestructura y la configuración de GitHub endurecidos.

**Architecture:** Sitio estático en `site/` publicado a S3 + CloudFront por `.github/workflows/deploy.yml`. Se elimina el job de producción; el job que queda conserva el Environment `dev` para no tocar el rol de IAM (su trust policy fija `repo:fjbatresv/rocker-mc:environment:dev`). Un script Python nuevo verifica en CI que el HTML sea compatible con la CSP y que las URLs absolutas coincidan con `SITE_URL`. Las cabeceras de seguridad se aplican con una *response headers policy* de CloudFront definida en `infra/`.

**Tech Stack:** HTML/CSS/JS sin dependencias, Python 3 (solo biblioteca estándar, `unittest`), GitHub Actions, AWS CLI v2, `gh`, `jq`.

**Spec:** este documento. Las decisiones vienen de la sesión del 2026-11-20 y están en la sección *Decisiones*.

## Decisiones (spec)

1. Desde hoy hay **dos** despliegues: (a) AWS, el actual Environment `dev`; (b) una landing de portafolio en GitHub Pages, que se hace en **otra rama y otro plan** (no entra acá).
2. El sitio de AWS es el sitio público del club: **indexable**. Se elimina el paso que reemplaza `robots.txt` y borra `sitemap.xml`.
3. URL pública: `https://rockers.fjbatresv.com/`. Es el valor de la variable `SITE_URL` del Environment `dev` (está guardado **sin** barra final). Reemplaza a `https://www.rockers502.gt/` en todo el repo.
4. Se aplican los cambios de configuración de GitHub con `gh`: ruleset en `main`, `dev` desplegable solo desde `main`, borrar los Environments `prod` y `produccion`.
5. Ya está hecho en esta rama (no repetir): accesibilidad, contraste (`--rojo-txt`), carrusel, SEO on-page, favicon comprimido, HTML sin `style="…"`.

## Global Constraints

- Sin dependencias nuevas: nada de `package.json`, ni build, ni librerías de Python fuera de la estándar.
- Todo texto, comentario, nombre de step y mensaje de commit va en español con voseo ("editá", "corré"), igual que el resto del repo.
- Las actions se fijan por SHA completo con la versión en comentario. Usá exactamente estas:
  - `actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1 # v7.0.1`
  - `aws-actions/configure-aws-credentials@e1253824e5c10ff9df46874f81ed3ec929e19cfd # v6.3.0`
- Ningún secreto se interpola con `${{ secrets.* }}` dentro de un `run:`: pasa por `env:` y se usa como `"$VAR"`.
- La CSP es exactamente la de la Tarea 4; el HTML de `site/` no puede tener `style="…"`, handlers `on*=` ni `<script>` en línea salvo `type="application/ld+json"`.
- `https://rockers.fjbatresv.com` es la única URL absoluta del sitio; ningún archivo de `site/` puede seguir mencionando `rockers502.gt`.

## Review Focus

1. **Un PR que no toca `site/`.** El check requerido "Verificar el sitio" tiene que correr igual; si no corre, GitHub bloquea el merge para siempre. → Tarea 3: `pull_request` sin filtro `paths` y un `grep` que lo pruebe.
2. **`workflow_dispatch` lanzado desde otra rama.** No debe desplegar. → Tarea 3 (condición `if:` del job) y Tarea 5 (política de ramas del Environment).
3. **`SITE_URL` con o sin barra final.** Las dos formas deben validar igual. → Tarea 1: `test_sitio_con_y_sin_barra`.
4. **Scripts permitidos y prohibidos.** `<script src>` y `ld+json` pasan; `<script type="module">` en línea y `onclick=` fallan. → Tarea 1: `test_scripts`.
5. **Una CSP que rompa el sitio en producción** (fuentes de Google, el ruido SVG `data:` de `body::before`, el JSON-LD). → Tarea 4, paso de verificación en el navegador con la consola sin violaciones.

---

### Tarea 1: Verificador de seguridad del HTML

**Files:**
- Create: `.github/scripts/verificar_seguridad.py`
- Create: `.github/scripts/test_verificar_seguridad.py`

**Interfaces:**
- Produces:
  - `SITIO = 'https://rockers.fjbatresv.com'` (constante del módulo)
  - `problemas_csp(html: str, pagina: str) -> list[str]`: un mensaje por cada `style="`, cada atributo `on<evento>=` y cada `<script>` sin `src` cuyo `type` no sea `application/ld+json`.
  - `problemas_url(raiz: str, sitio: str) -> list[str]`: normaliza `sitio` quitando la barra final y exige:
    - `index.html`: `canonical` y `og:url` iguales a `sitio + '/'`; `og:image` empieza por `sitio + '/'`.
    - `sitemap.xml`: un único `<loc>` igual a `sitio + '/'`.
    - `robots.txt`: contiene `Sitemap: ` + `sitio` + `/sitemap.xml` y no contiene `Disallow: /` como regla completa.
    - Ningún archivo de texto bajo `raiz` contiene `rockers502.gt`.
    - `404.html` no tiene `rel="canonical"`.
  - `problemas_enlaces_externos(html: str, pagina: str) -> list[str]`: todo `<a … target="_blank">` debe llevar `rel` con `noopener`.
  - CLI: `python3 .github/scripts/verificar_seguridad.py [--sitio URL]`, que usa `SITIO` por defecto, revisa `site/index.html` y `site/404.html`, imprime los problemas y sale con 1 si hay alguno. Si no hay, imprime `Seguridad y URLs: sin problemas.` y sale con 0. Mismo estilo que `verificar_enlaces.py`.

- [x] **Paso 1: Escribí los tests (`unittest`, con carpetas temporales de `tempfile`).** Escribí `test_sitio_con_y_sin_barra`, `test_scripts`, `test_style_en_linea`, `test_robots_bloqueado`, `test_dominio_viejo`, `test_canonical_en_404` y `test_target_blank_sin_noopener`. Estas son las aserciones concretas:

```python
def test_sitio_con_y_sin_barra(self):
    raiz = sitio_valido(self.tmp)            # helper: escribe index/404/robots/sitemap correctos
    self.assertEqual(problemas_url(raiz, 'https://rockers.fjbatresv.com'), [])
    self.assertEqual(problemas_url(raiz, 'https://rockers.fjbatresv.com/'), [])

def test_scripts(self):
    ok = '<script src="assets/js/main.js" defer></script><script type="application/ld+json">{}</script>'
    self.assertEqual(problemas_csp(ok, 'x.html'), [])
    self.assertEqual(len(problemas_csp('<script type="module">alert(1)</script>', 'x.html')), 1)
    self.assertEqual(len(problemas_csp('<script>alert(1)</script>', 'x.html')), 1)
    self.assertEqual(len(problemas_csp('<button onclick="x()">', 'x.html')), 1)

def test_style_en_linea(self):
    self.assertEqual(len(problemas_csp('<p style="margin:0">', 'x.html')), 1)

def test_robots_bloqueado(self):            # robots con "Disallow: /" → al menos 1 problema
def test_dominio_viejo(self):               # "rockers502.gt" en cualquier archivo → al menos 1 problema
def test_canonical_en_404(self):            # 404.html con rel="canonical" → al menos 1 problema
def test_target_blank_sin_noopener(self):   # <a target="_blank" href="https://x"> → 1 problema
```

- [x] **Paso 2:** Corré `python3 -m unittest discover -s .github/scripts -p 'test_*.py' -v`. Tiene que fallar con `ModuleNotFoundError: verificar_seguridad`.
- [x] **Paso 3:** Implementá `verificar_seguridad.py` con las firmas de arriba, usando `re` sobre el texto (igual que `verificar_enlaces.py`; no hace falta un parser de HTML). Para "Disallow: /" como regla completa, buscá la línea con `^Disallow:\s*/\s*$` en modo multilínea.
- [x] **Paso 4:** Corré otra vez los tests. Tienen que pasar los 7.
- [x] **Paso 5:** Corré `python3 .github/scripts/verificar_seguridad.py`. **Tiene que fallar** y listar los `rockers502.gt` de `site/`; es lo que arregla la Tarea 2.
- [x] **Paso 6: Commit**

```bash
git add .github/scripts/verificar_seguridad.py .github/scripts/test_verificar_seguridad.py
git commit -m "Verificador de CSP y URLs absolutas del sitio"
```

### Tarea 2: Mover el sitio a rockers.fjbatresv.com

**Files:**
- Modify: `site/index.html` (canonical, `og:url`, `og:image`, y en el JSON-LD los `@id`, `url` y `logo`)
- Modify: `site/sitemap.xml`, `site/robots.txt`
- Modify: `deploy.sh`, `CLAUDE.md`, `README.md` (solo las menciones de dominio; la reescritura de despliegue es de la Tarea 3)

**Interfaces:**
- Consumes: `verificar_seguridad.py` (Tarea 1).

- [x] **Paso 1:** Reemplazá `https://www.rockers502.gt/` por `https://rockers.fjbatresv.com/` en `site/`. Los `@id` del JSON-LD quedan `https://rockers.fjbatresv.com/#sitio` y `…/#club`.
- [x] **Paso 2:** Cambios en `deploy.sh`:
  - `ROCKERS_BUCKET` y `ROCKERS_DISTRIBUTION_ID` pasan a ser **obligatorias**: si faltan, sale con un mensaje claro (`: "${ROCKERS_BUCKET:?Definí ROCKERS_BUCKET}"`). Se quitan los valores por defecto `rockers502-gt-site` y `E000000000000`.
  - El mensaje final pasa a `https://rockers.fjbatresv.com/`.
- [x] **Paso 3:** En `CLAUDE.md`, la sección "Domain-dependent values" pasa a nombrar `rockers.fjbatresv.com` y el verificador. En `README.md`, el punto 1 de "Pendientes" se reemplaza por: "El dominio es `rockers.fjbatresv.com`; si cambia, actualizá `SITIO` en `verificar_seguridad.py` y corré el verificador: te lista cada archivo a tocar."
- [x] **Paso 4:** Corré `python3 .github/scripts/verificar_seguridad.py && python3 .github/scripts/verificar_enlaces.py`. Las dos salidas tienen que ser exitosas.
- [x] **Paso 5:** Corré `grep -rn "rockers502.gt" site deploy.sh CLAUDE.md`. No tiene que devolver nada.
- [x] **Paso 6: Commit:** `git commit -am "Publicar el sitio en rockers.fjbatresv.com"`

### Tarea 3: Workflow de un solo despliegue, endurecido

**Files:**
- Modify: `.github/workflows/deploy.yml` (reescritura)
- Create: `.github/dependabot.yml`
- Modify: `README.md`, sección "Despliegue" (reescritura: un entorno, sin tabla dev/prod)
- Modify: `CLAUDE.md`, sección "Deployment" (un solo job `desplegar` en el Environment `dev`, indexable; los PR solo verifican; quitar la mención a `robots.txt` reemplazado y al job `prod`)

**Interfaces:**
- Consumes: `verificar_seguridad.py --sitio`.
- Produces: el job con `name: Verificar el sitio` (contexto del check requerido en la Tarea 5) y el job `desplegar` con `environment: dev`.

- [x] **Paso 1: Reescribí `deploy.yml` con esta estructura**
  - `name: Desplegar`
  - `on`:
    - `push` a `main` con `paths: ['site/**', '.github/workflows/deploy.yml', '.github/scripts/**']`.
    - `pull_request` a `main` **sin `paths`**: el check requerido tiene que correr en todo PR.
    - `workflow_dispatch` sin inputs.
  - `permissions: contents: read` a nivel raíz. Nada de `id-token` en la raíz.
  - Job `verificar`, con `name: Verificar el sitio`:
    - checkout con `persist-credentials: false`;
    - el mismo step "Archivos críticos presentes";
    - `python3 -m unittest discover -s .github/scripts -p 'test_*.py'`;
    - `verificar_enlaces.py`;
    - `verificar_seguridad.py`.
  - Job `desplegar`, con `name: Desplegar en AWS`:
    - `needs: verificar`;
    - `if: github.event_name != 'pull_request' && github.ref == 'refs/heads/main'`;
    - `permissions: { contents: read, id-token: write }`;
    - `environment: { name: dev, url: ${{ vars.SITE_URL }} }`;
    - `concurrency: { group: desplegar-aws, cancel-in-progress: false }`;
    - `timeout-minutes: 20`.
  - Steps de `desplegar`, en orden:
    1. checkout con `persist-credentials: false`.
    2. "Comprobar la configuración del entorno": idéntico al actual, con mensaje `'dev'`.
    3. "Las URLs del sitio coinciden con SITE_URL": `python3 .github/scripts/verificar_seguridad.py --sitio "$SITE_URL"`.
    4. Asumir el rol.
    5. Subir assets.
    6. Subir el HTML.
    7. Content-Type de robots **y** sitemap (como el prod actual).
    8. Invalidar.
    9. Resumen con `Indexable: true`.
  - Los secretos se pasan por `env:` (`BUCKET`, `DISTRIBUTION`) y se usan como `"$BUCKET"`.
  - **Se elimina** el step "Bloquear la indexación" y el job `prod` completo.
- [x] **Paso 2:** Creá `.github/dependabot.yml` con `version: 2` y un único bloque: `package-ecosystem: github-actions`, `directory: /`, `schedule.interval: weekly`, `commit-message.prefix: "Actions"`.
- [x] **Paso 3: Verificación estática**
  - Corré `docker run --rm -v "$PWD:/repo" -w /repo rhysd/actionlint:latest -color` (o `actionlint` si está instalado). Esperado: sin errores.
  - Corré `grep -n 'secrets\.' .github/workflows/deploy.yml`. Esperado: solo líneas dentro de bloques `env:` o `with:`, ninguna en un `run:`.
  - Corré `grep -nE 'uses: [^@]+@v[0-9]' .github/workflows/deploy.yml`. Esperado: nada (todo fijado por SHA).
  - Corré `grep -n -A3 'pull_request:' .github/workflows/deploy.yml`. Esperado: sin `paths`.
  - Corré `grep -c 'prod' .github/workflows/deploy.yml`. Esperado: `0`.
- [x] **Paso 4:** En `README.md`, reescribí "Despliegue" para un solo entorno:
  - qué dispara el workflow;
  - por qué el Environment se sigue llamando `dev` (el rol de IAM);
  - las 2 variables y los 3 secretos;
  - que los PR corren solo la verificación.
  - Borrá las instrucciones de un segundo bucket/distribución, el `crear-rol.sh prod` y la tabla dev/prod.
  - Actualizá el diagrama a `push a main ──→ verificar ──→ desplegar` y `PR ──→ verificar`.
- [x] **Paso 5: Commit:** `git add -A .github README.md CLAUDE.md && git commit -m "Un solo despliegue a AWS, indexable y con el workflow endurecido"`

### Tarea 4: Cabeceras de seguridad en CloudFront

**Files:**
- Create: `infra/cabeceras-seguridad.json` (un `ResponseHeadersPolicyConfig`)
- Create: `infra/aplicar-cabeceras.sh`
- Modify: `infra/README.md` (sección nueva "Cabeceras de seguridad")
- Modify: `infra/crear-rol.sh` (solo el ejemplo y la ayuda: quitar la línea de `prod`)

**Interfaces:**
- Produces: la política `rockers502-cabeceras-seguridad`, asociada al `DefaultCacheBehavior` de la distribución.

- [x] **Paso 1: Escribí `cabeceras-seguridad.json`** con `Name: rockers502-cabeceras-seguridad` y estos valores exactos, todos con `Override: true`:
  - `ContentSecurityPolicy`: `default-src 'none'; script-src 'self'; style-src 'self' https://fonts.googleapis.com; font-src https://fonts.gstatic.com; img-src 'self' data:; base-uri 'none'; form-action 'none'; frame-ancestors 'none'; upgrade-insecure-requests`
  - `StrictTransportSecurity`: `AccessControlMaxAgeSec: 31536000`, `IncludeSubdomains: true`, `Preload: false`
  - `ContentTypeOptions`: activado
  - `FrameOptions`: `DENY`
  - `ReferrerPolicy`: `strict-origin-when-cross-origin`
  - `CustomHeadersConfig`: `Permissions-Policy: camera=(), microphone=(), geolocation=(), payment=(), usb=()`
- [x] **Paso 2: Escribí `aplicar-cabeceras.sh <distribution-id>`.** Usa `set -euo pipefail`, es idempotente y requiere AWS CLI v2 y `jq`. Hace esto:
  1. Busca la política por nombre con `aws cloudfront list-response-headers-policies --type custom`.
  2. Si no existe, la crea (`create-response-headers-policy`).
  3. Si existe, la actualiza con `update-response-headers-policy --id … --if-match <ETag>`.
  4. Lee `get-distribution-config`. Si `DefaultCacheBehavior.ResponseHeadersPolicyId` ya es esa política, imprime "ya asociada" y termina.
  5. Si no, la escribe con `jq` y llama a `update-distribution --if-match <ETag>`.
  6. Al final imprime el `curl -sI` que hay que correr para verificar.
  Lo corre una persona con permisos de administración: el rol de despliegue **no** recibe permisos nuevos.
- [x] **Paso 3:** Corré `bash -n infra/aplicar-cabeceras.sh && jq . infra/cabeceras-seguridad.json >/dev/null && echo ok`. Esperado: `ok`.
- [x] **Paso 4: Verificá la CSP en local, antes de que la aplique una persona**
  1. Serví `site/` con un servidor que mande la cabecera: `python3 -c` con `http.server.SimpleHTTPRequestHandler` y `end_headers` sobrescrito para agregar `Content-Security-Policy` con el valor del Paso 1, sin `upgrade-insecure-requests` (en `http://localhost` no aplica).
  2. Abrí `http://localhost:<puerto>/` y `/no-existe` en un navegador, y la 404 servida directamente en `/404.html`.
  3. Esperado: consola sin violaciones de CSP, fuentes Oswald/Barlow cargadas y textura de grano visible.
- [x] **Paso 5:** En `infra/README.md`, documentá:
  - qué hace cada cabecera;
  - por qué `style-src` no lleva `'unsafe-inline'` (el HTML no tiene `style="…"` y `verificar_seguridad.py` lo vigila);
  - que si se agrega un tercero (analytics, un iframe) hay que ampliar la CSP aquí.
- [x] **Paso 6: Commit:** `git add infra && git commit -m "Cabeceras de seguridad para CloudFront"`

### Tarea 5: Configuración de GitHub con `gh`

Se ejecuta **después** de que el PR de esta rama esté fusionado en `main` y el primer despliegue haya terminado en verde. Antes, el workflow viejo todavía referencia `prod`.

**Files:** ninguno del repo, salvo `README.md` (Paso 6).

- [ ] **Paso 1:** Limitá `dev` a la rama `main`:

```bash
gh api -X PUT repos/fjbatresv/rocker-mc/environments/dev \
  -F 'deployment_branch_policy[protected_branches]=false' -F 'deployment_branch_policy[custom_branch_policies]=true'
gh api -X POST repos/fjbatresv/rocker-mc/environments/dev/deployment-branch-policies -f name=main -f type=branch
```

- [ ] **Paso 2:** Borrá los Environments que sobran: `gh api -X DELETE repos/fjbatresv/rocker-mc/environments/prod` y lo mismo con `produccion`.
- [ ] **Paso 3:** Creá el ruleset de `main` con `gh api -X POST repos/fjbatresv/rocker-mc/rulesets --input -` y este JSON:
  - `name: "main protegida"`, `target: branch`, `enforcement: active`;
  - `conditions.ref_name.include: ["~DEFAULT_BRANCH"]`;
  - reglas:
    - `deletion`;
    - `non_fast_forward`;
    - `pull_request` con `required_approving_review_count: 0`;
    - `required_status_checks` con el contexto `"Verificar el sitio"` y `strict_required_status_checks_policy: false`.
  - Sin `bypass_actors`.
- [ ] **Paso 4: Repo y Actions**

```bash
gh repo edit fjbatresv/rocker-mc --delete-branch-on-merge
gh api -X PATCH repos/fjbatresv/rocker-mc -F 'security_and_analysis[secret_scanning][status]=enabled' \
  -F 'security_and_analysis[secret_scanning_push_protection][status]=enabled'
gh api -X PUT repos/fjbatresv/rocker-mc/actions/permissions -F enabled=true -f allowed_actions=selected -F sha_pinning_required=true
gh api -X PUT repos/fjbatresv/rocker-mc/actions/permissions/selected-actions \
  -F github_owned_allowed=true -F verified_allowed=false -f 'patterns_allowed[]=aws-actions/*'
```

- [ ] **Paso 5: Verificación**
  - `gh api repos/fjbatresv/rocker-mc/environments --jq '[.environments[].name]'` → `["dev"]`
  - `gh api repos/fjbatresv/rocker-mc/rulesets --jq '.[].name'` → `main protegida`
  - Abrí un PR de prueba que solo toque `README.md`: el check "Verificar el sitio" corre y el job "Desplegar en AWS" aparece como *skipped*.
- [ ] **Paso 6:** En `README.md`, agregá una sección corta "Protecciones del repositorio" con lo aplicado. Hacé commit en una rama nueva con PR, porque `main` ya no acepta push directo.

## Pendientes fuera del código (para la persona dueña de la cuenta de AWS)

1. **DNS:** `rockers.fjbatresv.com` responde NXDOMAIN. Creá en Route 53, zona `fjbatresv.com`, registros alias **A y AAAA** hacia la distribución de CloudFront. Comprobá que la distribución tenga ese *alternate domain name* y un certificado de ACM en `us-east-1` que lo cubra.
2. **Cabeceras:** corré `infra/aplicar-cabeceras.sh <distribution-id>`. Después corré `curl -sI https://rockers.fjbatresv.com` y verificá las seis cabeceras.
3. **HTTPS:** la distribución debe tener `Redirect HTTP to HTTPS`. Verificalo con `curl -sI http://rockers.fjbatresv.com`, que tiene que dar `301`.
4. **Recursos de prod que quedan huérfanos:**
   - el rol de IAM `rockers502-deploy-prod`;
   - el bucket y la distribución de prod, si se llegaron a crear.
5. **Search Console:** el dominio `fjbatresv.com` ya está verificado por TXT. Agregá la propiedad del subdominio y enviá `https://rockers.fjbatresv.com/sitemap.xml`.
6. **Emblema:** `Assets/logo.jpeg` todavía dice **"MG"**. Cuando exista el arte con "MC", reemplazalo y corré `python3 make_emblem.py`.
7. **Redes:** los enlaces a Instagram (`rockers502mggt`) y TikTok (`rockers.mg.guate`) conservan "mg" en el usuario. Confirmá si las cuentas se renombraron.
