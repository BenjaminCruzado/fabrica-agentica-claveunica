import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";

const scope = JSON.parse(await readFile(new URL("../data/scope.json", import.meta.url), "utf8"));
const html = await readFile(new URL("../public/index.html", import.meta.url), "utf8");
const app = await readFile(new URL("../public/app.js", import.meta.url), "utf8");
const publicDataJs = await readFile(new URL("../public/data.js", import.meta.url), "utf8");

assert.equal(scope.screens.length, 30, "debe generar 30 pantallas navegables");
assert.ok(scope.counts.api_endpoints >= 40, "debe conservar 40 endpoints documentados");
assert.ok(scope.counts.tables >= 40, "debe conservar 40 tablas documentadas");
assert.match(html, /Portal Ciudadano ClaveUnica/);

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

console.log("smoke ok: app generada desde implementation-ledger, con layouts y requisitos no clonados");
