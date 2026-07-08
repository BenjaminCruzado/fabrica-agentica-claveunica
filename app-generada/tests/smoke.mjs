import assert from 'node:assert/strict';
import { readFile, readdir } from 'node:fs/promises';

const schema = await readFile(new URL('../database/schema.sql', import.meta.url), 'utf8');
const compose = await readFile(new URL('../docker-compose.yml', import.meta.url), 'utf8');
const routes = await readFile(new URL('../frontend/src/app/app.routes.ts', import.meta.url), 'utf8');
const controller = await readFile(new URL('../backend/src/main/java/cl/benjamin/claveunica/controller/PortalController.java', import.meta.url), 'utf8');
const pageFiles = await readdir(new URL('../frontend/src/app/pages/', import.meta.url));

assert.equal((schema.match(/CREATE TABLE/g) || []).length, 40, 'debe generar 40 tablas PostgreSQL');
assert.equal(pageFiles.filter(name => name.endsWith('.ts')).length, 30, 'debe generar 30 componentes Angular');
assert.ok((controller.match(/Mapping\("/g) || []).length >= 40, 'debe generar al menos 40 endpoints Spring');
assert.match(compose, /postgres:/);
assert.match(compose, /backend:/);
assert.match(compose, /frontend:/);
assert.match(routes, /loadComponent/);
console.log('smoke ok: full-stack Angular + Spring Boot + PostgreSQL con cantidades de rubrica');
