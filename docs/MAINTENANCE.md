# Mantenimiento del repositorio

## Fuentes y salidas

Versionar código, contratos, skills, plantillas, fixtures, locks, certificaciones,
planes aprobados y evidencia saneada. Conservar notas históricas y contraejemplos
cuando explican una decisión o una regresión; su antigüedad no los hace temporales.
La investigación de contexto queda fuera del runtime instalado, no se elimina
para reducir artificialmente la evidencia disponible.

No versionar dependencias instaladas, bytecode, cachés, builds locales, resultados
de navegador o directorios temporales. `.gitignore` protege estas salidas; cada
subproyecto declara las suyas. Antes de retirar una ruta, comprobar que no contiene
fuentes versionadas, personalizaciones ni evidencia única. Usar rutas resueltas y
una copia recuperable cuando no sea necesario destruir los datos.

## Limpieza para 2.0.0

Se retiraron del checkout 48 rutas ignoradas: builds `dist`, cachés de Python,
linters, Next/Vinext/Wrangler y npm, entornos `.venv`, `node_modules`, resultados
de navegador, metadatos de compilación y temporales del estudio de contexto.
Se trasladaron a un respaldo local externo conservando su ruta relativa. No se
publica ese respaldo ni sus rutas personales. No se tocaron instalaciones activas,
otros consumidores, worktrees históricos ni fuentes de `specs/canonical/`.

Los informes de `tests/reports/` que respaldan resultados históricos se conservan
localmente, ignorados y fuera de los paquetes. Los JSON saneados de
`docs/validation/` conservan observaciones finales y fallos que justifican las
correcciones; no deben confundirse con el `quality-report.json` de una release.

## Preparar una release

Revisar todas las ramas y worktrees antes de integrar; una rama de distribución
generada no se mezcla con fuentes de mantenimiento. Cada release nueva exige
aprobación propia, checkout limpio, validación y doble build exactos. Seguir
[VALIDATION](VALIDATION.md), [RELEASING](RELEASING.md) y
[DISTRIBUTION](DISTRIBUTION.md). No generar reportes dentro del checkout dedicado.
La limpieza de temporales no autoriza mover tags ni sustituir assets publicados.
