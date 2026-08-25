# Rockers 502 MG Guatemala — sitio institucional

Sitio estático de una sola página. Sin framework, sin backend y sin paso de compilación obligatorio: HTML, un CSS y un JavaScript de unas 150 líneas. Vive en un bucket de S3 detrás de CloudFront, con dos entornos: un push a `main` publica en dev, y producción se lanza a mano.

---

## Verlo en local

El sitio son archivos planos, así que cualquier servidor estático sirve. Desde la raíz del repositorio:

```bash
cd site
python3 -m http.server 8080
```

Abrí <http://localhost:8080>. Para detenerlo, `Ctrl+C`.

Otras opciones equivalentes, por si preferís:

```bash
npx serve site          # Node
php -S localhost:8080 -t site
```

> Abrir `site/index.html` con doble clic también funciona, pero el navegador lo carga con el protocolo `file://` y algunas rutas se comportan distinto. Para revisar el resultado final, usá siempre un servidor.

**Qué revisar en cada cambio:** el menú en escritorio y en móvil, el carrusel con flechas y arrastre, y que el pie de página cierre bien. La ventana de móvil se simula con las herramientas de desarrollador (`Cmd+Opt+I` → ícono de dispositivo).

---

## Estructura

```
.
├── site/                        ← lo único que se sube al bucket
│   ├── index.html
│   ├── 404.html
│   ├── favicon.ico
│   ├── robots.txt
│   ├── sitemap.xml
│   └── assets/
│       ├── css/styles.css
│       ├── js/main.js
│       └── img/
│           ├── emblem.webp          escudo (680 px)
│           ├── emblem@2x.webp       escudo grande de la sección de simbología
│           ├── hero.webp            fondo del hero, blanco y negro
│           ├── og.jpg               vista previa al compartir (1200×630)
│           ├── favicon-512.png
│           ├── apple-touch-icon.png
│           ├── rodadas/             ocho fotos del carrusel
│           └── maquinas/            cinco fotos del mosaico de estilos
├── .github/
│   ├── workflows/deploy.yml     ← orquesta: dev automático, prod a mano
│   ├── workflows/publicar.yml   ← workflow reutilizable, uno por entorno
│   └── scripts/verificar_enlaces.py
├── infra/                       ← rol de IAM para el despliegue (OIDC)
│   ├── oidc-trust-policy.json
│   ├── deploy-policy.json
│   └── crear-rol.sh
├── Assets/logo.jpeg             ← arte original del emblema, fuente de verdad
├── make_emblem.py               ← único script: regenera el emblema y sus derivados
└── deploy.sh                    ← despliegue manual, como respaldo
```

---

## Editar el contenido

**No hay build.** `site/index.html` es el original, no un archivo generado: se edita a mano y lo que se ve en el editor es exactamente lo que se publica.

**Textos, enlaces, secciones:** editá `site/index.html` directamente. Es HTML plano, sin plantillas ni variables.

**Fotos del carrusel:** reemplazá los archivos de `site/assets/img/rodadas/`. Conviene mantener proporción 3:2 y exportar a WebP con calidad 75–80, por debajo de 150 KB cada una. Los pies de foto y el texto `alt` están en `site/index.html`.

**Sección "Los estilos que rodamos":** es un mosaico de cinco fotos de motos del club seguido de una retícula con los ocho nombres de estilo. Las fotos son ilustrativas del conjunto, no una por estilo: no intentan mostrar un ejemplar de cada categoría.

Para cambiar las fotos, reemplazá los archivos de `site/assets/img/maquinas/`. La primera (`moto-1.webp`) es la grande del mosaico y conviene que sea la más limpia; las otras cuatro son cuadradas. Exportá a WebP con calidad 75–80. Para cambiar los nombres, editá la lista `<ul class="style-names">` en `site/index.html`.

**Emblema, favicons e imagen de Open Graph:** los seis archivos derivados salen de `Assets/logo.jpeg`, el arte original del club sobre fondo negro. Es lo único que no conviene rehacer a mano. Si algún día cambia el logo, reemplazá ese archivo y ejecutá:

```bash
python3 make_emblem.py          # requiere Pillow, numpy y scipy
```

Regenera `emblem.webp`, `emblem@2x.webp`, `favicon-512.png`, `apple-touch-icon.png`, `favicon.ico` y `og.jpg`.

El script separa el fondo con un relleno por inundación desde los bordes en lugar de recortar con un círculo. Esto importa: **las bandas de ROCKERS y GUATEMALA sobresalen del aro**, así que cualquier máscara circular las corta por arriba y por abajo. La inundación sigue la silueta real y respeta el negro del interior del emblema, que al no tocar el borde nunca se marca como fondo. El resultado se centra en un lienzo cuadrado para que los `width`/`height` del HTML sigan siendo válidos.

---

## Despliegue

### Dos entornos

