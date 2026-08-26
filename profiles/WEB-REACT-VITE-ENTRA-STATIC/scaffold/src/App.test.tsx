import "@testing-library/jest-dom/vitest";
import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { App } from "./App";
import { authConfiguration, type AuthEnvironment } from "./auth";

describe("App", () => {
  it("exposes an accessible product boundary", () => {
    render(<App />);
    expect(screen.getByRole("heading", { level: 1 })).toHaveTextContent(
      "Frontera de identidad preparada",
    );
  });

  it("oidc contract: rejects non tenant-specific authorities", () => {
    expect(() =>
      authConfiguration(environment({ VITE_ENTRA_TENANT_ID: "common" })),
    ).toThrow(/tenant-specific/);
    expect(() =>
      authConfiguration(environment({ VITE_ENTRA_TENANT_ID: "../common" })),
    ).toThrow(/tenant-specific/);
  });

  it("spa pkce: configures MSAL browser without an implicit flow", () => {
    const config = authConfiguration(environment());
    expect(config.msal.auth.authority).toContain(
      "/11111111-1111-1111-1111-111111111111",
    );
    expect(config.loginScopes).toEqual(["api://reference/api.read"]);
  });

  it("spa session: confines the MSAL cache to session storage", () => {
    expect(authConfiguration(environment()).msal.cache?.cacheLocation).toBe(
      "sessionStorage",
    );
  });

  it("entra tenant: preserves the confirmed tenant in the authority", () => {
    expect(authConfiguration(environment()).tenantId).toBe(
      "11111111-1111-1111-1111-111111111111",
    );
  });

  it("entra permissions: requires a delegated API scope", () => {
    expect(() =>
      authConfiguration(environment({ VITE_ENTRA_API_SCOPE: "" })),
    ).toThrow(/API scope/);
  });
});

function environment(
  overrides: Partial<AuthEnvironment> = {},
): AuthEnvironment {
  return {
    VITE_ENTRA_TENANT_ID: "11111111-1111-1111-1111-111111111111",
    VITE_ENTRA_CLIENT_ID: "22222222-2222-2222-2222-222222222222",
    VITE_ENTRA_REDIRECT_URI: "http://127.0.0.1:4173/auth/callback",
    VITE_ENTRA_POST_LOGOUT_URI: "http://127.0.0.1:4173/",
    VITE_ENTRA_API_SCOPE: "api://reference/api.read",
    ...overrides,
  };
}
