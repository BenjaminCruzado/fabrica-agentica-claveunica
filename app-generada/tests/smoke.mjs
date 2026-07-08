import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";

const scope = JSON.parse(await readFile(new URL("../data/scope.json", import.meta.url), "utf8"));
const html = await readFile(new URL("../public/index.html", import.meta.url), "utf8");
const app = await readFile(new URL("../public/app.js", import.meta.url), "utf8");

assert.equal(scope.screens.length, 30, "debe generar 30 pantallas navegables");
assert.ok(scope.counts.api_endpoints >= 40, "debe conservar 40 endpoints documentados");
assert.ok(scope.counts.tables >= 40, "debe conservar 40 tablas documentadas");
assert.match(html, /Portal Ciudadano ClaveUnica/);

const uniqueSummaries = new Set(scope.screens.map((screen) => screen.summary));
const uniqueComponents = new Set(scope.screens.map((screen) => screen.component));
const uniqueFingerprints = new Set(scope.screens.map((screen) => screen.fingerprint));
const variants = new Set(scope.screens.map((screen) => screen.variant));

assert.ok(uniqueSummaries.size >= 10, "las pantallas no deben compartir el mismo resumen generico");
assert.ok(uniqueComponents.size >= 8, "debe haber componentes por modulo, no una sola plantilla");
assert.ok(uniqueFingerprints.size >= 24, "debe haber variedad estructural entre pantallas");
assert.deepEqual([...variants].sort(), ["form", "overview", "review"], "debe cubrir resumen, gestion y revision");
assert.match(app, /function overviewPanel/);
assert.match(app, /function formPanel/);
assert.match(app, /function reviewPanel/);
assert.doesNotMatch(app, /data\.screens\.map\(navItem\)/, "no debe renderizar 30 pestañas planas con una sola plantilla");

console.log("smoke ok: app generada cumple conteos, variedad visual y pantallas no clonadas");
