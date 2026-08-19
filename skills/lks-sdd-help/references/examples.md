# Ejemplos y prompts de inicio

## Respuesta breve

> Explícame LKS-SDD en dos minutos. No modifiques nada.

Resultado esperado: valor práctico, diferencia entre especificación y código, límites de autoridad y una opción de siguiente paso.

## Aplicación nueva

> Usa `$lks-sdd-define` para ayudarme a delimitar una aplicación nueva. Registra propuestas y decisiones por separado y no generes código.

## Repositorio existente

> Explícame cómo sería la adopción segura de este repositorio. Por ahora, no lo inspecciones ni crees archivos.

Resultado esperado: explicación del preflight, alcance, exclusiones, separación entre `as-is` e intención y pasos de confirmación. Como el prompt prohíbe inspeccionar, no se ejecuta inventario ni se crean archivos.

## Readiness

> Usa `$lks-sdd-assess-readiness` para evaluar `INC-001`. No corrijas documentos ni implementes nada.

## Alternativa tecnológica

> Compara la pila preferente con mi alternativa, pero conserva ambas como propuestas hasta que yo confirme una decisión.
