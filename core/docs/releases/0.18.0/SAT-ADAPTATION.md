# Hoja de adaptación del SAT — propuesta sin ejecución

Estado: diagnóstico de lectura y trabajo potencial del consumidor. No autoriza
modificación, instalación, migración, provisión de identidades ni despliegue del
SAT. La referencia consultada es `C:/Dev/sat-next-ai-designer`.

Observado estáticamente: estructura `backend/`–`frontend/`; Python declarado 3.13
y Node 24. FastAPI 0.125.0, SQLAlchemy 2.0.45, Alembic 1.17.2 y PyJWT 2.10.1 están
declarados en los manifiestos Python. React, TypeScript, Vite y Vitest se declaran
con rangos `^19.2.7`, `^5.9.3`, `^8.0.16`, `^4.1.10`. Los Dockerfiles observados
no fijan los digests de Python/Node y no se encontró declaración exacta de sus
gestores de paquetes. Estas observaciones no afirman versiones de producción.

| Área | Encaje propuesto | Adaptación potencial del SAT | Cierre requerido |
|---|---|---|---|
| Documentación | Mantener schema 1.5/método 1.5.0 | Reconciliar integraciones externas e internas preservando INT | Validación documental y trazabilidad |
| Unidades | API, SPA, PostgreSQL y job Alembic separados | Confirmar cuatro UNIT/BIND, propietarios y rutas reales | Decisión de arquitectura |
| Selección | Línea PY313/TS59 como primera candidata | Contrastar manifests/locks/runtime/herramientas; no actualizar a PY314/TS60 automáticamente | ADR y resolución completa |
| Composición | Sistema PY313-TS59 desde INT | Precisar contratos HTTP, SQL, migración, participantes y tareas de integración | Lock de sistema y cuatro locks participantes |
| Autenticación | Capabilities de credenciales, sesión, SPA, permisos y auditoría | Contrastar hash, keyring, refresh, revocación, CSRF y pertenencias con la conducta existente | Análisis funcional y de seguridad propio |
| API e interfaz | Adopción sin copia del scaffold | Mapear entradas y operaciones reales; conservar rutas y negocio existentes | Adaptador funcional y pruebas autorizadas |
| Base de datos | Perfil OCI y observador PostgreSQL | Fijar imagen exacta y preparar lectura independiente de operaciones del contrato | Fixture sintético aislado; ningún dato real |
| Migraciones | Job independiente de la API | Contrastar revisions y ensayar forward-fix/recuperación | Base desechable y evidencia de conservación |
| Herramientas | pip/npm observados en la línea de referencia SAT | Fijar versiones exactas y transitivas, sin cambios durante el diagnóstico | Locks y digests revisados |
| Verificación | Observadores HTTP, navegador, SQL y migración separados | Preparar entorno HTTPS, identidades sintéticas y aislamiento comprobable | Autorización de tareas y ejecución del consumidor |
| Evidencia | Seis scopes y procedencia exacta | Reconciliar evidencia insuficiente sin borrar historial | Revisión, entorno, locks, observaciones y hashes |
| Entrega | Fuera de la certificación inicial del plugin | Definir backup, restauración, promoción y controles productivos propios | Alcance y autorización separados |

La coincidencia de versiones declaradas no certifica el SAT. Las bibliotecas o
dependencias adicionales pueden dejar la combinación como no evaluada. Los
pendientes de fixture, contrato funcional y runtime deben permanecer visibles;
no se resolverán ejecutando la aplicación, copiando el scaffold o usando su base
de datos. El cambio de plugin tampoco equivale a una migración del consumidor.

Secuencia propuesta, aún sin ejecutar: cerrar inventario y documentación; decidir
bindings; preparar un entorno aislado autorizado; adaptar recursos de verificación;
implementar únicamente los cambios funcionales aprobados; ejecutar componentes,
sistema y negativos; revisar evidencia; tratar despliegue como entrega independiente.
