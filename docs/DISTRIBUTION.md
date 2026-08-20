# Distribución candidate M5

## Bundle de desarrollo

`scripts/build_candidate_package.py` genera fuera del repositorio dos ZIP reproducibles:

- `lks-sdd-plugin-vX.Y.Z.zip`, con el plugin bajo `lks-sdd/`;
- `lks-sdd-marketplace-vX.Y.Z.zip`, con `.agents/plugins/marketplace.json` y `plugins/lks-sdd/`.

`X.Y.Z` se deriva del manifiesto del plugin; el builder no mantiene una segunda versión hardcodeada.

La entrada del marketplace usa la forma estándar `local`, ruta `./plugins/lks-sdd`, instalación `AVAILABLE`, autenticación `ON_INSTALL` y categoría `Productivity`. El builder añade un manifiesto por archivo y `SHA256SUMS`, rechaza enlaces, salidas dentro del repositorio y patrones de secretos conocidos.

```powershell
python scripts\build_candidate_package.py --date 2026-08-20 --source-commit COMMIT_COMPLETO --output C:\ruta\externa\lks-sdd-v0.6.0
```

La carpeta de salida debe no existir y `--source-commit` debe identificar el commit exacto de 40 caracteres. Una segunda compilación desde el mismo commit y fecha debe producir los mismos hashes.

## Instalación controlada

1. Extraer el ZIP de marketplace en una carpeta temporal controlada.
2. Verificar `SHA256SUMS` y el manifiesto antes de configurar Codex.
3. Añadir esa raíz como marketplace local no predeterminado con el flujo soportado por la versión de Codex utilizada.
4. Instalar `lks-sdd@lks-sdd-development` y abrir una tarea nueva para cargar la versión.
5. Registrar únicamente alias, versión, checksum y resultado; no contenido del proyecto.

La instalación no se automatiza desde este repositorio porque modifica el entorno Codex del participante. Debe estar autorizada y asociada al proyecto del piloto.

## Retirada

Siga `pilot/ROLLBACK.md`. Retirar el plugin no autoriza a revertir automáticamente documentación o código consumidor, borrar evidencia ni mover etiquetas Git.
