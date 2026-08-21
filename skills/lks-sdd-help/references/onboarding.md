# Onboarding de cinco a diez minutos

## 1. El problema que resuelve

Generar código antes de aclarar el objetivo, el alcance y la aceptación crea velocidad aparente y retrabajo real. SDD mantiene especificaciones versionadas y comprobables para que lo acordado, lo implementado y lo demostrado puedan compararse.

## 2. Qué añade LKS-SDD

LKS-SDD empaqueta para Codex un método común, plantillas y validadores. El plugin no es la fuente de verdad de una aplicación: esa fuente permanece en los Markdown y evidencias de su repositorio.

## 3. Dónde se trabaja

- Codex es el entorno soportado para ejecutar el plugin sobre una raíz de proyecto, sus archivos y, en hitos posteriores, el código.
- ChatGPT Work puede ser una superficie auxiliar para análisis y revisión de documentos, pero no se declara como runtime equivalente del plugin.
- Un proyecto ChatGPT organiza contexto; un repositorio conserva el estado versionado. No son equivalentes.

Lea [Codex, Work y repositorios](work-codex-guide.md) para entender esta separación y los límites de compatibilidad.

## 4. Dos rutas

- **Aplicación nueva:** definir, decidir, planificar un incremento y evaluar su readiness.
- **Repositorio existente:** empezar con preflight e inspección estática de solo lectura; reconciliar lo observado con la intención confirmada antes de materializar documentación.

## 5. Cómo se decide

Hechos, requisitos, propuestas, decisiones, supuestos y pendientes conservan etiquetas distintas. Solo una confirmación explícita convierte una propuesta en decisión. La pila preferente se compara después de entender requisitos y restricciones; nunca se elige automáticamente.

Una idea breve no se convierte automáticamente en un producto genérico. La definición pregunta en tandas pequeñas por dominio, usuarios, tarea o decisión, entradas, reglas y resultado; las opciones ofrecidas son propuestas y siempre permiten otra respuesta o reconocer que todavía no se sabe.

## 6. Cómo se ve el avance

La cobertura se muestra por dimensiones: suficiente para avanzar en un alcance, requiere profundización, desconocida o no aplicable con motivo. El resumen destaca bloqueos y la siguiente decisión y ofrece más detalle bajo petición. Que los documentos sean estructuralmente válidos no significa que la definición sea suficiente.

Readiness conserva tres resultados: `specification_readiness` para la definición funcional, `delivery_readiness` para gobierno/plan/release/tareas y `automation_support` para perfiles, locks y gates. Una especificación puede estar lista con entrega o automatización bloqueada; se mantiene la decisión tecnológica sin seleccionar otro perfil por defecto.

## 7. Diseño de interfaz

Cuando existe frontend, primero se describen pantallas, flujos, estados, diálogos, accesibilidad y dirección visual. Después pueden generarse propuestas PNG/JPG con ImageGen. Cada imagen sigue siendo propuesta hasta validación humana explícita y se conserva junto al contrato Markdown; la imagen no sustituye comportamiento ni copy confirmados.

## 8. Cómo se organiza la entrega

Antes de implementar se confirma si el producto trabaja como release acotada, evolución continua o mantenimiento. Esa decisión incluye versionado, Git/ramas, entornos, pipeline, promoción, despliegue y recuperación. El trabajo se organiza en un plan y una release, con un tablero breve y una ficha independiente por tarea. Un cambio posterior se registra con fecha efectiva; no invalida ni borra el historial anterior.

La arquitectura puede contener varias unidades desplegables. Cada unidad selecciona un perfil de referencia exacto. Las capabilities permiten reutilizar gates, pero solo la composición completa certificada puede anunciar soporte automático.

## 9. Cuándo aparece el código

La definición y readiness no generan código. Un resultado `ready` tampoco autoriza implementación: la selección TASK y sus bindings solo se preparan mediante preview revisado y autorización explícita. La verificación puede planificarse durante `in-progress`, pero no ejecuta ni registra evidencia hasta `implementation.status=completed`. Después distingue checks superados, fallidos y no ejecutados.

La trazabilidad previa a implementar llega hasta `TEST-###`; después de ejecutar, la fase de verificación exige también `EVID-###` aplicable. Si no hay requisitos confirmados para el alcance, la comprobación no puede superar la puerta por estar vacía.

## 10. Versiones y compatibilidad

Los proyectos nuevos usan método 1.2.0 y esquema 1.2. Los proyectos 1.0/1.1 continúan validándose en compatibilidad y no se migran al actualizar. La migración es explícita, reversible y de un salto. El paso a 1.2 añade estructura pendiente sin inventar gobierno, tareas, perfiles ni evidencia. El apply exige backup externo, autorización y hash coincidente.

## 11. Primer paso a elegir

- pedir una explicación breve;
- definir una aplicación nueva sin código;
- iniciar o comprender la adopción segura de un repositorio existente;
- consultar el estado de un proyecto ya inicializado;
- evaluar un incremento documentado.

La elección inicia un workflow solo cuando la persona lo solicita expresamente.

Cuando se use la CLI local, `<plugin-root>` debe resolverse desde la instalación que contiene `.codex-plugin/plugin.json`; `<project-root>` identifica por separado el proyecto consumidor. El patrón portable es `python "<plugin-root>/scripts/lks_sdd.py" <comando> "<project-root>"`.
