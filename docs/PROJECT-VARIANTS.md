# Variantes tecnológicas aprobables

Una combinación desconocida no es una incompatibilidad demostrada. La nueva ruta
optativa permite aprobar una combinación concreta y verificar sus TASK sin
certificar globalmente ese stack. El modo estricto sigue siendo el predeterminado.

## Estados y límites

| Eje | Resultado y significado |
|---|---|
| Compatibilidad | `exact-certified`: metadatos observados coinciden con una referencia certificada. No demuestra todavía el comportamiento del consumidor. |
| Reglas certificadas | `compatible-certified` queda reservado: los rangos descriptivos actuales no conceden este estado. |
| Variante | `unassessed-variant`: diferencias observables sin contradicción demostrada. |
| Aprobación | `approved-project-variant`: aprobación vigente para esas entradas y alcance. |
| Incompatibilidad | `incompatible`: contradicción manifest/lock demostrada. |
| Información | `not-assessed`: entradas ausentes, ilegibles o diagnóstico insuficiente. |
| Verificación | `verified`, `verified-with-reservations`, `not-verified`; los gates conservan su resultado real. |
| Cierre | `task_status` sigue independiente; `work complete` comprueba política, AUTH, EXEC, evidencia vigente y gates de aceptación. |
| Entrega | `delivery_readiness=not-assessed`; la aprobación tecnológica nunca ejecuta ni autoriza despliegue. |

Las variantes aprobadas producen `verified-with-reservations` cuando superan los
gates requeridos de la TASK: siempre conservan la ausencia de certificación global
y el límite de entorno/etapa como reservas. `--allow-unvalidated` no es una aprobación.
No se admite `--force` para saltar una aprobación o gate. El rerun forzado exige
motivo y otra EVID, y solo vuelve a ejecutar comprobaciones.

## Recorrido cotidiano

1. Ejecutar `variants diagnose` sobre la unidad tecnológica. Sin `--profile`, el
   resultado propone la referencia con más dependencias observadas en común y
   desempata por ID: es una referencia de comparación, no una selección de stack.
2. Confirmar la referencia en el binding/INT y mantener el contrato, planificación
   y AUTH habituales. La aprobación tecnológica no sustituye autorización de implementación.
3. Preparar el único documento optativo descrito debajo y presentar juntos:
   diferencias, composición, gates afectados, observer, riesgos, entorno y caducidad.
4. Mostrar `variants preview`; aplicar su hash únicamente después de la aprobación
   del responsable. La escritura es una decisión durable; repetirla es idempotente.
   Antes de iniciar un consumidor ya existente, usar `variants prepare` o
   `work start`: esta ruta crea únicamente locks base y EXEC/CKPT, sin copiar
   scaffolds ni sobrescribir código funcional. La aprobación debe preceder al inicio.
5. Usar `work verify` o `verify --variant` para la etapa elegida. La repetición
   reutiliza gates deterministas vigentes. `work complete` cierra solo si la política
   lo permite y todos los gates de aceptación e integración aplicables están pasados.

No preguntar otra vez por una aprobación vigente. Agrupar las decisiones nuevas en
una sola interacción. Mostrar el resumen primero; usar `--detail` para consultar
todos los hashes, versiones, diferencias y material aprobado.

```powershell
python <plugin-root>/scripts/lks_sdd.py variants diagnose <project-root> --profile API-FASTAPI-STATELESS-OCI --json
python <plugin-root>/scripts/lks_sdd.py variants preview <project-root> --variant VAR-001 --stage development --actor project-owner --reason "API equivalente; versiones revisadas" --risks "Compatibilidad limitada a los gates declarados" --expires YYYY-MM-DD
python <plugin-root>/scripts/lks_sdd.py variants approve <project-root> --variant VAR-001 --stage development --actor project-owner --reason "API equivalente; versiones revisadas" --risks "Compatibilidad limitada a los gates declarados" --expires YYYY-MM-DD --apply --authorize <preview_hash>
python <plugin-root>/scripts/lks_sdd.py variants status <project-root> --variant VAR-001 --stage development
python <plugin-root>/scripts/lks_sdd.py work start <project-root> --increment INC-001 --task TASK-001 --json
python <plugin-root>/scripts/lks_sdd.py work verify <project-root> --task TASK-001 --json -- --stage development
python <plugin-root>/scripts/lks_sdd.py verify <project-root> --variant VAR-001 --increment INC-001 --task TASK-001 --execution-id EXEC-001 --stage integration --plan --json
python <plugin-root>/scripts/lks_sdd.py verify <project-root> --variant VAR-001 --increment INC-001 --task TASK-001 --execution-id EXEC-001 --stage integration --execute --authorize --record-evidence EVID-002 --json
python <plugin-root>/scripts/lks_sdd.py work complete <project-root> --task TASK-001 --json
```

