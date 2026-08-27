import { expect, test } from "@playwright/test";

test("simulated oidc integration: signs in through the controlled double", async ({ page }) => {
  await page.route("http://127.0.0.1:8000/__test__/oidc/authorize", async (route) => {
    const payload = route.request().postDataJSON() as Record<string, unknown>;
    expect(payload.code_challenge_method).toBe("S256");
    expect(String(payload.code_challenge)).toHaveLength(43);
    await route.fulfill({ json: { code: "synthetic-code" } });
  });
  await page.route("http://127.0.0.1:8000/__test__/oidc/token", async (route) => {
    const payload = route.request().postDataJSON() as Record<string, unknown>;
    expect(String(payload.code_verifier).length).toBeGreaterThanOrEqual(43);
    await route.fulfill({ json: { access_token: "synthetic-access-token" } });
  });
  await page.goto("/");
  await page.getByRole("button", { name: "Iniciar sesión" }).click();
  await expect(page.getByText("Sesión iniciada como")).toBeVisible();
});
