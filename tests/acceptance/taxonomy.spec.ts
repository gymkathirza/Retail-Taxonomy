import { expect, test } from "@playwright/test";

const API = process.env.PLAYWRIGHT_API_URL || "http://127.0.0.1:8000";
const unique = `ShipZone-${Date.now()}`;
const renamed = `${unique}-Updated`;

test.describe("Taxonomy acceptance", () => {
  test("login → browse → create → update → retire → restore → verify via API", async ({
    page,
    request,
  }) => {
    await page.goto("/");
    await expect(page.getByRole("heading", { name: "Retail Taxonomy" })).toBeVisible();
    await page.getByLabel("Username").fill("admin");
    await page.getByLabel("Password").fill("password");
    await page.getByRole("button", { name: "Sign in" }).click();
    await expect(page.getByLabel(/show inactive/i)).toBeVisible({ timeout: 30_000 });

    await page.getByLabel("Name").fill(unique);
    await page.getByRole("button", { name: "Create zone" }).click();
    await expect(page.getByRole("button", { name: unique })).toBeVisible({
      timeout: 15_000,
    });

    await page.getByRole("button", { name: unique }).click();
    await page.getByLabel("Name").fill(renamed);
    await page.getByRole("button", { name: "Save" }).click();
    await expect(page.getByRole("button", { name: renamed })).toBeVisible({
      timeout: 15_000,
    });

    page.once("dialog", (dialog) => dialog.accept());
    await page.getByRole("button", { name: renamed }).click();
    await page.getByRole("button", { name: "Retire" }).click();
    await expect(page.getByRole("button", { name: renamed })).toHaveCount(0, {
      timeout: 15_000,
    });

    await page.getByLabel(/show inactive/i).check();
    await expect(page.getByRole("button", { name: `${renamed} (inactive)` })).toBeVisible({
      timeout: 15_000,
    });
    await page.getByRole("button", { name: `${renamed} (inactive)` }).click();
    await page.getByRole("button", { name: "Restore" }).click();
    await expect(page.getByRole("button", { name: renamed, exact: true })).toBeVisible({
      timeout: 15_000,
    });

    const list = await request.get(`${API}/api/v1/zones`, {
      headers: {
        Authorization: `Basic ${Buffer.from("admin:password").toString("base64")}`,
      },
    });
    expect(list.ok()).toBeTruthy();
    const body = await list.json();
    const match = (body.items as { name: string; is_active: boolean }[]).find(
      (z) => z.name === renamed,
    );
    expect(match?.is_active).toBe(true);
  });
});
