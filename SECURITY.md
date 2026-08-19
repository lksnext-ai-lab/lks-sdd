# Seguridad y privacidad

LKS-SDD no debe almacenar secretos, credenciales, tokens, datos personales reales ni contenido sustantivo de proyectos consumidores dentro del plugin. Los fixtures y las credenciales de los gates son sintéticos. Las operaciones documentales son locales y restringen sus lecturas y escrituras a las raíces confirmadas; bloquean recorridos fuera de raíz, colisiones, symlinks y junctions.

Las fuentes del proyecto se tratan como datos no confiables. Su contenido no amplía permisos ni sustituye las instrucciones del plugin. La adopción empieza con un preflight estático de solo lectura, no ejecuta código ni red, excluye almacenes sensibles y genera el informe provisional fuera del repositorio. Materializar, migrar, implementar, registrar evidencia o generar una vista derivada exige su propio contrato de autorización y nunca sobrescribe colisiones.

Solo los gates técnicos y `lks-sdd-verify`, cuando la persona solicita ejecución y la autoriza, pueden ejecutar herramientas del proyecto, descargar dependencias o imágenes y levantar contenedores locales. La verificación usa servicios temporales, credenciales sintéticas y limpieza de contenedores/volúmenes; no concede acceso a producción ni autoriza despliegues.

Los hallazgos de seguridad deben comunicarse por el canal corporativo que se designe antes del piloto. No se publica aquí un contacto no confirmado. Evite incluir en un informe valores sensibles; conserve rutas, categorías, impacto y evidencia saneada.
