#!/usr/bin/env bash
set -euo pipefail

if [ "$#" -ne 1 ] || [ -z "$1" ]; then
  echo "Uso: $0 <distribution-id>" >&2
  exit 2
fi
command -v aws >/dev/null || { echo 'Requiere AWS CLI v2.' >&2; exit 1; }
command -v jq >/dev/null || { echo 'Requiere jq.' >&2; exit 1; }
aws --version | grep -q '^aws-cli/2\.' || { echo 'Requiere AWS CLI v2.' >&2; exit 1; }

distribution=$1
nombre=rockers502-cabeceras-seguridad
config="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/cabeceras-seguridad.json"
tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT

politica=$(aws cloudfront list-response-headers-policies --type custom | jq -c --arg nombre "$nombre" '.ResponseHeadersPolicyList.Items[]? | select(.ResponseHeadersPolicy.ResponseHeadersPolicyConfig.Name == $nombre) | {id: .ResponseHeadersPolicy.Id, etag: .ETag}')
if [ -z "$politica" ]; then
  policy_id=$(aws cloudfront create-response-headers-policy --response-headers-policy-config "file://$config" --query 'ResponseHeadersPolicy.Id' --output text)
else
  policy_id=$(jq -r '.id' <<<"$politica")
  etag=$(jq -r '.etag' <<<"$politica")
  aws cloudfront update-response-headers-policy --id "$policy_id" --if-match "$etag" --response-headers-policy-config "file://$config" >/dev/null
fi

aws cloudfront get-distribution-config --id "$distribution" > "$tmp/distribution.json"
etag=$(jq -r '.ETag' "$tmp/distribution.json")
if [ "$(jq -r '.DistributionConfig.DefaultCacheBehavior.ResponseHeadersPolicyId // empty' "$tmp/distribution.json")" = "$policy_id" ]; then
  echo 'La política de cabeceras ya está asociada.'
  exit 0
fi
jq --arg id "$policy_id" '.DistributionConfig | .DefaultCacheBehavior.ResponseHeadersPolicyId = $id' "$tmp/distribution.json" > "$tmp/config.json"
aws cloudfront update-distribution --id "$distribution" --if-match "$etag" --distribution-config "file://$tmp/config.json" >/dev/null
echo "Política asociada. Verificá con: curl -sI https://rockers502mc.com.gt/"
