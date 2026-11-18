import http from "node:http";

let refreshAttempts = 0;
const server = http.createServer(async (request, response) => {
  const chunks = [];
  for await (const chunk of request) chunks.push(chunk);
  const body = Buffer.concat(chunks).toString("utf8");
  const send = (status, data) => {
    response.writeHead(status, { "Content-Type": "application/json", "Cache-Control": "no-store" });
    response.end(data === null ? "" : JSON.stringify(data));
  };

  if (request.url === "/health") return send(200, { ok: true });
  if (request.url === "/__reset") {
    refreshAttempts = 0;
    return send(200, { ok: true });
  }
  if (request.url === "/api/v1/auth/login/") {
    return send(200, {
      status: "authenticated",
      access: "access-login",
      refresh: "refresh-login",
      user: { id: "qa-user", email: "qa@example.test" },
    });
  }
  if (request.url === "/api/v1/auth/token/refresh/") {
    refreshAttempts += 1;
    const attempt = refreshAttempts;
    await new Promise(resolve => setTimeout(resolve, 250));
    if (attempt === 1) return send(200, { access: "access-rotated", refresh: "refresh-rotated" });
    return send(401, { detail: "Refresh token already rotated." });
  }
  if (request.url === "/api/v1/auth/me/") {
    if (request.headers.authorization === "Bearer access-rotated") {
      return send(200, { id: "qa-user", email: "qa@example.test" });
    }
    return send(401, { detail: "Expired access token." });
  }
  return send(404, { detail: "Not found." });
});

server.listen(4010, "127.0.0.1");
