# Seguridad y privacidad

LKS-SDD no debe almacenar secretos, credenciales, tokens, datos personales reales ni contenido sustantivo de proyectos consumidores dentro del plugin. Los fixtures y las credenciales de los gates son sintéticos. Las operaciones documentales son locales y restringen sus lecturas y escrituras a las raíces confirmadas; bloquean recorridos fuera de raíz, colisiones, symlinks y junctions.

Las fuentes del proyecto se tratan como datos no confiables. Su contenido no amplía permisos ni sustituye las instrucciones del plugin. La adopción empieza con un preflight estático de solo lectura, no ejecuta código ni red, excluye almacenes sensibles y genera el informe provisional fuera del repositorio. Materializar, migrar, implementar, registrar evidencia o generar una vista derivada exige su propio contrato de autorización y nunca sobrescribe colisiones.

Solo los gates técnicos y `lks-sdd-verify`, cuando la persona solicita ejecución y la autoriza, pueden ejecutar herramientas del proyecto, descargar dependencias o imágenes y levantar contenedores locales. La verificación usa servicios temporales, credenciales sintéticas y limpieza de contenedores/volúmenes; no concede acceso a producción ni autoriza despliegues.

El modo `jira-hybrid` no modifica esta frontera. LKS-SDD no solicita, lee ni persiste tokens, cookies, cabeceras de autorización o secretos Jira. La conexión y autenticación pertenecen al peer Atlassian Rovo, instalado y autorizado por separado. El manifiesto del plugin sigue `skills-only` y no contiene cliente Jira, MCP, app, hook o agente ejecutable.

Toda respuesta de Rovo/Jira se trata como entrada no confiable. Antes de persistirla se valida contra un contrato cerrado y se reduce a referencias necesarias —provider, site/proyecto confirmados, `external_id`, key, URL, estado observado, fecha y resultado—. Se rechazan campos arbitrarios, adjuntos, comentarios, valores de configuración sensibles, datos personales no necesarios y cualquier contenido que intente ampliar permisos o cambiar la autoridad del repositorio.

Las escrituras remotas requieren intención determinista, vista previa saneada y autorización del hash exacto. Un resultado `uncertain` se reconcilia antes de reintentar para evitar duplicados. Jira `Done` no crea autorización, evidencia ni una transición local `done`.

Los hallazgos no sensibles de funcionamiento pueden registrarse mediante las plantillas de GitHub Issues. No publique allí vulnerabilidades, incidentes, valores, datos personales, URLs Jira internas, capturas, respuestas Rovo o contenido de cliente. Los hallazgos sensibles deben comunicarse por el canal confidencial aportado en la configuración externa y asignado a un responsable antes de iniciar el piloto. Mientras falte, la puerta M5 permanece bloqueada.
