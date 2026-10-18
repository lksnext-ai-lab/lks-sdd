# Corrección del bloqueo de aprobaciones S8

Fecha: 2026-10-17. **Resuelto en fuente y en los componentes del paquete corregido**.
No se ha repetido S8 ni se acepta su rendimiento o su recorrido final.

La causa era un recorrido inverso de pertenencia: plan → tarea → interfaz → propuesta
propietaria. Arrastraba de nuevo esa propuesta y sus 35 tecnologías al descriptor
del plan y de la tarea, aunque la propuesta ya tiene su comprobación separada.
No habían cambiado los documentos ni sus decisiones; había cambiado el conjunto exigido.

`v3_approval` distingue ahora el inventario `interfaces` de una propuesta/feature
heredada de una dependencia normativa entrante. Solo omite ese enlace inverso de
pertenencia; conserva `depends_on`, `implements`, `modifies`, `contributes_to` y
dependencias tipadas explícitas, incluso si coinciden con el inventario. Las reglas
globales y los contratos de interfaz permanecen. El selector de contexto no cambia:
las fuentes literales completas siguen disponibles. La propuesta y su tecnología
siguen formando parte de las bases de ejecución y un cambio material las invalida.

El caso original de 338 elementos vuelve a **286 unidades**, con plan, ejecución
y revisión de tarea acreditados por **las mismas decisiones originales**. No hay
fallback que acepte cualquier descriptor antiguo, escritura de decisiones ni renovación
automática. Una dependencia normativa nueva o modificada sigue exigiendo cobertura.

## Comprobaciones y paquete

- **25 casos de alcance/aprobación superados**, cinco nuevos. Incluyen decisiones
  anteriores, propuesta y tecnología cambiadas, contrato modificado, revocación,
  globales, dependencias explícitas/tipadas y ausencia de aprobación implícita de otra
  propuesta. Se comprueba también que el contexto conserva propuesta, interfaz y tecnología.
- **Dos recorridos afectados superados**: ciclo completo y código obsoleto;
  mutación concurrente durante preparación rechazada antes del primer efecto.
- **Dos componentes desde la CLI fijada del nuevo paquete**: `work-prepare` y
  previsualización `work-continue` devuelven `ready`, con capturas `stored`, sin
  escrituras/efectos. La tarea permanece en backlog, `app.py` ausente y todos los
  originales y digests de decisiones intactos. No se implementa ni inicia S8.
- Contrato estático, 13 fixtures y revisión del diff superados. No cambian esquemas,
  `specs/canonical/`, autoridad de personas, formatos, E/S ni guardas de aplicación.
  La cobertura de rutas largas y del resto del núcleo se reutiliza en su alcance
  no afectado; no se declara un nuevo gate stable ni se retoma el incidente de Windows.

Cinco ZIP `development-unreleased`, **dos construcciones reproducibles** del mismo
núcleo, checksums/CRC/recursos comprobados y núcleo Codex/Copilot idéntico.
Fuente: `working-tree:f5d853c6e5a20163ad6bdf9c798aa2cdead8682ceb535a3d7fd6c10f2c49f283`.
Runtime: `296e104a253a9c75b5f54042270f550b91f49c394469ee82dfcff4e9b14a7103`.
Paquetes: `C:\AI-Workspace\management\operations\lks-sdd-v4-h1-20261015\v4-17\correction\candidate-packages`.
La versión base de manifest sigue 3.4.3; canal, fuente y digest identifican esta
candidata de desarrollo. No es la 3.4.3 publicada ni una versión estable instalada.

El arnés usó inicialmente una ruta de ascendencia incorrecta después de construir
los paquetes. Se corrigió y se retomó solo la comprobación de componentes; los
archivos ya construidos se verificaron y reutilizaron. El error queda conservado.

## Estado y presupuesto

El hallazgo de cobertura de aprobaciones queda resuelto en este alcance. Los dos
intentos finales anteriores se conservan sobre su candidata original: no se sustituyen
bytes ni se transforman retrospectivamente en éxitos. Los paquetes nuevos sustituyen
los anteriores únicamente para futuras comprobaciones.

**48/48 conocidos y reservados**, sin ampliación: cero intentos nuevos de recorrido
completo o variantes M6; se retienen dos reservas S8 y dos H2. Las pruebas focales y
las dos consultas/previsualizaciones se contabilizan aparte, sin atribuir ahorro.
No se deduce un nuevo saldo global de horas ni consumo facturado de estos resultados.

AC-26 mantiene pendientes de rendimiento/aceptación final; AC-40, AC-42/43 y la
observación real de hosts siguen pendientes. Dos reservas S8 no reinician por sí
solas una serie válida de cuatro sobre otra revisión. La corrección no resuelve
automáticamente ese límite de cobertura. Windows y H2 permanecen pendientes;
sin instalación, publicación, commit ni push.

Registro: [v4-17-correction-progress.json](v4-17-correction-progress.json).
Los resultados previos siguen en [RESULTS-V4-17.md](RESULTS-V4-17.md).
Evidencia: `C:\AI-Workspace\management\operations\lks-sdd-v4-h1-20261015\v4-17\correction` (fuente previa, 27 métodos focales, componentes, huellas y paquetes).
