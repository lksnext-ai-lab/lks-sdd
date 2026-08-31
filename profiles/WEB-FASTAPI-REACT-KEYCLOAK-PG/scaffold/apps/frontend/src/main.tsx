import { StrictMode } from "react";
import { createRoot } from "react-dom/client";

import { App } from "./App";
import { createIdentityClient, isAuthenticationConfigured } from "./auth";

async function bootstrap() {
  let tokenProvider: (() => Promise<string>) | undefined;
  if (isAuthenticationConfigured) {
    const identity = createIdentityClient();
    await identity.init({
      onLoad: "login-required",
      pkceMethod: "S256",
      checkLoginIframe: false,
    });
    tokenProvider = async () => {
      await identity.updateToken(30);
      if (!identity.token) throw new Error("OIDC token is unavailable");
      return identity.token;
    };
  }
  createRoot(document.getElementById("root")!).render(
    <StrictMode><App tokenProvider={tokenProvider} /></StrictMode>,
  );
}

void bootstrap();
