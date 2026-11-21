# Landing de portafolio en rockers.fjbatresv.com — diseño

Fecha: 2026-11-21 · Estado: borrador para aprobación (incluye respuestas del 2026-11-21)

## Intención

Una página pública en `https://rockers.fjbatresv.com/` que presenta el sitio de Rockers 502 MC como **caso de estudio de ingeniería** dentro del portafolio de Javier Batres. No es el sitio del club (ese es `https://rockers502mc.com.gt/`, en AWS); es una pieza que habla *sobre* el proyecto: qué se construyó, con qué tecnologías, qué patrones y arquitectura, y por qué se tomó cada decisión.

**Para quién:** reclutadores con conocimiento técnico (el tipo que abre el repo después de leer la página) y, en segundo lugar, personas con criterio técnico que querrían un sitio así para su club, negocio u organización.

**Qué debe lograr:** que el lector termine con ganas de **contratar a Javier** o de **encargarle algo parecido**. Cada sección empuja hacia uno de los dos botones del cierre.

## Objetivos

1. Contar el proyecto como una serie de **decisiones con su porqué**, no como una lista de features.
2. Que cada afirmación sea **verificable**: enlaza al archivo, commit o PR del repo `fjbatresv/rocker-mc` que la respalda.
3. Hablarle a las dos audiencias en la misma página: cada decisión trae su porqué técnico y una línea de "qué gana el cliente".
4. Que la landing **practique lo que predica**: sin framework ni build, accesible AA, CSP compatible, liviana, verificada en CI.
5. Cerrar con dos salidas claras: contratar / encargar un proyecto.

## No objetivos

- No reemplaza ni duplica el contenido del sitio del club (historia, emblema, requisitos de ingreso). Lo resume en una línea y enlaza.
- No tiene formulario de contacto, backend, analytics ni cookies.
- No es un blog ni una plantilla para otros casos de estudio (si después hay más, se verá).

## Anti-objetivos (fallaría aunque funcione)

- **Inflar:** números inventados, "enterprise-grade", métricas que no se midieron. Todo dato de la página se mide del repo o del sitio en vivo.
- **Competir con el sitio del club en buscadores:** la landing no se presenta como el sitio de Rockers 502 MC; su `title`, `description` y JSON-LD la describen como caso de estudio.
- **Contradecir el argumento:** meter Node, dependencias, un build o `style="…"` en línea en una página que defiende no tenerlos.
- **Esconder el uso de IA o los errores:** la sección de proceso cuenta el error real del dominio y cómo se atrapó.

## Enfoques considerados

| Enfoque | A favor | En contra |
|---|---|---|
| **A. HTML/CSS estático en `landing/` de este repo, sin build, publicado con GitHub Pages** ✅ | Coherente con el argumento "sin build"; reutiliza los verificadores en CI; vive junto a la evidencia que enlaza | Contenido escrito a mano en HTML; dos idiomas = dos archivos que mantener en paralelo |
| B. Astro/Starlight en este repo | Markdown/MDX, componentes, i18n cómodo | Agrega Node, dependencias y build a un repo que presume no tenerlos |
| C. Página dentro de `fjbatresv_web` | Todo el portafolio junto | Separa la página de la evidencia; no usa `rockers.fjbatresv.com` |

**Elegido: A** (decisión de Javier, 2026-11-21).

## Decisiones tomadas en la conversación

1. **Dirección visual A, "heredada del club":** negro `--negro #0A0A0B`, rojo `#C1121F` (y `--rojo-txt #EA4650` para texto chico), Oswald / Barlow / Barlow Condensed de Google Fonts, igual que `site/`. Mismas reglas de accesibilidad: el rojo `#C1121F` nunca para texto de párrafo; `prefers-reduced-motion` apaga toda animación.
2. **Idioma:** español como página principal (`landing/index.html`, `lang="es"`), inglés en `landing/en/index.html` (`lang="en"`). Ambas con `hreflang` recíproco y `x-default` → español. Selector de idioma visible en el encabezado.
3. **Contacto:** solo **correo `fjbatresv@gmail.com`** (uno solo para ambas salidas; Javier aprobó publicarlo) y **la web personal `https://fjbatresv.com`**. Nada de LinkedIn ni formulario. Cada salida puede llevar un asunto prellenado distinto en el `mailto:` (por ejemplo "Oportunidad laboral" / "Proyecto web").
4. **IA:** el trabajo con agentes de IA es **una sección propia** (no el eje de la página).
5. **Diagrama de arquitectura:** SVG en línea, hecho a mano, **responsivo** (se reacomoda a vertical en pantallas angostas), con `<title>`/`<desc>` accesibles. Sin librerías.
6. **Relación con el club:** Javier es **miembro** de Rockers 502 MC e hizo el sitio **de forma voluntaria, con la aprobación del club**. No fue un encargo pagado y la página no debe presentarlo como tal.

