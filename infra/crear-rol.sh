#!/usr/bin/env bash
#
# Crea (o actualiza) el rol de IAM que GitHub Actions asume por OIDC para
# publicar el sitio en un entorno.
#
#   ./crear-rol.sh produccion rockers502-gt-site E1XXXXXXXXXXXX
#   ./crear-rol.sh dev        rockers502-gt-dev  E2YYYYYYYYYYYY
#
# El nombre del entorno debe coincidir con el Environment de GitHub, porque la
# trust policy lo fija en la condición `sub`. Es lo que impide que el job de dev
# asuma el rol de producción.
#
# Requiere AWS CLI v2 con permisos de IAM. Es idempotente: se puede volver a
# ejecutar para corregir la política sin borrar el rol.
#
set -euo pipefail

GITHUB_REPO="${GITHUB_REPO:-fjbatresv/rocker-mc}"
AQUI="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if [ $# -ne 3 ]; then
  echo "Uso: $0 <entorno> <bucket> <distribution-id>" >&2
  echo "Ejemplo: $0 produccion rockers502-gt-site E1XXXXXXXXXXXX" >&2
  exit 1
fi

ENTORNO="$1"
BUCKET="$2"
DISTRIBUTION_ID="$3"
ROL="rockers502-deploy-${ENTORNO}"

ACCOUNT_ID="$(aws sts get-caller-identity --query Account --output text)"

echo "==> Cuenta:       $ACCOUNT_ID"
echo "==> Repositorio:  $GITHUB_REPO"
echo "==> Entorno:      $ENTORNO"
echo "==> Rol:          $ROL"
echo "==> Bucket:       $BUCKET"
echo "==> Distribución: $DISTRIBUTION_ID"
echo

TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

rellenar() {
  sed -e "s|ACCOUNT_ID|${ACCOUNT_ID}|g" \
      -e "s|GITHUB_REPO|${GITHUB_REPO}|g" \
      -e "s|ENTORNO|${ENTORNO}|g" \
      -e "s|DISTRIBUTION_ID|${DISTRIBUTION_ID}|g" \
      -e "s|BUCKET|${BUCKET}|g" \
      "$1"
}

rellenar "$AQUI/oidc-trust-policy.json" > "$TMP/trust.json"
rellenar "$AQUI/deploy-policy.json"     > "$TMP/permisos.json"

# --- Proveedor OIDC: una sola vez por cuenta ---------------------------------
PROVEEDOR="arn:aws:iam::${ACCOUNT_ID}:oidc-provider/token.actions.githubusercontent.com"
if aws iam get-open-id-connect-provider --open-id-connect-provider-arn "$PROVEEDOR" >/dev/null 2>&1; then
  echo "==> Proveedor OIDC de GitHub: ya existe"
else
  echo "==> Creando el proveedor OIDC de GitHub"
  aws iam create-open-id-connect-provider \
    --url https://token.actions.githubusercontent.com \
    --client-id-list sts.amazonaws.com \
    --thumbprint-list 6938fd4d98bab03faadb97b34396831e3780aea1 >/dev/null
fi

# --- Rol ---------------------------------------------------------------------
if aws iam get-role --role-name "$ROL" >/dev/null 2>&1; then
  echo "==> El rol existe: actualizando su trust policy"
  aws iam update-assume-role-policy \
    --role-name "$ROL" \
    --policy-document "file://$TMP/trust.json"
else
  echo "==> Creando el rol"
  aws iam create-role \
    --role-name "$ROL" \
    --description "Despliegue del sitio de Rockers 502 MG (entorno ${ENTORNO})" \
    --max-session-duration 3600 \
    --assume-role-policy-document "file://$TMP/trust.json" >/dev/null
fi

echo "==> Aplicando los permisos"
aws iam put-role-policy \
  --role-name "$ROL" \
  --policy-name "rockers502-deploy-policy" \
  --policy-document "file://$TMP/permisos.json"

ROL_ARN="arn:aws:iam::${ACCOUNT_ID}:role/${ROL}"

cat <<RESUMEN

Listo.

Cargá esto en GitHub → Settings → Environments → ${ENTORNO}

  Secreto  AWS_ROLE_ARN                      ${ROL_ARN}
  Secreto  AWS_S3_BUCKET                     ${BUCKET}
  Secreto  AWS_CLOUDFRONT_DISTRIBUTION_ID    ${DISTRIBUTION_ID}
  Variable AWS_REGION                        us-east-1
  Variable SITE_URL                          https://…

RESUMEN
