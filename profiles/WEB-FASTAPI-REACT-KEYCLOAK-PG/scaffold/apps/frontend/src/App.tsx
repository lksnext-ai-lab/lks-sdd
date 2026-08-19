import { isAuthenticationConfigured } from "./auth";
import "./index.css";

export function App() {
  return (
    <main>
      <p className="eyebrow">LKS-SDD · Codex · perfil H0</p>
      <h1>Aplicación de referencia preparada para un incremento vertical</h1>
      <p>
        El scaffold aporta límites FastAPI y React, salud y readiness diferenciados,
        configuración OIDC y una base reproducible. El comportamiento de negocio se implementa
        únicamente desde requisitos y criterios confirmados.
      </p>
      <dl>
        <div>
          <dt>Identidad</dt>
          <dd>{isAuthenticationConfigured ? "OIDC configurado" : "OIDC pendiente de entorno"}</dd>
        </div>
        <div>
          <dt>Estado</dt>
          <dd>Scaffold listo</dd>
        </div>
      </dl>
    </main>
  );
}
