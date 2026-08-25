# Rol de IAM para GitHub Actions (OIDC)

Estos archivos crean el rol que GitHub Actions asume para publicar el sitio. **No hay llaves de acceso**: GitHub emite un token de identidad de corta vida y AWS lo cambia por credenciales temporales.

| Archivo | Qué es |
|---|---|
| `oidc-trust-policy.json` | Quién puede asumir el rol |
| `deploy-policy.json` | Qué puede hacer el rol una vez asumido |
| `crear-rol.sh` | Rellena las plantillas y aplica todo con la AWS CLI |

Los `.json` son plantillas con marcadores (`ACCOUNT_ID`, `GITHUB_REPO`, `ENTORNO`, `BUCKET`, `DISTRIBUTION_ID`). El script los sustituye; también se pueden rellenar a mano.

---

## Uso

Un rol por entorno:

```bash
cd infra
./crear-rol.sh produccion rockers502-gt-site E1XXXXXXXXXXXX
./crear-rol.sh dev        rockers502-gt-dev  E2YYYYYYYYYYYY
```

El script averigua el ID de cuenta solo, crea el proveedor OIDC si no existe, crea o actualiza el rol, aplica los permisos, e imprime los valores exactos que hay que cargar en el Environment de GitHub.

Es idempotente: se puede volver a ejecutar para corregir la política sin borrar nada.

Si tu repositorio no es `fjbatresv/rocker-mc`, exportá `GITHUB_REPO` antes:

```bash
GITHUB_REPO=usuario/repo ./crear-rol.sh produccion mi-bucket E1XXXX
```

---

## Qué dice la trust policy, y por qué importa

```json
"token.actions.githubusercontent.com:sub": "repo:GITHUB_REPO:environment:ENTORNO"
```

El `sub` está fijado al **environment**, no a la rama. Esa línea es lo que impide que el job de dev asuma el rol de producción: aunque alguien modifique el workflow, el token que GitHub emite para un job de dev lleva `environment:dev` y AWS rechaza la petición contra el rol de producción.

Es también la razón de tener dos roles en vez de uno. Un rol único con acceso a ambos buckets convertiría cualquier descuido en el workflow de dev en un riesgo para el sitio real.

Alternativas más flojas y por qué no:

| Condición `sub` | Problema |
|---|---|
| `repo:usuario/repo:*` | Cualquier rama, cualquier PR de un tercero, puede desplegar a producción |
| `repo:usuario/repo:ref:refs/heads/main` | Mejor, pero dev y producción quedan indistinguibles: un solo rol para ambos |
| `repo:usuario/repo:environment:produccion` | Solo los jobs que declaran ese environment — y ese environment puede exigir aprobación |

La condición `aud` es igual de necesaria: sin ella, un token emitido para otra audiencia podría servir.

---

## Qué permisos concede, y por qué cada uno

| Acción | Para qué la necesita el workflow |
|---|---|
| `s3:ListBucket` | `aws s3 sync` compara el contenido local con el del bucket antes de subir |
| `s3:PutObject` | Subir archivos |
| `s3:DeleteObject` | El `--delete` del sync retira lo que ya no existe en el repositorio |
| `s3:GetObject` | El sync compara, y `aws s3 cp` lee el objeto al corregir su `Content-Type` |
| `s3:GetObjectTagging` / `s3:PutObjectTagging` | Corregir el `Content-Type` es una copia sobre sí mismo; la CLI conserva las etiquetas y sin estos permisos falla con un `AccessDenied` poco obvio |
| `cloudfront:CreateInvalidation` | Purgar la caché del CDN tras publicar |
| `cloudfront:GetInvalidation` | El paso `wait invalidation-completed` la consulta hasta que termina |

Todo está acotado por recurso: el bucket y la distribución **de ese entorno**, nada más. El rol no puede crear buckets, cambiar políticas, tocar otras distribuciones ni leer nada más de la cuenta.

---

## Comprobar que quedó bien

```bash
# Quién puede asumirlo
aws iam get-role --role-name rockers502-deploy-produccion \
  --query 'Role.AssumeRolePolicyDocument' --output json

# Qué puede hacer
aws iam get-role-policy --role-name rockers502-deploy-produccion \
  --policy-name rockers502-deploy-policy --output json
```

La prueba de fuego es lanzar el workflow: si el paso *Asumir el rol de AWS* pasa, la trust policy está bien; si pasan los `s3 sync`, los permisos también.

---

## Si algo falla

| Error | Causa habitual |
|---|---|
| `Not authorized to perform sts:AssumeRoleWithWebIdentity` | El `sub` no coincide: revisá el nombre del repositorio y que el environment del job sea el mismo que dice la trust policy |
| `Credentials could not be loaded` | Falta `permissions: id-token: write` en el workflow |
| `AccessDenied` en `s3 sync` | El bucket del secreto no es el del `Resource` de la política |
| `AccessDenied` al corregir el `Content-Type` | Faltan los permisos de tagging |
| `InvalidClientTokenId` | El proveedor OIDC no existe en la cuenta |
