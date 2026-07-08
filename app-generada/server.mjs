import { createServer } from "node:http";
import { copyFile, readFile, writeFile } from "node:fs/promises";
import { existsSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const publicDir = path.join(__dirname, "public");
const appData = JSON.parse(await readFile(path.join(__dirname, "data", "scope.json"), "utf8"));
const publicState = JSON.parse(await readFile(path.join(__dirname, "data", "public-state.json"), "utf8"));
const dbPath = path.join(__dirname, "data", "app-db.json");
const seedPath = path.join(__dirname, "data", "app-db.seed.json");
const port = Number(process.env.PORT || 3000);

if (!existsSync(dbPath)) {
  await copyFile(seedPath, dbPath);
}

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

async function bodyJson(req) {
  let raw = "";
  for await (const chunk of req) raw += chunk;
  if (!raw.trim()) return {};
  return JSON.parse(raw);
}

async function loadDb() {
  return JSON.parse(await readFile(dbPath, "utf8"));
}

async function saveDb(db) {
  await writeFile(dbPath, JSON.stringify(db, null, 2) + "\n", "utf8");
}

function metrics(db) {
  return [
    { label: "Tramites activos", value: db.procedures.filter((item) => item.status !== "completado").length },
    { label: "Mensajes nuevos", value: db.notifications.filter((item) => !item.read).length },
    { label: "Sesiones protegidas", value: db.sessions.filter((item) => item.active).length },
    { label: "Autorizaciones vigentes", value: db.consents.filter((item) => item.status === "vigente").length },
    { label: "Expedientes en curso", value: db.cases.filter((item) => item.status !== "cerrado").length },
    { label: "Alertas pendientes", value: db.events.filter((item) => item.type !== "resolved").length }
  ];
}

function screenRecords(db, route) {
  return db.screenRecords[route] || [];
}

function nextId(prefix, collection) {
  return `${prefix}-${String(collection.length + 1).padStart(3, "0")}`;
}

function applyAction(db, payload) {
  const screenRoute = String(payload.screenRoute || "");
  const action = String(payload.action || "Actualizar");
  const event = {
    id: nextId("EVT", db.events),
    type: "user_action",
    screen: screenRoute,
    message: `${action} ejecutado`,
    createdAt: new Date().toISOString()
  };

  if (action.includes("Marcar leida")) {
    const item = db.notifications.find((notification) => !notification.read);
    if (item) item.read = true;
  } else if (action.includes("Cerrar sesion")) {
    const item = db.sessions.find((session) => session.active && !session.trusted) || db.sessions.find((session) => session.active);
    if (item) item.active = false;
  } else if (action.includes("Revocar")) {
    const item = db.consents.find((consent) => consent.status !== "revocada");
    if (item) item.status = "revocada";
  } else if (action.includes("Crear ticket")) {
    db.tickets.push({ id: nextId("TK", db.tickets), topic: "Solicitud ciudadana", status: "abierto", updatedAt: "ahora" });
  } else if (action.includes("Iniciar") || action.includes("Continuar") || action.includes("Abrir tramite")) {
    db.procedures.push({ id: nextId("TRA", db.procedures), name: "Solicitud iniciada desde portal", status: "en curso", owner: "Portal ciudadano", updatedAt: "ahora" });
  }

  db.events.unshift(event);
  return event;
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
    if (url.pathname === "/api/v1/app-state") {
      const db = await loadDb();
      return json(res, 200, { ...publicState, portalMetrics: metrics(db), db });
    }
    if (url.pathname === "/api/v1/screens") return json(res, 200, { screens: publicState.screens });
    if (url.pathname.startsWith("/api/v1/screens/")) {
      const db = await loadDb();
      const route = "/" + decodeURIComponent(url.pathname.replace("/api/v1/screens/", ""));
      const screen = publicState.screens.find((item) => item.route === route);
      if (!screen) return json(res, 404, { error: "screen_not_found" });
      return json(res, 200, { screen, records: screenRecords(db, route), events: db.events.filter((item) => item.screen === route).slice(0, 5) });
    }
    if (url.pathname === "/api/v1/actions" && req.method === "POST") {
      const db = await loadDb();
      const payload = await bodyJson(req);
      const event = applyAction(db, payload);
      await saveDb(db);
      return json(res, 200, { status: "ok", event, portalMetrics: metrics(db), db });
    }
    return staticFile(req, res);
  } catch (error) {
    return json(res, 500, { error: "internal_error", detail: String(error.message || error) });
  }
}).listen(port, "0.0.0.0", () => {
  console.log(`Portal Ciudadano ClaveUnica escuchando en http://0.0.0.0:${port}`);
});
