# Checkpoints de ejecución 0.18.0

## CKPT-018-001 — H0

Fecha: 2026-08-31. Estado: contrato materializado; implementación pendiente.

Hechos: creado worktree C:/Dev/lks-sdd-0.18.0 desde main
9b13616e9f9d67c7112ee620c65b8ea6831c50c2, rama codex/release-0.18.0.
El checkout original conserva únicamente site/ y el storyboard no versionados.
CONTRACT.md recoge 24 bloques, nueve variantes, aceptación y límites aprobados.

Verificación H0: comparación del contrato con el plan autorizado; revisión de
diff y ausencia de cambios canónicos. No se han ejecutado aún los gates H1-H6.

Pendientes: R18-02..R18-24. Certificación 0.18, publicación, registro y activación:
not-run. Piloto, producción, revisión humana e interoperabilidad: not-run.

Próximo paso: corregir ART-INTEGRATIONS y sus regresiones sin alterar IDs ni el
schema consumidor 1.5. Mantener SAT en lectura y no tocar el site original.

## CKPT-018-002 — R18-02

Fecha: 2026-08-31. Estado: corrección de tablas y referencias verificada.

Cambios: ambas tablas opcionales de ART-INTEGRATIONS reconocidas en 1.5;
delivery diferencia sistemas externos de interfaces entre unidades. Rechaza
duplicados dentro de una tabla o entre ambas sin renumerar ni escribir documentos.

Evidencia ejecutada: unittest tests.test_integrations_v018 y
tests.test_contract_engine: 17 passed; tests.test_fullstack_integration_contract_v017
y tests.test_quality_suite_registry: 18 passed. validate_plugin_contract.py:
VALID; validate_fixture_manifest.py: VALID (12 fixtures). Diff sin whitespace.
Estos resultados no acreditan todavía variantes, autenticación ni H5.

Pendientes: R18-03..R18-24. Próximo paso: observadores y operaciones declaradas
comunes, eliminando la dependencia de /api/v1 y la obligación de browser para DB.

## CKPT-018-003 — implementación en curso, sin certificación

Fecha: 2026-08-31. Estado: H1/H2 avanzados; H3/H4 en desarrollo. No publicar.

Hechos observados:

- 21 regresiones de integraciones pasan: rutas declaradas, login ajeno al contrato,
  mocks fuera de /api/v1, HTTP read-only y elección de observadores sin browser para DB.
- Siete regresiones de diagnóstico/adopción pasan: versiones declaradas/resueltas
  separadas, drift, React 16/17 negativos, ambos layouts y archivos preservados.
- Nueve perfiles candidate creados; cinco contratos arquitectónicos no seleccionables.
  Se han resuelto locks Python y Node. Ninguna variante está certificada ni activa.
- 33 pruebas de seguridad contra PostgreSQL real pasan en Python 3.13 y 3.14.
  Esto es diagnóstico sobre fixtures, no certificación de perfiles completos.
- Primer flujo Chromium/HTTPS en PY313-TS59 pasa: escritura /records, lectura SQL
  independiente, recarga, cookies seguras, dos pestañas y logout offline honesto.
  La lectura después del reinicio observado es SQL; queda completar la prueba HTTP
  posterior y fallos de servicios. Revisión visual automática inspeccionada, humana not-run.
- Baseline 0.17.0 descargada fuera del worktree; los cinco hashes coinciden con GitHub.

Diagnósticos externos: C:/Dev/lks-sdd-0.18.0-evidence/dev-api-py313 y
dev-system-py313; dev-system-py314. Contienen exclusivamente datos sintéticos y
secretos efímeros de prueba; no incluir .runtime en bundles ni en contextos Docker.
Los Dockerfiles incorporan .dockerignore. Las redes/containers lkssdd18* creadas
por verification/gate.py son desechables; limpiar únicamente mediante su --cleanup.

