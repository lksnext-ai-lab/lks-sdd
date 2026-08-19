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
- **Repositorio existente:** empezar con preflight e inspección de solo lectura. La automatización de esta ruta sigue en backlog en `0.1.0`.

## 5. Cómo se decide

Hechos, requisitos, propuestas, decisiones, supuestos y pendientes conservan etiquetas distintas. Solo una confirmación explícita convierte una propuesta en decisión. La pila preferente se compara después de entender requisitos y restricciones; nunca se elige automáticamente.

## 6. Cuándo aparece el código

M1 no genera código. Readiness evalúa un incremento y explica bloqueos, pero un resultado `ready` tampoco autoriza implementación.

## 7. Primer paso a elegir

- pedir una explicación breve;
- definir una aplicación nueva sin código;
- comprender la futura adopción de un repositorio existente;
- consultar el estado de un proyecto ya inicializado;
- evaluar un incremento documentado.

La elección inicia un workflow solo cuando la persona lo solicita expresamente.