Cambiar de etapa requiere aprobación para la nueva etapa. Desarrollo no habilita
integración, release ni producción. `variants verify` ofrece la misma campaña en
la CLI de variantes; sin `--execute` solo muestra el plan. No descarga imágenes:
la imagen revisada y fijada por digest debe estar disponible en el daemon local.

## Documento canónico optativo

La ruta depende del contrato activo y no debe mezclarse durante una migración:

| Contrato | Variantes | Aprobaciones |
|---|---|---|
| 1.5 / 1.5.0 | `docs/lks-sdd/02-design/technology-variants.md` | `docs/lks-sdd/02-design/technology-approvals/` |
| 2.0 / 2.0.0 | `docs/lks-sdd/03-solution/technology-variants.md` | `docs/lks-sdd/00-control/technology-approvals/` |

En ambos casos el documento contiene exactamente un bloque `lks-sdd-variants`
con el objeto validado por
[`project-variants.schema.json`](../schemas/project-variants.schema.json).
El índice de proyecto 1.5 no necesita campos nuevos. Durante 1.5→2.0 el
documento se transforma a la ruta v2 y las aprobaciones históricas se archivan;
ninguna aprobación histórica se reactiva como autoridad v2.

Ejemplo conceptual (sustituir el hash, la imagen y el comando por entradas revisadas):

````markdown
# Tecnología de proyecto

```lks-sdd-variants
{
  "schema_version": "1.0",
  "policy": {
    "mode": "approved-project-variants",
    "allow_task_closure": true,
    "allowed_stages": ["development", "integration"],
    "approver_roles": ["project-owner"],
    "max_age_days": 30,
    "cache_max_age_hours": 24
  },
  "variants": [{
    "id": "VAR-001",
    "profile_id": "API-FASTAPI-STATELESS-OCI",
    "increment": "INC-001",
    "release": "REL-001",
    "task_ids": ["TASK-001"],
    "environment": "ENV-001",
    "technology_roots": ["backend"],
    "inputs": ["backend", "verification/observer.py"],
    "composition": {"layout": "backend", "difference": "package layout differs from reference"},
    "gates": [{
      "id": "GATE-API-TEST",
      "source": "approved-consumer",
      "stage": "development",
      "scopes": ["component"],
      "interfaces": [],
      "deterministic": true,
      "timeout_seconds": 60,
      "image": "REGISTRY/IMAGE@sha256:DIGEST_REVISADO",
      "observer": {
        "path": "verification/observer.py",
        "sha256": "HASH_REVISADO",
        "inputs": [],
        "command": ["/usr/local/bin/python", "-I", "-B", "/input/verification/observer.py"]
      }
    }]
  }]
```
````

Cada gate puede reducir sus `inputs` a rutas relevantes; por defecto recibe todos
los `inputs` de la variante. Estos deben cubrir el código, pruebas, configuración
y contratos técnicos que determinan el resultado. Los auxiliares del observer
se declaran en `observer.inputs`; sus bytes también requieren revisión al cambiar.
Las rutas tecnológicas incorporan automáticamente los manifests y locks reconocidos.
Las composiciones de varias unidades conservan sus bindings y locks base en INT;
la composición real diferente se describe y aprueba en `composition`.

El responsable debe revisar los roles permitidos en la política versionada. Como
AUTH, la aprobación local atribuye la decisión a un rol, no implementa autenticación
corporativa ni firma criptográfica de identidad. La integridad detecta alteraciones;
los permisos del repositorio y su revisión protegen la autoridad humana.

## Observer y aislamiento

Fuentes admitidas: `packaged`, `approved-consumer`, `experimental`. La última no
puede aprobarse ni ejecutarse oficialmente. `packaged` conserva el comando del
perfil; no admite un override de consumidor. Para layout distinto o salida
estructurada, declarar y aprobar un observer explícito.

