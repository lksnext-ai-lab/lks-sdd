import { useState } from "react";
import type { AuthController } from "./auth";

type AppProps = {
  auth?: AuthController;
  configurationError?: string;
};

export function App({ auth, configurationError }: AppProps) {
  const [username, setUsername] = useState(auth?.username() ?? null);

  async function signIn() {
    await auth?.signIn();
    setUsername(auth?.username() ?? null);
  }

  async function signOut() {
    await auth?.signOut();
    setUsername(null);
  }

  return (
    <main>
      <p className="eyebrow">LKS-SDD · perfil React + Microsoft Entra</p>
      <h1>Frontera de identidad preparada</h1>
      <p>Authorization Code con PKCE, tenant y scopes se mantienen como contrato explícito.</p>
      <section aria-labelledby="status-title">
        <h2 id="status-title">Estado</h2>
        {configurationError ? (
          <p role="alert">Configuración pendiente: {configurationError}</p>
        ) : username ? (
          <>
            <p>Sesión iniciada como <strong>{username}</strong>.</p>
            <button type="button" onClick={() => void signOut()}>Cerrar sesión</button>
          </>
        ) : (
          <>
            <p>Sesión no iniciada.</p>
            <button type="button" onClick={() => void signIn()} disabled={!auth}>Iniciar sesión</button>
          </>
        )}
      </section>
    </main>
  );
}
