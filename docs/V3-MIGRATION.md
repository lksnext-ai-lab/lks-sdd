# Migración explícita de v2 a v3

Instalar el plugin 3.0 no modifica proyectos. La ruta contempla schema 2.0 con
métodos 2.0.0 y 2.1.0, con formato válido y runtime identificable. Un origen desconocido
se conserva y diagnostica. Un proyecto 1.5 utiliza su ruta existente a v2.

1. En una rama/base acordada, ejecute migration-diagnose. No escribe. Inventaría
   documentos, adjuntos, evidencia y personalizaciones, identidades y trabajo abierto.
2. Prepare migration-preview con actor_name, profile, controls, statement y target.
   La vista fija UUID, conservación de originales, configuración y continuidad.
   Con runtime fijado, el paquete debe incluir su sustitución v3 y adaptadores
   revisados; no se permite dejar el checkout en formato nuevo con escritor antiguo.
3. Valide conjuntamente la conversión y configuración concretas. Aplique ese paquete.
   El origen debe seguir siendo el mismo. Ante interrupción, use recover/rollback.
4. Compruebe validate, runtime-doctor cuando proceda y migration-continuation.
   Las tareas cerradas mantienen su resultado histórico. No se revisa toda la historia.
   Las abiertas conservan plan y contenido: reconcilie únicamente los datos nuevos
   necesarios y autorice su ejecución bajo el método vigente.

Los originales completos quedan bajo `docs/lks-sdd/00-control/migrations/<UUID>/tree/`.
El recibo enumera fuentes, hashes y correspondencias. No se cambia código de negocio.
Una decisión v2 conserva procedencia; no se vuelve aprobación v3 por transformar
su representación. Una aprobación de contenido solo se reutiliza si se acredita su
equivalencia exacta; cuando falte, se valida actualmente la porción abierta.
Las confirmaciones canónicas v2 conservan su procedencia y se contrastan contra sus
originales recuperables y la unidad convertida exacta. Una feature heredada puede
seguir siendo la raíz de propuesta sin reescribir su negocio. No se heredan permisos
operativos: el plan existente necesita autorización actual para continuar en v3.

`old-branch` compara un checkout v2 pendiente con el mapa compartido. Presente los
cambios y aplique autoría v3 revisada, preservando ambos antecedentes. No ejecute una
segunda migración independiente del mismo proyecto ni imponga el índice de una rama.
El plugin no puede impedir que un clon desconectado siga usando v2.

La conversión técnica, la continuidad operativa y la aceptación por las personas son
resultados distintos. Las muestras automatizadas y sus limitaciones se registran en
la evidencia de v3; no se atribuye prueba a una versión publicada sin muestra relevante.