El contenedor Linux usa imagen con SHA-256, usuario sin privilegios, raíz y entradas
de solo lectura, capacidades eliminadas, red exterior deshabilitada y límites de
memoria, CPU, procesos, tiempo y salida. No recibe el contrato canónico, secretos
del host, su entorno, socket Docker o credenciales. `/tmp` permite trabajo efímero;
`/output` es el único directorio montado escribible. Las aplicaciones y servicios
que necesite observar deben ser autocontenidos en esa imagen/ejecución. Esta primera
ruta no observa directamente servicios externos ni infraestructura de producción.
Un requisito externo no satisfecho permanece bloqueado.

El observer emite un objeto JSON validado contra
[`consumer-observation.schema.json`](../schemas/consumer-observation.schema.json).
Incluye `LKS_RUN_NONCE`, gate, scopes, interfaces, observaciones y archivos producidos
en `LKS_OUTPUT`, con sus hashes. El runtime verifica nonce, salida real del proceso,
schema, semántica de scopes críticos y bytes de artefactos antes de crear EVID.
Un `passed` escrito en stdout no basta. La revisión del código del observer sigue
siendo necesaria: el aislamiento y el schema no prueban por sí solos que sus
aserciones representen correctamente la aceptación funcional.

Los gates visuales e interfaces mantienen sus contratos de evidencia existentes;
los mocks de dominio, capturas insuficientes o lecturas sin persistencia no se
convierten en integración válida. No se sustituye un observer empaquetado en silencio.
`GATE-VISUAL-BROWSER-REVIEW` no se declara como observer: se aporta con
`--visual-evidence docs/lks-sdd/evidence/visual/REVIEW.json` y se valida mediante
el contrato visual 1.2 existente, incluyendo alcance, revisión y capturas reales.
Sin esa evidencia, una TASK visual permanece pendiente. El cierre vuelve a
comprobar sus hashes; una autodeclaración del observer no acredita revisión humana.

## Reutilización, caducidad y compatibilidad

El fingerprint de aprobación incorpora stack y versiones, hashes de manifests/locks,
observer y auxiliares, comando/imagen, gates, composición, perfil base, AUTH,
planificación, entorno, etapa y política. Cambiar cualquiera de esos elementos
requiere revisar una nueva propuesta. Cambiar código normal invalida evidencia,
sin pedir otra aprobación tecnológica si sus condiciones permanecen iguales.

La caché reutiliza EVID y artefactos íntegros, no un booleano guardado. Cada gate
liga entradas relevantes, motor y aprobación; solo se reutiliza si es determinista
y está dentro de `cache_max_age_hours`. La promoción a release/producción exige
ejecución completa. No se reutilizan fallos, bloqueos ni omisiones. El reporte
separa `executed`, `reused` y `omitted`, con motivos. Una omisión crítica mantiene
la TASK `not-verified`, aunque esa iteración de desarrollo haya sido útil.
La edad se calcula desde `observed_at`, conservada al reutilizar: crear otra EVID
no rejuvenece un resultado. `--reuse-evidence EVID-###` limita la búsqueda a esa
evidencia; entradas caducadas se ejecutan de nuevo con otra EVID inmutable.
El cierre comprueba aprobación aún vigente y entradas actuales, independientemente
del TTL de caché usado para decidir qué procesos repetir. Los fallos y omisiones
tienen también un artefacto de resultado persistido, sin fingir un build exitoso.

Los proyectos existentes no se migran, no reciben preguntas nuevas ni alteraciones
de locks/EVID. El motor certificado permanece intacto y su CLI directa conserva el
modo estricto. La ruta optativa usa el dispatcher público y los seis workflows
existentes. Actualizar o instalar el plugin, publicar y ejecutar una release siguen
siendo operaciones separadas.

## Verificación del evolutivo

```powershell
python -X utf8 tests/run_unit_tests.py --module test_project_variants
python -X utf8 tests/variant_docker_smoke.py
```

La fixture genérica reproduce versiones diferentes, dependencia adicional,
composición equivalente y observer de consumidor. La prueba Docker ejecuta
aserciones reales en aislamiento, vuelve a verificar con cero procesos, completa
la TASK mediante TASK/EXEC/CKPT y comprueba el contrato resultante. No demuestra
interoperabilidad de todos los stacks ni aceptación humana de una release.