Pendientes materiales: terminar conexión de composiciones en preparación/readiness/
runner/trazabilidad, pruebas de adopción desde bundle, fortalecimiento semántico de
evidencia PostgreSQL/migración/procedencia, tests de fallos y recuperación, cerrar
versiones/hashes de herramientas e imágenes, completar fixtures e inventarios,
recertificar 8 activos + 9 nuevos, regresión integral y reproducibilidad, PR/CI/tag,
publicación y marketplace. Los cambios del motor invalidan las certificaciones
anteriores para soporte vigente hasta recertificarlas. Es esperado durante desarrollo.

Publicación 0.18, registro y activación local: not-run. SAT y canónicos: sin cambios.

## CKPT-018-004 — contratos y candidatos implementados; certificación pendiente

- 30 regresiones específicas pasan; 23 perfiles estructuralmente válidos y 14
  fixtures inventariados. Dos fixtures nuevos prueban adopción sin sobrescritura.
- Los gates completos diagnósticos de API PY314, API PY313 y PostgreSQL pasaron.
  Las dos líneas web pasaron previamente HTTPS/SQL/reload/reinicio; las ampliaciones
  de separación del migrador, outage y suites siguen en validación. No acreditan H5.
- Seguridad ampliada a 39 casos PostgreSQL reales: tamaño de cuerpo sin confiar
  en Content-Length, configuración cerrada y límites compartidos de hash incluidos.
- La SPA añade rechazo de respuestas tardías tras logout y rutas de otro origen.
  Se corrigieron los filtros ESLint/Vitest para separar fuente, build y Playwright;
  se repite el gate completo, conservando diagnósticos fallidos fuera del repositorio.
- Sistema resuelto por INT, cuatro bindings y locks participantes; job y base de
  datos independientes. La evidencia exige lectura SQL estructurada del mismo ID,
  recursos/revisions declarados y composición exacta. Los booleanos no bastan.
- Certificación interna 1.1 incorpora observaciones, capturas y hashes del motor;
  los lectores históricos permanecen. Una ejecución durante cambios del motor
  fue rechazada por deriva. Deben recertificarse los ocho activos con el motor final.
- Preparación adoptada: diagnóstico estático y recursos de verificación; la
  adaptación funcional/fixture queda explícita y no se ejecuta el scaffold contra
  el consumidor. La hoja SAT documenta cambios potenciales, sin ejecutar ninguno.
- Metadatos de desarrollo en 0.18.0, baseline 0.17.0 verificada, corpus humano
  0.18 not-run y seis casos automatizados nuevos FX-61..66. Los presupuestos no cambian.
- Fuentes normalizadas a LF antes de cerrar hashes, conforme a .gitattributes.

Pendientes: completar/certificar las nueve variantes candidate; recertificar ocho
activos; regresión fast/integration/package/profile, evals, benchmark, instalación
de prueba y round-trip desde bundle; cerrar matriz R18 con evidencia; commits/PR/CI,
checkout limpio final, doble build, tag/prerelease, descarga y verificación,
marketplace local y activación tras reinicio. Publicación/registro/activación not-run.

## CKPT-018-005 — motor definitivo y recertificación en curso

Fecha: 2026-08-31. No publicar hasta cerrar H5.

- 23 pruebas específicas de integraciones, variantes y adopción pasan; seis evals
  y catorce fixtures validados. Corpus 0.18 y baseline 0.17 están reconciliados.
- El runner ejecuta el observador empaquetado, no una copia editable del consumidor,
  y rechaza imágenes/configuración ajenas a la variante. Un sistema no puede
  ocultarse en un BIND de unidad ficticia.
- Cada observación certificada lleva identidad de ejecución, perfil, variante,
  runtime y hashes de fuentes/motor. Se rechazan mezclas aun recalculando hashes;
  capturas y manifiesto deben concordar. El historial detallado se conserva.
- La SPA comprueba el origen después de normalizar URLs del navegador, incluidos
  casos de barras invertidas y caracteres de control. Los cuatro locks web/sistema
  afectados se regeneraron; las variantes se certifican después de este cambio.
- Se han actualizado las seis skills sin cambiar nombres, descripciones o
  invocación implícita. La documentación distingue los observadores por protocolo
  y el marketplace local usa remove/add, nunca upgrade sobre la fuente no Git.
- El workflow compara los cinco assets y valida plugin y marketplace de ambos
  builds. Conserva presupuestos, canales humanos y fecha única de certificación.
