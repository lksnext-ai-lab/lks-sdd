# Releases técnicas

## Propósito

Las releases de GitHub fijan hitos reproducibles del plugin LKS-SDD para Codex. Publicar una release técnica no equivale a aprobar el método como política corporativa, instalar el plugin, habilitar soporte oficial ni decidir su distribución por marketplace.

## Versionado

- El manifiesto `.codex-plugin/plugin.json`, `CHANGELOG.md`, las notas de release y la etiqueta deben usar la misma versión SemVer.
- Un hito funcional compatible incrementa la versión menor; una corrección compatible incrementa el parche; una ruptura de contrato incrementa la versión mayor.
- La versión SemVer del plugin no acredita por sí sola un hito metodológico del mismo número. La nota de release declara por separado qué hitos están implementados, preparados, pendientes o `not-run`.
- Los commits intermedios en `main` no generan ni modifican releases. La release se actualiza creando una versión nueva cuando el cambio está cerrado y validado.
- Las etiquetas `vX.Y.Z` son inmutables. Una versión publicada nunca se mueve ni se reutiliza.
- Las versiones `candidate` se publican como prerelease y pueden tener canales semánticos, humanos o de piloto pendientes si las notas lo declaran. Una versión `stable` exige todos los canales definidos en `quality/catalog.json`.

## Puerta de publicación

Antes de publicar una versión:

1. Cerrar el alcance y actualizar versión, changelog, estado documental y notas en `docs/releases/`.
2. Ejecutar las validaciones de `docs/VALIDATION.md` y revisar el diff completo.
3. Integrar el commit exacto en `main` y comprobar que el árbol de trabajo está limpio.
4. Crear y subir la etiqueta anotada `vX.Y.Z` sobre ese commit.
5. Para M5 o posteriores, generar los bundles desde ese commit, verificar reproducibilidad, manifiesto y checksums, y mantenerlos fuera del árbol Git.
6. Crear la release de GitHub desde la etiqueta, con las notas versionadas y los assets candidate aplicables; verificar URL, commit, estado, hashes y descargas.

Si una validación o la publicación falla, se corrige en una versión nueva o antes de crear la etiqueta; una etiqueta ya publicada no se reescribe.

## Contenido de las notas

Las notas deben distinguir capacidades implementadas, compatibilidad, validaciones, límites y pendientes. Deben indicar expresamente cualquier estado `candidate` y evitar presentar una release técnica como aprobación corporativa.

Cada nota incluye como mínimo:

- versión y fecha;
- enlace o referencia al changelog;
- matriz o declaración de compatibilidad;
- perfiles y locks aplicables;
- resultados de eval y canales que siguen `not-run`;
- vulnerabilidades conocidas y otras limitaciones;
- instrucciones de actualización;
- migración o declaración explícita de que no se requiere;
- rollback;
- periodo o estado de soporte;
- responsables confirmados o, si todavía no existen, el pendiente explícito.

El validador contractual compara dinámicamente la versión del manifiesto con la primera entrada del changelog y `docs/releases/vX.Y.Z.md`. La etiqueta se comprueba únicamente al publicar, porque los commits intermedios no constituyen una release.
