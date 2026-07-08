import { createServer } from "node:http";
import { readFile } from "node:fs/promises";
import { existsSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const publicDir = path.join(__dirname, "public");
const appData = JSON.parse(await readFile(path.join(__dirname, "data", "scope.json"), "utf8"));
const port = Number(process.env.PORT || 3000);

const types = {
  ".html": "text/html; charset=utf-8",
  ".css": "text/css; charset=utf-8",
  ".js": "text/javascript; charset=utf-8",
  ".json": "application/json; charset=utf-8",
  ".svg": "image/svg+xml; charset=utf-8"
};

function json(res, status, payload) {
  res.writeHead(status, { "content-type": "application/json; charset=utf-8", "cache-control": "no-store" });
  res.end(JSON.stringify(payload, null, 2));
}

async function staticFile(req, res) {
  const url = new URL(req.url || "/", "http://localhost");
  const requested = url.pathname === "/" ? "/index.html" : url.pathname;
  const target = path.normalize(path.join(publicDir, requested));
  if (!target.startsWith(publicDir)) return json(res, 403, { error: "forbidden" });
  const file = existsSync(target) ? target : path.join(publicDir, "index.html");
  const ext = path.extname(file);
  const body = await readFile(file);
  res.writeHead(200, { "content-type": types[ext] || "application/octet-stream" });
  res.end(body);
}

createServer(async (req, res) => {
  try {
    const url = new URL(req.url || "/", "http://localhost");
    if (url.pathname === "/api/v1/health") return json(res, 200, { status: "ok", service: appData.name });
    if (url.pathname === "/api/v1/scope") return json(res, 200, appData);
    if (url.pathname === "/api/v1/screens") return json(res, 200, { screens: appData.screens });
    if (url.pathname.startsWith("/api/v1/")) {
      return json(res, 200, {
        status: "mock",
        path: url.pathname,
        message: "Endpoint de demostracion del portal ciudadano.",
        user: appData.mockUser.name
      });
    }
    return staticFile(req, res);
  } catch (error) {
    return json(res, 500, { error: "internal_error", detail: String(error.message || error) });
  }
}).listen(port, "0.0.0.0", () => {
  console.log(`Portal Ciudadano ClaveUnica escuchando en http://0.0.0.0:${port}`);
});
