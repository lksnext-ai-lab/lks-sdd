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

## 7. Diseño de interfaz

Cuando existe frontend, primero se describen pantallas, flujos, estados, diálogos, accesibilidad y dirección visual. Después pueden generarse propuestas PNG/JPG con ImageGen. Cada imagen sigue siendo propuesta hasta validación humana explícita y se conserva junto al contrato Markdown; la imagen no sustituye comportamiento ni copy confirmados.

## 8. Cuándo aparece el código

La definición y readiness no generan código. Un resultado `ready` tampoco autoriza implementación: el perfil H0 solo se prepara mediante un preview revisado y autorización explícita. La verificación se planifica antes de ejecutarse y distingue checks superados, fallidos y no ejecutados.

## 9. Primer paso a elegir

- pedir una explicación breve;
- definir una aplicación nueva sin código;
- iniciar o comprender la adopción segura de un repositorio existente;
- consultar el estado de un proyecto ya inicializado;
- evaluar un incremento documentado.

La elección inicia un workflow solo cuando la persona lo solicita expresamente.
