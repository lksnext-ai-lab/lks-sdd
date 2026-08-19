# Releases técnicas

## Propósito

Las releases de GitHub fijan hitos reproducibles del plugin LKS-SDD para Codex. Publicar una release técnica no equivale a aprobar el método como política corporativa, instalar el plugin, habilitar soporte oficial ni decidir su distribución por marketplace.

## Versionado

- El manifiesto `.codex-plugin/plugin.json`, `CHANGELOG.md`, las notas de release y la etiqueta deben usar la misma versión SemVer.
- Un hito funcional compatible incrementa la versión menor; una corrección compatible incrementa el parche; una ruptura de contrato incrementa la versión mayor.
- Los commits intermedios en `main` no generan ni modifican releases. La release se actualiza creando una versión nueva cuando el cambio está cerrado y validado.
- Las etiquetas `vX.Y.Z` son inmutables. Una versión publicada nunca se mueve ni se reutiliza.

## Puerta de publicación

Antes de publicar una versión:

1. Cerrar el alcance y actualizar versión, changelog, estado documental y notas en `docs/releases/`.
2. Ejecutar las validaciones de `docs/VALIDATION.md` y revisar el diff completo.
3. Integrar el commit exacto en `main` y comprobar que el árbol de trabajo está limpio.
4. Crear y subir la etiqueta anotada `vX.Y.Z` sobre ese commit.
5. Crear la release de GitHub desde la etiqueta, con las notas versionadas, y verificar URL, commit, estado y artefactos fuente.

Si una validación o la publicación falla, se corrige en una versión nueva o antes de crear la etiqueta; una etiqueta ya publicada no se reescribe.

## Contenido de las notas

Las notas deben distinguir capacidades implementadas, compatibilidad, validaciones, límites y pendientes. Deben indicar expresamente cualquier estado `candidate` y evitar presentar una release técnica como aprobación corporativa.
