import { expect, test } from "@playwright/test";

const origin = "http://localhost:3000";
const bff = origin + "/api/bff";

test.beforeEach(async ({ request }) => {
  await request.get("http://127.0.0.1:4010/__reset");
});

test("login keeps tokens out of JSON and sets HttpOnly Strict cookies", async ({ page, context }) => {
  await page.goto("/login");
  const response = await page.request.post(bff + "/auth/login/", {
    headers: { Origin: origin },
    data: { email: "qa@example.test", password: "not-a-real-password" },
  });

  expect(response.status()).toBe(200);
  const body = await response.json();
  expect(body).not.toHaveProperty("access");
  expect(body).not.toHaveProperty("refresh");

  const cookies = await context.cookies(origin);
  const access = cookies.find(cookie => cookie.name === "estate_access");
  const refresh = cookies.find(cookie => cookie.name === "estate_refresh");
  expect(access).toBeTruthy();
  expect(refresh).toBeTruthy();
  for (const cookie of [access!, refresh!]) {
    expect(cookie.httpOnly).toBe(true);
    expect(cookie.secure).toBe(true);
    expect(cookie.sameSite).toBe("Strict");
    expect(cookie.path).toBe("/api/bff");
  }
});

test("rejects state-changing requests with a foreign Origin", async ({ request }) => {
  const response = await request.post(bff + "/auth/login/", {
    headers: { Origin: "https://attacker.example" },
    data: { email: "qa@example.test", password: "invalid" },
  });
  expect(response.status()).toBe(403);
  expect(await response.json()).toMatchObject({ detail: "Cross-origin request rejected." });
});

test("concurrent expired-session requests preserve the winning rotated cookies", async ({ page, context }) => {
  await page.goto("/login");
  await context.addCookies([
    { name: "estate_access", value: "access-expired", url: origin, path: "/api/bff", httpOnly: true, secure: true, sameSite: "Strict" },
    { name: "estate_refresh", value: "refresh-shared", url: origin, path: "/api/bff", httpOnly: true, secure: true, sameSite: "Strict" },
  ]);

  const responses = await Promise.all([
    page.request.get(bff + "/auth/me/", { headers: { Origin: origin } }),
    page.request.get(bff + "/auth/me/", { headers: { Origin: origin } }),
  ]);
  expect(responses.map(response => response.status()).sort()).toEqual([200, 409]);

  const winner = responses.find(response => response.status() === 200)!;
  const loser = responses.find(response => response.status() === 409)!;
  const winnerCookies = winner.headers()["set-cookie"] || "";
  const loserCookies = loser.headers()["set-cookie"] || "";
  expect(winnerCookies).toContain("estate_access=access-rotated");
  expect(winnerCookies).toContain("estate_refresh=refresh-rotated");
  expect(loserCookies).not.toContain("estate_access=");
  expect(loserCookies).not.toContain("estate_refresh=");
  expect((await loser.json()).detail).toContain("Retry shortly");

  const cookies = await context.cookies(origin);
  expect(cookies.find(cookie => cookie.name === "estate_access")?.value).toBe("access-rotated");
  expect(cookies.find(cookie => cookie.name === "estate_refresh")?.value).toBe("refresh-rotated");
});
