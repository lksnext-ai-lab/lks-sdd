# Releases técnicas

## Propósito

Una release fija un plugin verificable; no acredita aceptación humana, piloto,
activación de host, instalación personal ni política corporativa.

La versión estable `2.0.2` tiene una aprobación explícita en
`quality/release-approval-v2.0.2.json`. Una aprobación no sustituye el gate técnico
ni transforma canales humanos o de piloto `not-run` en evidencia superada.

## Puerta de publicación

Antes de publicar:

1. Cierre el alcance, actualice versión, changelog y nota de release.
2. Revise el diff e integre el commit exacto en `main`.
3. Desde un checkout limpio y dedicado, ejecute el gate y un único build según
   [VALIDATION.md](VALIDATION.md) y [DISTRIBUTION.md](DISTRIBUTION.md).
4. Revise `release-manifest.json`, valide `SHA256SUMS` y el ZIP Copilot.
5. Cree una etiqueta anotada e inmutable `vX.Y.Z` sobre ese commit.
6. Espere la validación del workflow de la etiqueta y publique los assets
   verificados.

Una release stable exige únicamente aprobación, integridad estática, las catorce
pruebas de humo y la regresión Windows de rutas largas. No exige campañas Docker,
certificaciones activas de perfiles, evals, benchmarks, baseline ni doble build.

## Etiquetado y publicación

Tras tener el manifiesto aprobado y un árbol limpio:

```powershell
$releaseVersion = "2.0.2"
$releaseTag = "v$releaseVersion"
$sourceCommit = (git rev-parse HEAD).Trim()

git tag -a $releaseTag $sourceCommit -m "LKS-SDD $releaseVersion"
git push origin $releaseTag
```

Compruebe que la etiqueta remota apunta al SHA acreditado y cree la release con los
assets enumerados por `release-manifest.json`, `SHA256SUMS` y la nota versionada.
No reutilice etiquetas ni sustituya assets de una versión publicada.

El builder y los workflows no hacen push, no crean releases, no instalan plugins ni
modifican proyectos consumidores. Esas operaciones requieren autorización separada.
