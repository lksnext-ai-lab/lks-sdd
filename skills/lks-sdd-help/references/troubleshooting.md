# Troubleshooting

## La skill no se activa

Describa el objetivo o invoque de forma explícita la skill correspondiente: `$lks-sdd-help`, `$lks-sdd-define`, `$lks-sdd-adopt-existing`, `$lks-sdd-assess-readiness`, `$lks-sdd-implement` o `$lks-sdd-verify`. Compruebe que el plugin está disponible en Codex. La activación implícita ayuda, pero no es una garantía contractual.

## No se encuentra el proyecto

Confirme la raíz. Un proyecto ChatGPT no concede acceso directo a una carpeta; un proyecto local, CLI o IDE puede usar una raíz distinta. No inicialice hasta descartar que exista una aplicación previa.

## El índice es inválido

Ejecute la validación en modo de lectura y revise cada error. No reconstruya decisiones desde el índice ni sustituya Markdown humanos. Una corrección requiere una petición operativa separada.

## Readiness está bloqueado

Lea el alcance del bloqueo y el cambio mínimo indicado. Confirme que requisito, aceptación, decisión, incremento y prueba están enlazados. Un bloqueo de otro incremento no debe paralizar el evaluado.

## Se detecta una aplicación existente

Detenga la ruta `new` y continúe con `lks-sdd-adopt-existing`. El primer inventario debe ser estático y de solo lectura; no materialice hasta confirmar alcance, cobertura, reconciliación, baseline vigente y preview.

## Falta una capacidad de Work o Codex

Revise [realidad del producto](product-reality.md), permisos y configuración. Declare la limitación y use un fallback conservador: fuentes adjuntas, Markdown exportados o una raíz local confirmada. No atribuya el problema a la persona usuaria.
