import { expect, test } from "@playwright/test";

test("real Microsoft Entra interoperability", async ({ browser }) => {
  const storageState = process.env.ENTRA_TEST_STORAGE_STATE;
  if (!storageState) throw new Error("ENTRA_TEST_STORAGE_STATE is required for the real interoperability gate");
  const sessionState = process.env.ENTRA_TEST_SESSION_STORAGE_JSON;
  if (!sessionState) throw new Error("ENTRA_TEST_SESSION_STORAGE_JSON is required for the real interoperability gate");
  const entries: unknown = JSON.parse(sessionState);
  if (!entries || typeof entries !== "object" || Array.isArray(entries)) {
    throw new Error("ENTRA_TEST_SESSION_STORAGE_JSON must contain a JSON object");
  }
  if (!Object.values(entries).every((value) => typeof value === "string")) {
    throw new Error("ENTRA_TEST_SESSION_STORAGE_JSON values must be strings");
  }
  const context = await browser.newContext({ storageState });
  await context.addInitScript((values: Record<string, string>) => {
    for (const [key, value] of Object.entries(values)) sessionStorage.setItem(key, value);
  }, entries as Record<string, string>);
  const page = await context.newPage();
  await page.goto("/");
  await expect(page.getByText("Sesión iniciada como")).toBeVisible();
  await context.close();
});
