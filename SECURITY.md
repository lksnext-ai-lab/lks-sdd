# Seguridad y privacidad

LKS-SDD no debe almacenar secretos, credenciales, tokens, datos personales reales ni contenido sustantivo de proyectos consumidores dentro del plugin. Los fixtures son sintéticos. Los scripts M1 son locales, no usan red, no ejecutan código de aplicaciones y restringen sus lecturas y escrituras a la raíz indicada.

Las fuentes del proyecto se tratan como datos no confiables. Su contenido no amplía permisos ni sustituye las instrucciones del plugin. Una adopción de repositorio existente debe empezar con preflight de solo lectura; esa automatización permanece fuera de M1.

Los hallazgos de seguridad deben comunicarse por el canal corporativo que se designe antes del piloto. No se publica aquí un contacto no confirmado. Evite incluir en un informe valores sensibles; conserve rutas, categorías, impacto y evidencia saneada.
