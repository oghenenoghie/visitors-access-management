import { expect, test } from "@playwright/test";

test.beforeEach(async ({ request }) => {
  await request.get("http://127.0.0.1:4010/__reset");
});

test("login keeps tokens out of JSON and sets HttpOnly Strict cookies", async ({ page, context }) => {
  await page.goto("/login");
  const response = await page.evaluate(async () => {
    const result = await fetch("/api/bff/auth/login/", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email: "qa@example.test", password: "not-a-real-password" }),
    });
    return { status: result.status, body: await result.json() };
  });

  expect(response.status).toBe(200);
  expect(response.body).not.toHaveProperty("access");
  expect(response.body).not.toHaveProperty("refresh");

  const cookies = await context.cookies();
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
  const response = await request.post("http://localhost:3000/api/bff/auth/login/", {
    headers: { Origin: "https://attacker.example" },
    data: { email: "qa@example.test", password: "invalid" },
  });
  expect(response.status()).toBe(403);
  expect(await response.json()).toMatchObject({ detail: "Cross-origin request rejected." });
});

test("concurrent expired-session requests preserve the winning rotated cookies", async ({ page, context }) => {
  await page.goto("/login");
  await context.addCookies([
    { name: "estate_access", value: "access-expired", domain: "localhost", path: "/api/bff", httpOnly: true, secure: true, sameSite: "Strict" },
    { name: "estate_refresh", value: "refresh-shared", domain: "localhost", path: "/api/bff", httpOnly: true, secure: true, sameSite: "Strict" },
  ]);

  const results = await page.evaluate(async () => {
    const responses = await Promise.all([
      fetch("/api/bff/auth/me/", { credentials: "same-origin", cache: "no-store" }),
      fetch("/api/bff/auth/me/", { credentials: "same-origin", cache: "no-store" }),
    ]);
    return Promise.all(responses.map(async response => ({
      status: response.status,
      body: await response.json(),
      setCookie: response.headers.get("set-cookie"),
    })));
  });

  expect(results.map(result => result.status).sort()).toEqual([200, 409]);
  const winner = results.find(result => result.status === 200)!;
  const loser = results.find(result => result.status === 409)!;
  expect(winner.setCookie).toContain("estate_access=access-rotated");
  expect(winner.setCookie).toContain("estate_refresh=refresh-rotated");
  expect(loser.setCookie).toBeNull();
  expect(loser.body.detail).toContain("Retry shortly");

  const cookies = await context.cookies();
  expect(cookies.find(cookie => cookie.name === "estate_access")?.value).toBe("access-rotated");
  expect(cookies.find(cookie => cookie.name === "estate_refresh")?.value).toBe("refresh-rotated");
});
