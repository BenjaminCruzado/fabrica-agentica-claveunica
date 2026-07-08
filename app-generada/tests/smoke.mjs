import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";

const scope = JSON.parse(await readFile(new URL("../data/scope.json", import.meta.url), "utf8"));
const html = await readFile(new URL("../public/index.html", import.meta.url), "utf8");

assert.equal(scope.screens.length, 30, "debe generar 30 pantallas navegables");
assert.ok(scope.counts.api_endpoints >= 40, "debe conservar 40 endpoints documentados");
assert.ok(scope.counts.tables >= 40, "debe conservar 40 tablas documentadas");
assert.match(html, /Portal Ciudadano ClaveUnica/);

console.log("smoke ok: app generada cumple conteos minimos y tiene shell web");
