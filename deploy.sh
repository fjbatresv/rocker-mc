#!/usr/bin/env bash
#
# Despliegue de rockers502.gt a S3 + CloudFront.
#
#   ./deploy.sh
#
# Requiere: AWS CLI v2 configurado con un perfil que tenga permisos sobre el
# bucket y la distribución. Configurá las tres variables de abajo (o exportalas
# en el entorno antes de ejecutar).
#
set -euo pipefail

BUCKET="${ROCKERS_BUCKET:-rockers502-gt-site}"
DISTRIBUTION_ID="${ROCKERS_DISTRIBUTION_ID:-E000000000000}"
PROFILE="${AWS_PROFILE:-default}"
SRC="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/site"

aws() { command aws --profile "$PROFILE" "$@"; }

echo "==> Origen: $SRC"
echo "==> Bucket: s3://$BUCKET"

# --- 1. Recursos con hash implícito: caché larga -----------------------------
# Imágenes, CSS y JS se cachean un año. Cuando cambien, la invalidación del
# paso 3 se encarga; si el sitio creciera, conviene versionar los nombres.
echo "==> Subiendo assets (caché larga)"
aws s3 sync "$SRC/assets" "s3://$BUCKET/assets" \
  --delete \
  --cache-control "public, max-age=31536000, immutable"

# --- 2. HTML y metadatos: sin caché en el navegador --------------------------
# CloudFront sí los cachea; el navegador siempre revalida.
echo "==> Subiendo HTML y metadatos (sin caché)"
aws s3 sync "$SRC" "s3://$BUCKET" \
  --delete \
  --exclude "assets/*" \
  --cache-control "public, max-age=0, must-revalidate"

# Content-Type explícito para los que S3 suele adivinar mal
aws s3 cp "s3://$BUCKET/sitemap.xml" "s3://$BUCKET/sitemap.xml" \
  --content-type "application/xml" \
  --cache-control "public, max-age=3600" \
  --metadata-directive REPLACE

aws s3 cp "s3://$BUCKET/robots.txt" "s3://$BUCKET/robots.txt" \
  --content-type "text/plain; charset=utf-8" \
  --cache-control "public, max-age=3600" \
  --metadata-directive REPLACE

# --- 3. Invalidación ---------------------------------------------------------
echo "==> Invalidando CloudFront"
INVALIDATION_ID=$(aws cloudfront create-invalidation \
  --distribution-id "$DISTRIBUTION_ID" \
  --paths "/*" \
  --query 'Invalidation.Id' \
  --output text)

echo "==> Invalidación $INVALIDATION_ID en curso"
aws cloudfront wait invalidation-completed \
  --distribution-id "$DISTRIBUTION_ID" \
  --id "$INVALIDATION_ID"

echo "==> Listo: https://www.rockers502.gt/"