- Recertificación completa en curso: ocho perfiles anteriores y nueve candidatos.
  Cada candidato debe pasar con el motor actual antes de promocionarse; después
  se ejecutan de nuevo todos sus gates para certificar el descriptor promovido.
  Hasta cerrar la segunda ejecución no se presenta como soporte vigente.
- La pasada fast diagnóstica detectó un timeout bajo carga Docker y aserciones
  históricas de corpus/inventario. Estas últimas están corregidas; los tiempos
  deben medirse de nuevo sin carga concurrente. No se ampliaron presupuestos.

Evidencia de trabajo externa: C:/Dev/lks-sdd-0.18.0-evidence, ficheros
candidate-v018-*, cert-v018-* y promotion-*. Las certificaciones vigentes se
comprueban con el lector del plugin, no por el nombre del fichero de diagnóstico.

Pendientes: finalizar 17 certificaciones, regresión completa y benchmark sin carga,
round-trip/bundle, cierre de matriz y notas, PR/CI/main final, checkout limpio,
harness candidate, doble build, tag/prerelease y descarga verificada, marketplace
y activación tras reinicio. SAT y fuentes canónicas no modificados; site/storyboard
del workspace original intactos. Publicación/registro/activación: not-run.

## CKPT-018-006 — revisión del coste de ejecución

El usuario cuestiona expresamente la agilidad tras más de dos horas. Se reconoce
repetición evitable: certificar mientras cambiaban las fuentes y volver a ejecutar
por metadatos de promoción. La última SPA TS59 pasó sus checks, pero el registro
se rechazó por deriva de fuentes durante la ejecución; no fue un fallo funcional.

Se detuvieron las colas automáticas de nuevas certificaciones. La comprobación
API-FASTAPI-KEYCLOAK-PG-OCI ya iniciada puede finalizar y limpiar sus recursos;
no se encadenará el siguiente perfil. No lanzar más baterías completas sin
resolver primero su necesidad y congelar los inputs. Las dos API locales han
cerrado sus gates finales; el resto no se presenta como terminado por analogía.

Criterio de continuación: pruebas dirigidas durante desarrollo; una regresión
completa sobre código congelado; certificación de combinaciones comprometidas;
verificaciones de paquete/publicación. Separar duración útil de repetición
evitable. El acoplamiento actual entre metadatos y certificado necesita tratarse
sin fabricar procedencia ni modificar certificados para aparentar una ejecución.
No se ha acordado reducir alcance, omitir controles de seguridad o publicar con
gates pendientes. Publicación, registro y activación local siguen sin ejecutar.

## CKPT-018-007 — diecisiete certificaciones cerradas, integración y entrega pendientes

Fecha: 2026-08-31. El usuario autoriza continuar conservando las nueve
certificaciones vigentes y cerrando las ocho pendientes, sin ampliar alcance.

Se fijaron los metadatos finales en una copia temporal de certificación; cada
perfil pasó una única batería completa y se incorporó al worktree solo después
de validar fuentes, motor, observaciones y locks exactos. No se modificó el motor
ni se reescribió procedencia para evitar una ejecución. Los nueve certificados
anteriores permanecen byte a byte intactos.

Resultado: 17 perfiles active con certificación exacta vigente; otros 6 candidate
sin promoción; 23 locks actuales. Pasan validadores de contrato, plugin, seis
skills y catorce fixtures. Los canales humanos y de piloto mantienen su estado.

El contenido funcional y los metadatos de perfiles quedan congelados. La regresión
previa se ejecuta mediante el PR/CI; el harness candidate publicable se ejecutará
en el checkout limpio del SHA final de main y reutilizará estas certificaciones.
Los resultados finales de H5/H6 estarán anclados a ese SHA en los assets externos;
este checkpoint versionado no pretende anticiparlos.

Pendientes: revisar/confirmar evidencia, PR y CI; integrar; harness final y doble
build; workflow de tag y prerelease privada; descargar/verificar cinco assets;
marketplace local y activación tras reinicio. El estado de rollback 0.17.0 está
guardado fuera del repositorio y el marketplace aún no se ha modificado.
