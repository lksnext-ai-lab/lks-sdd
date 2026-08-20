# Contrato de implementación

## Entrada obligatoria

- índice y Markdown válidos;
- incremento `INC-###` confirmado y preparado;
- autorización explícita para implementar;
- perfil seleccionado mediante ADR confirmada;
- lock exacto validado para una capacidad implementable;
- baseline materializada y vigente cuando la ruta sea `adopt-existing`;
- checkout y cambios locales inventariados antes de editar.
- aplicabilidad de interfaz resuelta para incrementos 0.6+ y, cuando sea aplicable, contrato UX confirmado con prototipo visual validado o una no aplicabilidad visual motivada.

## Control de alcance

Codex traduce cada criterio de aceptación en cambios y pruebas concretos. No añade funcionalidades «útiles», refactorizaciones transversales, migraciones destructivas, integraciones o dependencias que no sean necesarias para el incremento. Un bloqueo localizado detiene solo la parte dependiente.

El scaffold H0 crea límites técnicos reproducibles, no comportamiento de negocio. Los nombres, modelos, endpoints y pantallas funcionales proceden de los requisitos confirmados del proyecto.

El resultado de readiness aporta `checked_files` e `input_fingerprint`. El hash del preview incorpora ese fingerprint; por tanto, cualquier cambio posterior en Markdown o en una imagen validada invalida el apply. Las imágenes no se duplican en `.lks-sdd/project.json`: se consumen desde sus enlaces canónicos y se verifican por contenido.

Para frontend, Codex implementa contra pantallas, flujos, interacciones, accesibilidad, dirección visual y `VIS-###` confirmados. Si la realidad técnica exige desviarse del contrato visual, detiene esa parte y solicita una decisión documentada; no convierte la desviación en aprobación implícita.

## Salida

- código y configuración acotados;
- tests con identificadores trazables;
- documentación actualizada quirúrgicamente;
- lista de comandos ejecutados y no ejecutados;
- desviaciones o cambios de alcance visibles;
- evidencia pendiente de verificación independiente.

La implementación no declara por sí misma conformidad, seguridad, accesibilidad, rendimiento ni preparación para entrega.