| | dev | producción |
|---|---|---|
| Se dispara | automático, en cada push a `main` que toque `site/**` | a mano: **Actions → Desplegar → Run workflow** |
| Buscadores | bloqueado (`robots.txt` con `Disallow: /`, sin sitemap) | indexable |
| Para qué | ver el sitio real antes de exponerlo | el sitio del club |

Un merge a `main` publica en dev y ahí se queda. Producción se lanza cuando alguien decide lanzarlo, eligiendo `produccion` en el desplegable. También se puede relanzar dev a mano desde el mismo menú.

Ambos pasan primero por el job `verificar`, que comprueba que los cuatro archivos críticos existan y que ninguna referencia local del HTML apunte a un archivo inexistente.

```
push a main ──→ verificar ──→ dev
Run workflow ──→ verificar ──→ dev  o  producción  (según se elija)
```

### Por qué dos archivos de workflow

`deploy.yml` decide *cuándo* y *dónde*; `publicar.yml` es un workflow reutilizable con la secuencia de publicación, y se invoca una vez por entorno. La alternativa —copiar los mismos ocho pasos dos veces— garantiza que tarde o temprano se arreglen en uno y no en el otro.

**Nada específico de un entorno vive en el código.** La región, la URL, el bucket, el rol y la distribución salen del Environment de GitHub. Cambiar de cuenta de AWS o de región no toca el repositorio.

### Configurar los Environments

En **Settings → Environments**, creá dos: `dev` y `produccion`. En cada uno:

**Variables** (`Environment variables`, visibles en los logs):

| Variable | Ejemplo dev | Ejemplo producción |
|---|---|---|
| `AWS_REGION` | `us-east-1` | `us-east-1` |
| `SITE_URL` | `https://dev.rockers502.gt/` | `https://www.rockers502.gt/` |

**Secretos** (`Environment secrets`, ocultos en los logs):

| Secreto | Qué es |
|---|---|
| `AWS_ROLE_ARN` | Rol que asume el workflow en ese entorno |
| `AWS_S3_BUCKET` | Bucket de ese entorno |
| `AWS_CLOUDFRONT_DISTRIBUTION_ID` | Distribución de ese entorno |

> Los tres son **identificadores**, no credenciales — no hay ninguna llave de acceso guardada en GitHub. Aun así van como secretos: publicar el ARN de un rol y el nombre del bucket le ahorra trabajo de reconocimiento a quien quiera intentar algo.

Si a un entorno le falta cualquiera de los cinco, el workflow falla en el primer paso con un mensaje que dice exactamente cuál, en vez de reventar más adelante con un error de la AWS CLI.

**Protección recomendada para `produccion`:** en **Settings → Environments → produccion**, activá *Required reviewers* con uno o dos miembros. Con eso, aunque alguien lance el workflow, la publicación queda esperando aprobación.

### Infraestructura, por cada entorno

Lo que sigue hay que hacerlo dos veces —una por entorno—, cambiando el nombre del bucket y el subdominio. Si preferís empezar con uno solo, montá producción y dejá el Environment `dev` sin configurar: el job de dev fallará con un mensaje claro y producción seguirá funcionando a mano.

#### 1. Bucket privado

```bash
aws s3 mb s3://rockers502-gt-site --region us-east-1        # producción
aws s3 mb s3://rockers502-gt-dev  --region us-east-1        # dev
aws s3api put-public-access-block \
  --bucket rockers502-gt-site \
  --public-access-block-configuration \
    "BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true"
```

Sin *static website hosting*: CloudFront habla con el bucket por su endpoint REST.

#### 2. Certificado TLS

Debe estar en **`us-east-1`**, sin importar dónde esté el bucket. Es el tropiezo más común al montar esto por primera vez. Un solo certificado puede cubrir los tres nombres:

```bash
aws acm request-certificate \
  --region us-east-1 \
  --domain-name rockers502.gt \
  --subject-alternative-names www.rockers502.gt dev.rockers502.gt \
  --validation-method DNS
```

Validá creando los CNAME que devuelve ACM.

#### 3. Distribución de CloudFront

| Ajuste | Valor |
|--------|-------|
| Origen | El bucket S3 con **Origin Access Control** (no OAI, que está en desuso) |
| Viewer protocol policy | `Redirect HTTP to HTTPS` |
| Default root object | `index.html` |
| Compress objects automatically | Sí (Brotli y gzip) |
| Cache policy | `CachingOptimized` administrada |
| Alternate domain names | producción: `rockers502.gt`, `www.rockers502.gt` · dev: `dev.rockers502.gt` |
| Custom error response | `403` → `/404.html` con código de respuesta `404` |

> El **403 → 404.html no es opcional.** Un bucket privado responde `403 AccessDenied` —no `404`— cuando la llave no existe. Sin esa regla, quien escriba mal una URL vería un error crudo de AWS en vez de la página del club.

