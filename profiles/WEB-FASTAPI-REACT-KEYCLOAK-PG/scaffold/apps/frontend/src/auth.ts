import Keycloak from "keycloak-js";

export const authConfiguration = {
  url: import.meta.env.VITE_OIDC_URL ?? "",
  realm: import.meta.env.VITE_OIDC_REALM ?? "",
  clientId: import.meta.env.VITE_OIDC_CLIENT_ID ?? "",
};

export const isAuthenticationConfigured = Object.values(authConfiguration).every(Boolean);

export function createIdentityClient(): Keycloak {
  if (!isAuthenticationConfigured) {
    throw new Error("OIDC configuration is incomplete");
  }
  return new Keycloak(authConfiguration);
}
