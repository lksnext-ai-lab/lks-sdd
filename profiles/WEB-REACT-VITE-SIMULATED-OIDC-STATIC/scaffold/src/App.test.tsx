import "@testing-library/jest-dom/vitest";
import { render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { App } from "./App";
import { authConfiguration, bootstrapAuthentication, pkceChallenge } from "./auth";

const developmentEnvironment = {
  VITE_APP_ENV: "development",
  VITE_SIMULATED_OIDC_ISSUER: "http://127.0.0.1:8000/__test__/oidc",
};

describe("App", () => {
  beforeEach(() => sessionStorage.clear());

  it("exposes an accessible product boundary", () => {
    render(<App />);
    expect(screen.getByRole("heading", { level: 1 })).toHaveTextContent("Frontera de identidad simulada");
  });

  it("oidc contract: accepts loopback and HTTPS test issuers", () => {
    expect(authConfiguration(developmentEnvironment).issuer).toBe("http://127.0.0.1:8000/__test__/oidc");
    expect(authConfiguration({
      VITE_APP_ENV: "acceptance-preproduction",
      VITE_SIMULATED_OIDC_ISSUER: "https://identity.acceptance.example/__test__/oidc/",
    }).issuer).toBe("https://identity.acceptance.example/__test__/oidc");
  });

  it("spa pkce: produces the RFC 7636 S256 challenge", async () => {
    await expect(pkceChallenge(
      "dBjftJeZ4CVP-mB92K27uhbUJU1p1r_wW1gFWFOEjXk",
      crypto,
    )).resolves.toBe("E9Melhoa2OwvFrEMTJguCHaoeK1t8URWbuGJSstw-cM");
  });

  it("spa session: stores the synthetic session only in sessionStorage", async () => {
    const fetcher = vi.fn()
      .mockResolvedValueOnce(new Response(JSON.stringify({ code: "code-001" }), { status: 200 }))
      .mockResolvedValueOnce(new Response(JSON.stringify({ access_token: "token-001" }), { status: 200 }));
    const auth = await bootstrapAuthentication(developmentEnvironment, {
      fetcher: fetcher as unknown as typeof fetch,
      storage: sessionStorage,
      webCrypto: crypto,
    });
    await auth.signIn();
    expect(auth.username()).toBe("synthetic.user@example.invalid");
    await expect(auth.acquireApiToken()).resolves.toBe("token-001");
    expect(localStorage.length).toBe(0);
    await auth.signOut();
    expect(auth.username()).toBeNull();
  });

  it("simulated identity safety: fails closed for production", () => {
    expect(() => authConfiguration({
      ...developmentEnvironment,
      VITE_APP_ENV: "production",
    })).toThrow(/disabled outside explicit non-production environments/);
  });

  it.each(["", "staging", "preprod", "unknown"])(
    "simulated identity safety: rejects unapproved environment %s",
    (value) => {
      expect(() => authConfiguration({
        ...developmentEnvironment,
        VITE_APP_ENV: value,
      })).toThrow();
    },
  );

  it("simulated identity safety: requires explicit environment and issuer", () => {
    expect(() => authConfiguration({})).toThrow(/explicit non-production environment/);
    expect(() => authConfiguration({ VITE_APP_ENV: "development" })).toThrow(/simulated OIDC issuer/);
  });

  it.each([
    "http://identity.example/__test__/oidc",
    "https://identity.example/oidc",
    "https://user@identity.example/__test__/oidc",
    "https://identity.example/__test__/oidc?tenant=real",
    "https://identity.example/__test__/oidc#fragment",
    "https://identity.example/__test__/other/../oidc",
    "https://login.microsoftonline.com/tenant/v2.0",
    "https://identity.example/%5f%5ftest%5f%5f/oidc",
  ])("simulated identity safety: rejects ambiguous issuer %s", (issuer) => {
    expect(() => authConfiguration({
      ...developmentEnvironment,
      VITE_SIMULATED_OIDC_ISSUER: issuer,
    })).toThrow();
  });
});