Al terminar, CloudFront ofrece copiar la política del bucket:

```json
{
  "Version": "2008-10-17",
  "Statement": [{
    "Sid": "AllowCloudFrontServicePrincipal",
    "Effect": "Allow",
    "Principal": { "Service": "cloudfront.amazonaws.com" },
    "Action": "s3:GetObject",
    "Resource": "arn:aws:s3:::rockers502-gt-site/*",
    "Condition": {
      "StringEquals": {
        "AWS:SourceArn": "arn:aws:cloudfront::<ACCOUNT_ID>:distribution/<DISTRIBUTION_ID>"
      }
    }
  }]
}
```

#### 4. DNS

En Route 53, registros **A de tipo alias** hacia cada distribución: el dominio raíz y `www` a producción, `dev` a la de desarrollo. El raíz no admite CNAME.

#### 5. Conectar GitHub con AWS (OIDC)

Las políticas de IAM están en [`infra/`](infra/), con su propio README. Un rol por entorno:

```bash
cd infra
./crear-rol.sh produccion rockers502-gt-site E1XXXXXXXXXXXX
./crear-rol.sh dev        rockers502-gt-dev  E2YYYYYYYYYYYY
```

El script crea el proveedor OIDC si no existe, crea o actualiza el rol, aplica los permisos mínimos e imprime los valores exactos para cargar en el Environment de GitHub. Es idempotente.

La condición clave de la trust policy fija el `sub` al **environment**, no a la rama:

```
repo:fjbatresv/rocker-mc:environment:produccion
```

Eso es lo que impide que el job de dev asuma el rol de producción. En [`infra/README.md`](infra/README.md) está el detalle de por qué cada permiso es necesario y qué hacer si algo falla.

### Despliegue manual

`deploy.sh` hace lo mismo desde una terminal, por si Actions no está disponible:

```bash
export ROCKERS_BUCKET=rockers502-gt-site
export ROCKERS_DISTRIBUTION_ID=E1XXXXXXXXXXXX
./deploy.sh
```

---

## Política de caché

| Tipo | `Cache-Control` | Razón |
|------|-----------------|-------|
| `assets/**` (imágenes, CSS, JS) | `public, max-age=31536000, immutable` | Cambian poco; la invalidación del deploy los refresca |
| `*.html` | `public, max-age=0, must-revalidate` | El contenido institucional debe poder corregirse el mismo día |
| `robots.txt`, `sitemap.xml` | `public, max-age=3600` | Punto medio razonable |

Las primeras 1&nbsp;000 invalidaciones mensuales son gratuitas; con la frecuencia de cambio esperada eso nunca genera costo. Si el sitio empezara a actualizarse a diario, conviene versionar los nombres de archivo (`styles.a1b2c3.css`) y quitar la invalidación total.

---

## Costo estimado

| Concepto | Mensual |
|----------|---------|
| S3 (almacenamiento, ~2 MB) | menos de US$0.01 |
| CloudFront (dentro de la capa gratuita con el tráfico esperado) | US$0 |
| Route 53 (zona alojada) | US$0.50 |
| ACM | US$0 |
| GitHub Actions (repositorio público, o minutos gratuitos del plan) | US$0 |
| **Total** | **≈ US$0.50/mes** más el dominio anual |

El entorno de dev agrega un bucket y una distribución más, ambos con tráfico casi nulo: en la práctica no mueve la aguja.

---

## Rendimiento y accesibilidad

Objetivos que el sitio cumple y conviene verificar tras el despliegue:

- Lighthouse ≥ 95 en Performance, Accessibility, Best Practices y SEO.
- El contenido completo es visible sin JavaScript; solo se pierden las animaciones de entrada y las flechas del carrusel, que sigue funcionando por arrastre.
- Navegación completa por teclado, con *skip link* y foco visible.
- Contraste WCAG AA en todo el texto. El rojo `#C1121F` no se usa en párrafos: solo en titulares, bordes, íconos y fondos de botón.
- `prefers-reduced-motion` desactiva todas las animaciones.

---

## Pendientes antes de salir a producción

1. **Confirmar el dominio.** Todo apunta a `rockers502.gt`; si se elige otro, hay que actualizar `canonical`, Open Graph, `sitemap.xml`, `robots.txt` y el JSON-LD de `index.html`.
2. **Validar los ocho estilos de moto** y sus descripciones con la mesa directiva. El requisito publicado en 2021 nombra solo cuatro; el sitio ya lo redacta ampliado.
3. **Pies de foto del carrusel.** Hoy son descriptivos genéricos; reemplazarlos por lugar y fecha reales.
4. **Derechos de imagen.** Hay caras reconocibles en las fotos de rodadas. Conviene el visto bueno de quienes aparecen.
5. **Correo del club.** El sitio hoy solo enlaza a redes; un `contacto@` daría una vía formal para terceros.
