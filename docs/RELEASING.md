# Releases técnicas

## Propósito

Una release fija un plugin verificable; no acredita aceptación humana, piloto,
activación de host, instalación personal ni política corporativa.

La versión estable `2.1.3` tiene una aprobación explícita en
`quality/release-approval-v2.1.3.json`. Una aprobación no sustituye el gate técnico
ni transforma canales humanos o de piloto `not-run` en evidencia superada.

## Puerta de publicación

Antes de publicar:

1. Cierre el alcance y actualice la versión y su sección `## X.Y.Z` en el changelog.
2. Revise el diff e integre el commit exacto en `main`.
3. Desde `main`, ejecute manualmente el job `stable-preflight` del workflow
   `quality`.
4. Revise su artefacto de evidencia: preflight, gate, manifiesto, checksums y ZIP
   Copilot.
5. Cree una etiqueta anotada e inmutable `vX.Y.Z` sobre ese commit.
6. Espere la validación de etiqueta. Si acredita el `stable-preflight` del mismo
   SHA, reutilizará su evidencia; si no existe, repetirá gate y build de forma
   visible.
7. Espere la aprobación protegida que crea la draft release con sus assets
   verificados.
8. Revise la draft y publíquela explícitamente cuando corresponda.

Una release stable exige únicamente aprobación, integridad estática, las catorce
pruebas de humo y la regresión Windows de rutas largas. No exige campañas Docker, catálogos tecnológicos, evals, benchmarks, baseline ni doble build.

## Etiquetado y publicación

Tras tener el manifiesto aprobado y un árbol limpio:

```powershell
$releaseVersion = "2.1.3"
$releaseTag = "v$releaseVersion"
$sourceCommit = (git rev-parse HEAD).Trim()

git tag -a $releaseTag $sourceCommit -m "LKS-SDD $releaseVersion"
git push origin $releaseTag
```

La etiqueta `vX.Y.Z` es la única referencia de release: activa el workflow técnico
y es la referencia del catálogo Copilot. No cree una segunda etiqueta específica
para Copilot.

Compruebe que la etiqueta remota apunta al SHA acreditado. La promoción protegida crea
la draft con los assets enumerados por `release-manifest.json`, `SHA256SUMS` y la nota
versionada. No reutilice etiquetas ni sustituya assets de una versión publicada.

El builder, el preflight y el workflow técnico de etiqueta no hacen push, no crean
releases, no instalan plugins ni modifican proyectos consumidores. La promoción
protegida es la única excepción: crea una draft tras aprobación humana. Publicar,
instalar o modificar proyectos consumidores requiere autorización separada.

## Draft release protegida

Tras una validación correcta de `quality` sobre una etiqueta stable `vX.Y.Z`, el
workflow `release-draft` verifica el artefacto `release-evidence` de ese run exacto.
Este puede provenir de un preflight reutilizado o de una revalidación completa, pero
en ambos casos acredita el mismo gate, SHA, manifiesto, checksums, ZIP Copilot,
sección acreditada del changelog y referencia Copilot antes de quedar pendiente de aprobación en el entorno
`release-draft`.

Un administrador debe configurar previamente ese entorno con revisores requeridos y,
cuando la política lo permita, sin autoaprobación. El workflow solo crea una **draft**
después de esa aprobación y adjunta todos los assets acreditados por el manifiesto,
junto con `release-manifest.json` y `SHA256SUMS`. No publica la release.

Si existe ya una release o draft para la etiqueta, el workflow se bloquea y requiere
reconciliación manual; nunca sustituye assets ni vuelve a publicar. Después de revisar
la draft, una persona autorizada usa GitHub para pulsar **Publish release**.

## Preflight de release

El camino normal es abrir **Actions → quality → Run workflow** sobre `main`. El job
manual `stable-preflight` usa un checkout limpio del SHA seleccionado y, sin recibir
versiones, SHA ni etiquetas como inputs:

1. ejecuta el preflight de solo lectura;
2. ejecuta el gate estable completo, en paralelo para sus checks técnicos
   independientes;
3. genera una vez todos los paquetes de distribución y valida los paquetes Copilot,
   plugin y marketplace;
4. conserva `stable-preflight-evidence` durante 30 días.

La evidencia incluye `release-readiness.json`, `release-gate.json`, el manifiesto,
`SHA256SUMS`, los paquetes de distribución, la validación de paquetes y la
procedencia del run manual. Revise que readiness y gate estén en estado superado antes
de crear `vX.Y.Z`.

El job no crea etiquetas, releases ni assets públicos. La validación de etiqueta
solo evita repetir gate y build si puede enlazar ese artefacto al mismo SHA, rama y
ejecución manual. Una evidencia ausente provoca una revalidación completa; una
evidencia encontrada pero inconsistente bloquea el flujo. El comando local sigue
disponible solo para diagnosticar un bloqueo concreto:

```powershell
$releaseReadiness = Join-Path $env:TEMP 'lks-sdd-release-readiness.json'
python -B -X utf8 scripts\release_readiness.py `
  --channel stable `
  --output $releaseReadiness
```

## Observabilidad de release

Después de una ejecución correcta del workflow `quality` sobre una etiqueta `v*`,
el workflow separado `release-observability` registra el tiempo observado de cola,
dependencias, carga de evidencia y ruta de validación. En una revalidación mide gate
y empaquetado; en una reutilización mide resolución y verificación de procedencia y
declara el gate/build del tag como `not-run`. El informe no forma parte del gate
técnico: medir no convierte una release en aprobada ni sustituye sus checksums,
manifiesto o revisión humana.

La caché pip de CI solo conserva descargas de las dependencias declaradas por
`requirements-runtime.txt`; `pip install --require-hashes` sigue validando los
artefactos instalados. No se cachean candidates, ZIPs, evidencia ni decisiones de
release.

El mismo observador lee el `marketplace.json` del commit etiquetado y comprueba que
su referencia GitHub configurada resuelve exactamente al SHA de la release. No crea,
mueve ni selecciona etiquetas; si la referencia está ausente, es ambigua o apunta a
otro commit, publica un diagnóstico y falla de forma visible.

Los dos informes se conservan como el artefacto `release-observability-<run-id>`.
La revisión humana continúa como `not-observed` porque este observador no mide la
aprobación de entorno, la revisión de la draft ni la decisión de publicación. No debe
presentarse como superada.

Para investigar localmente una referencia configurada, sin modificar el repositorio:

```powershell
$sourceCommit = (git rev-parse HEAD).Trim()
python -B -X utf8 scripts\validate_distribution_reference.py `
  --source-commit $sourceCommit
```
