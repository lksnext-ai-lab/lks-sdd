# Contrato de implementación

## Entrada obligatoria

- índice y Markdown válidos;
- incremento `INC-###` confirmado, con `specification_readiness` listo y estado combinado preparado;
- autorización explícita para implementar;
- perfil seleccionado mediante ADR confirmada;
- `automation_support: supported` y lock H0 empaquetado validado para una capacidad implementable;
- baseline materializada y vigente cuando la ruta sea `adopt-existing`;
- checkout y cambios locales inventariados antes de editar.
- aplicabilidad de interfaz resuelta para incrementos 0.6+ y, cuando sea aplicable, contrato UX confirmado con prototipo visual validado o una no aplicabilidad visual motivada.

## Control de alcance

Codex traduce cada criterio de aceptación en cambios y pruebas concretos. No añade funcionalidades «útiles», refactorizaciones transversales, migraciones destructivas, integraciones o dependencias que no sean necesarias para el incremento. Un bloqueo localizado detiene solo la parte dependiente.

El scaffold H0 crea límites técnicos reproducibles, no comportamiento de negocio. Los nombres, modelos, endpoints y pantallas funcionales proceden de los requisitos confirmados del proyecto.

El resultado de readiness aporta `checked_files`, `active_contract_fingerprint`, `profile_lock`, `document_fingerprint` y la vista compatible `input_fingerprint`. El hash del preview se vincula a la huella del contrato activo; cualquier cambio posterior en un input Markdown, relación, lock o imagen confirmada de ese incremento invalida el apply. Las filas históricas permanecen en la huella documental para auditoría, pero no se convierten en inputs activos. Las imágenes no se duplican en `.lks-sdd/project.json`: se consumen desde sus enlaces canónicos y se verifican por contenido.

En el dry-run previo, `.lks-sdd/profile.lock.json` puede no existir todavía: el plan debe incluir la copia byte a byte de `technology-profile.lock.json` del H0 empaquetado y la huella activa ya está ligada a su SHA-256 esperado. Si el destino existe y es idéntico se conserva; si contiene `{}`, difiere, es un directorio o usa un enlace, la preparación falla cerrada y no sobrescribe nada. El apply autorizado materializa la copia exacta. Desde ese momento, verificación exige el archivo consumidor y vuelve a compararlo con el empaquetado.

Que `specification_readiness` sea favorable no basta si `automation_support` está `selection-required` o `unsupported`. Esta skill solo prepara el perfil H0 empaquetado; no sustituye una pila alternativa, no la considera un defecto funcional y no selecciona H0 automáticamente.

Para frontend, Codex implementa contra pantallas, flujos, interacciones, accesibilidad, dirección visual y `VIS-###` confirmados. Si la realidad técnica exige desviarse del contrato visual, detiene esa parte y solicita una decisión documentada; no convierte la desviación en aprobación implícita.

## Salida

- código y configuración acotados;
- tests con identificadores trazables;
- documentación actualizada quirúrgicamente;
- lista de comandos ejecutados y no ejecutados;
- desviaciones o cambios de alcance visibles;
- evidencia pendiente de verificación independiente.

La implementación no declara por sí misma conformidad, seguridad, accesibilidad, rendimiento ni preparación para entrega.

El índice conserva `implementation.status: in-progress` mientras quede trabajo del incremento y usa `blocked` si ese trabajo no puede continuar. Solo cuando código, documentación, pruebas de implementación y registro de alcance estén realmente completos puede cambiarse a `completed`; en ese momento `implementation.increment`, `profile_id` y `changed_paths` deben describir exactamente la implementación entregada. El plan de verificación puede consultarse durante `in-progress`, pero ejecutar checks o registrar evidencia falla cerrado hasta `completed`.

La invocación portable resuelve el dispatcher desde la instalación del plugin, no desde el proyecto consumidor:

```powershell
python "<plugin-root>/scripts/lks_sdd.py" implement "<project-root>" --increment INC-001 --dry-run
```