## Estructura de la página

Orden de arriba hacia abajo (igual en ambos idiomas):

1. **Encabezado:** marca "ROCKERS 502 · CASE STUDY", anclas a Decisiones · Arquitectura · Proceso · Stack, selector ES/EN.
2. **Hero:** titular (propuesta: "Un sitio chico. Ingeniería grande." / "A small site. Serious engineering."), una línea de qué es, botones **Trabajemos juntos** (ancla al cierre) y **Ver código** (repo), enlace al sitio en vivo, franja con 3 datos medidos (ver *Datos*).
3. **El proyecto:** como miembro del club, Javier construyó de forma voluntaria (y con aprobación del club) su sitio: identidad, historia, estructura y requisitos de ingreso. Las restricciones salen de esa realidad: un club que no tiene a nadie para mantener un sistema, sin presupuesto para servidores y con visitantes que llegan desde el celular. Una captura del sitio del club.
4. **Decisiones** (núcleo): cinco tarjetas. Cada una con: título, el porqué técnico (2–3 líneas), "qué gana quien tiene un sitio así" (1 línea, en términos de costo, riesgo o alcance; sin insinuar que el club fue un cliente), y enlace(s) a la evidencia.
   - Sin framework ni build → `site/`, ausencia de `package.json`.
   - Accesibilidad medida → `--rojo-txt` y contrastes calculados, foco visible, menú con Escape, `prefers-reduced-motion`, objetivo táctil de 24 px en el carrusel (`styles.css`, `main.js`).
   - Seguridad verificable → CSP sin `unsafe-inline` (`infra/cabeceras-seguridad.json`), `verificar_seguridad.py` en CI, actions fijadas por SHA, despliegue por OIDC sin llaves.
   - Peso y velocidad → WebP, favicon 338 KB → 52 KB, JS mínimo y opcional (el sitio funciona sin JS).
   - SEO técnico → JSON-LD `@graph`, canonical, sitemap, 404 correcta.
5. **Arquitectura:** diagrama SVG. Flujo principal: `PR → Verificar el sitio (check obligatorio)`; `push a main → verificar → desplegar (OIDC) → S3 privado → CloudFront + política de cabeceras → visitante`. Rama secundaria: `landing/ → GitHub Pages → rockers.fjbatresv.com`. Debajo, 3–4 líneas explicando por qué cada pieza.
6. **Cómo se trabajó: agentes de IA:** el ciclo plan escrito → Codex implementa → Claude coordina y revisa → verificadores automáticos → PR. Enlace al plan en `docs/superpowers/plans/`. El caso honesto: el PR #2 publicó el dominio equivocado; se detectó revisando el sitio en vivo y se corrigió en el PR #3, que además endureció el verificador para que no vuelva a pasar.
7. **Stack:** lista compacta: HTML, CSS, JavaScript sin dependencias, Python (stdlib, verificadores y tests), GitHub Actions, AWS S3, CloudFront, IAM OIDC, GitHub Pages.
8. **Cierre (fondo rojo):** "¿Te sumás a la rodada?" con dos bloques: **Para tu equipo** (contratarme) y **Para tu proyecto** (encargar un sitio así). Ambos llevan a `mailto:fjbatresv@gmail.com` (con asunto prellenado distinto) y a `https://fjbatresv.com`.
9. **Pie:** crédito, enlace al repo, enlace al sitio del club.

## Datos

