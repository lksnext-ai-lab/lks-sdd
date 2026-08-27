/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_APP_ENV?: string;
  readonly VITE_SIMULATED_OIDC_ISSUER?: string;
  readonly VITE_OIDC_AUDIENCE?: string;
  readonly VITE_SIMULATED_SUBJECT?: string;
  readonly VITE_SIMULATED_OBJECT_ID?: string;
  readonly VITE_SIMULATED_USERNAME?: string;
}
