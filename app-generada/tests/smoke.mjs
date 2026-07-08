import assert from "node:assert/strict";
import { copyFile, readFile } from "node:fs/promises";
import { spawn } from "node:child_process";

const scope = JSON.parse(await readFile(new URL("../data/scope.json", import.meta.url), "utf8"));
const seedDb = JSON.parse(await readFile(new URL("../data/app-db.seed.json", import.meta.url), "utf8"));
const html = await readFile(new URL("../public/index.html", import.meta.url), "utf8");
const app = await readFile(new URL("../public/app.js", import.meta.url), "utf8");
const publicDataJs = await readFile(new URL("../public/data.js", import.meta.url), "utf8");
const schema = await readFile(new URL("../data/schema.sql", import.meta.url), "utf8");

assert.equal(scope.screens.length, 30, "debe generar 30 pantallas navegables");
assert.ok(scope.counts.api_endpoints >= 40, "debe conservar 40 endpoints documentados");
assert.ok(scope.counts.tables >= 40, "debe conservar 40 tablas documentadas");
assert.match(html, /Portal Ciudadano ClaveUnica/);
assert.match(schema, /CREATE TABLE citizens/);
assert.match(schema, /CREATE TABLE procedures/);
assert.ok(seedDb.procedures.length >= 3, "la app debe tener datos de dominio iniciales");
assert.ok(seedDb.notifications.length >= 3, "la app debe integrar notificaciones en la base local");

const uniqueSummaries = new Set(scope.screens.map((screen) => screen.summary));
const uniqueLayouts = new Set(scope.screens.map((screen) => screen.layout));
const uniqueFingerprints = new Set(scope.screens.map((screen) => screen.fingerprint));
const requirementIds = scope.requirements.map((item) => item.id);

assert.ok(uniqueSummaries.size >= 28, "las pantallas no deben compartir el mismo resumen generico");
assert.ok(uniqueLayouts.size >= 24, "debe haber layouts derivados de requisitos, no tres plantillas rotativas");
assert.ok(uniqueFingerprints.size >= 30, "debe haber variedad estructural entre pantallas");
assert.equal(scope.requirements.length, 90, "cada pantalla debe generar requisitos UI, flujo y validacion");
assert.equal(requirementIds.length, new Set(requirementIds).size, "los requisitos del ledger deben ser unicos");
assert.equal(scope.apiCatalog.endpoint_count, 40, "el catalogo API debe conservar 40 endpoints");
assert.match(app, /function overviewPanel/);
assert.match(app, /function formPanel/);
assert.match(app, /function reviewPanel/);
assert.match(app, /fetch\("\/api\/v1\/app-state"\)/);
assert.match(app, /fetch\("\/api\/v1\/actions"/);
for (const forbiddenLabel of [
  "Contrato y trazabilidad",
  "Endpoint mock",
  "Fingerprint UI",
  "Validaciones de la vista",
  "REQ_UI_",
  "REQ_FLOW_",
  "REQ_VAL_",
  "trazabilidad de fabrica",
  "Flujo simulado por la fabrica"
]) {
  assert.doesNotMatch(app, new RegExp(forbiddenLabel), `la UI publica no debe exponer ${forbiddenLabel}`);
  assert.doesNotMatch(publicDataJs, new RegExp(forbiddenLabel), `los datos publicos no deben exponer ${forbiddenLabel}`);
}
assert.doesNotMatch(app, /data\.screens\.map\(navItem\)/, "no debe renderizar 30 pestañas planas con una sola plantilla");

const port = "3197";
await copyFile(new URL("../data/app-db.seed.json", import.meta.url), new URL("../data/app-db.json", import.meta.url));
const child = spawn(process.execPath, ["server.mjs"], {
  cwd: new URL("..", import.meta.url),
  env: { ...process.env, PORT: port },
  stdio: "ignore"
});

async function waitForServer() {
  for (let attempt = 0; attempt < 30; attempt += 1) {
    try {
      const response = await fetch(`http://127.0.0.1:${port}/api/v1/health`);
      if (response.ok) return;
    } catch {}
    await new Promise((resolve) => setTimeout(resolve, 100));
  }
  throw new Error("servidor no inicio para smoke test");
}

try {
  await waitForServer();
  const before = await (await fetch(`http://127.0.0.1:${port}/api/v1/app-state`)).json();
  const unreadBefore = before.db.notifications.filter((item) => !item.read).length;
  const eventCountBefore = before.db.events.length;
  const actionResponse = await fetch(`http://127.0.0.1:${port}/api/v1/actions`, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({ screenRoute: "/notificaciones/inbox", action: "Marcar leida" })
  });
  assert.equal(actionResponse.ok, true, "la API de acciones debe responder ok");
  const after = await (await fetch(`http://127.0.0.1:${port}/api/v1/app-state`)).json();
  const unreadAfter = after.db.notifications.filter((item) => !item.read).length;
  assert.equal(after.db.events.length, eventCountBefore + 1, "la accion debe persistir evento");
  assert.equal(unreadAfter, Math.max(0, unreadBefore - 1), "la accion debe cambiar estado de notificaciones");
} finally {
  child.kill();
  await copyFile(new URL("../data/app-db.seed.json", import.meta.url), new URL("../data/app-db.json", import.meta.url));
}

console.log("smoke ok: app integrada con base local, API, acciones persistentes y evidencia separada");
