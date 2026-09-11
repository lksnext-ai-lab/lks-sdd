# Perfil WEB-REACT-VITE-STATIC

SPA React + TypeScript construida con Vite y publicada como bundle estático. No incorpora backend, identidad, base de datos ni runtime servidor implícitos.

## Condiciones

- La selección exige una ADR confirmada y un `BIND-###` asociado a una `UNIT-###`.
- Configuración build-time y runtime, fallback de rutas, navegadores, almacenamiento local y monitorización se deciden por proyecto.
- El mismo artefacto inmutable se promociona entre entornos siempre que el contrato de configuración lo permita.
- Lint, tipos, unitarias, build, navegador y accesibilidad son gates obligatorios; G4 exige evidencia externa de promoción, smoke, observabilidad y recuperación.
