# Contrato de implementación

## Entrada obligatoria

- índice y Markdown válidos;
- incremento `INC-###` confirmado y preparado;
- autorización explícita para implementar;
- perfil seleccionado mediante ADR confirmada;
- lock exacto validado para una capacidad implementable;
- baseline materializada y vigente cuando la ruta sea `adopt-existing`;
- checkout y cambios locales inventariados antes de editar.

## Control de alcance

Codex traduce cada criterio de aceptación en cambios y pruebas concretos. No añade funcionalidades «útiles», refactorizaciones transversales, migraciones destructivas, integraciones o dependencias que no sean necesarias para el incremento. Un bloqueo localizado detiene solo la parte dependiente.

El scaffold H0 crea límites técnicos reproducibles, no comportamiento de negocio. Los nombres, modelos, endpoints y pantallas funcionales proceden de los requisitos confirmados del proyecto.

## Salida

- código y configuración acotados;
- tests con identificadores trazables;
- documentación actualizada quirúrgicamente;
- lista de comandos ejecutados y no ejecutados;
- desviaciones o cambios de alcance visibles;
- evidencia pendiente de verificación independiente.

La implementación no declara por sí misma conformidad, seguridad, accesibilidad, rendimiento ni preparación para entrega.