Todo número que aparezca en la página se mide, no se estima, y el plan dice con qué comando. Valores de referencia al 2026-11-21: `site/` pesa 2.1 MB en 26 archivos; el código fuente (index.html + 404.html + styles.css + main.js) suma ~52 KB; 0 dependencias; contraste de `--rojo-txt` 5.17:1. Si un dato cambia antes de publicar, manda el medido.

## Restricciones técnicas

- **Ubicación:** carpeta `landing/` en la raíz del repo. Archivos: `landing/index.html`, `landing/en/index.html`, `landing/404.html`, `landing/assets/css/landing.css`, `landing/assets/img/…`, `landing/robots.txt`, `landing/sitemap.xml`, favicon. Sin JS salvo que algo lo justifique; si se usa, debe ser opcional (la página funciona sin él).
- **Sin build, sin dependencias, sin `style="…"`, sin handlers `on*=`, sin `<script>` en línea salvo `application/ld+json`.**
- **GitHub Pages no permite cabeceras HTTP propias.** La CSP va en `<meta http-equiv="Content-Security-Policy">` con las mismas fuentes que la de AWS, salvo lo que en `<meta>` no aplica (`frame-ancestors`; documentarlo).
- **Reutilizar estilos sin acoplar:** la landing copia los tokens que necesita a su propio `landing.css`; no enlaza `site/assets/css/styles.css` (son sitios y despliegues distintos).
- **Imágenes:** capturas del sitio del club generadas una vez y guardadas como WebP; `og:image` propia 1200×630 para la landing.
- **SEO:** `canonical` a `https://rockers.fjbatresv.com/` (y `/en/`), `hreflang`, JSON-LD de tipo `CreativeWork`/`TechArticle` sobre el caso de estudio con `about` → el sitio del club y `author` → Javier Batres. Indexable.
- **Verificación en CI:** el job existente **"Verificar el sitio"** (check obligatorio en PRs) debe también verificar `landing/`: enlaces locales rotos, compatibilidad con la CSP, `rel="noopener"` en `target="_blank"`, y que `landing/` no use `rockers502mc.com.gt` como canonical. Extender los verificadores existentes con un parámetro de raíz en lugar de duplicarlos.
- **Despliegue:** workflow nuevo `.github/workflows/landing.yml` que, en `push` a `main` con cambios en `landing/**` (y en `workflow_dispatch` desde `main`), vuelve a verificar y publica `landing/` con `actions/configure-pages`, `actions/upload-pages-artifact` y `actions/deploy-pages`, fijadas por SHA, permisos mínimos (`pages: write`, `id-token: write` solo en el job de deploy), Environment `github-pages`.
- **Dominio (ya configurado al 2026-11-21):** Pages está en modo *workflow* con dominio propio `rockers.fjbatresv.com`, y el DNS ya tiene `CNAME rockers.fjbatresv.com → fjbatresv.github.io`. No hace falta archivo `CNAME` en `landing/`. Pendiente fuera del código: activar "Enforce HTTPS" después del primer despliegue.
- **Verificadores por raíz:** al parametrizar `verificar_seguridad.py` por raíz, el dominio esperado y los prohibidos dependen de la raíz: en `site/` se espera `rockers502mc.com.gt` y se prohíbe `rockers.fjbatresv.com`; en `landing/` se espera `rockers.fjbatresv.com` como canonical y se permite enlazar a `rockers502mc.com.gt`. El `sitemap.xml` de la landing tiene **dos** `<loc>` (`/` y `/en/`), mientras que el de `site/` sigue teniendo uno.
- **Convenciones del repo:** textos, comentarios y commits en español con voseo (la versión en inglés de la página, en inglés). Actualizar `README.md` y `CLAUDE.md` para describir `landing/` y su despliegue.

## Lo que queda a criterio de quien implemente

- Redacción final de los textos (respetando la estructura, el tono del club y los anti-objetivos).
- Distribución visual exacta de cada sección dentro de la dirección A.
- Cómo se reacomoda el diagrama en móvil, mientras siga siendo legible a 360 px.
- Si hace falta algún JS mínimo (por ejemplo, ninguno es lo esperado).
