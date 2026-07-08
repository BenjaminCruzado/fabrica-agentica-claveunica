let data = window.APP_DATA;
let db = {};
const app = document.querySelector("#app");

async function loadState() {
  const response = await fetch("/api/v1/app-state");
  if (!response.ok) throw new Error("No se pudo cargar el estado del portal");
  data = await response.json();
  db = data.db || {};
}

function route() {
  return location.hash.replace("#", "") || "/dashboard";
}

function setRoute(next) {
  location.hash = next;
}

function rowsFor(screen) {
  return (db.screenRecords?.[screen.route] || screen.records || []).map((row) => Array.isArray(row) ? row : [row.a, row.b, row.c]);
}

function recentEvents(screen) {
  return (db.events || []).filter((event) => event.screen === screen.route || route() === "/dashboard").slice(0, 5);
}

async function runAction(screenRoute, action) {
  const response = await fetch("/api/v1/actions", {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({ screenRoute, action })
  });
  if (!response.ok) {
    alert("No se pudo completar la accion");
    return;
  }
  await loadState();
  render();
}

function groupedScreens() {
  return data.modules.map((module) => ({
    ...module,
    screens: data.screens.filter((screen) => screen.module === module.id)
  }));
}

function navGroup(module) {
  const current = route();
  return `
    <section class="nav-group">
      <strong>${module.name}</strong>
      ${module.screens.map((screen) => {
        const active = current === screen.route ? "active" : "";
        return `<a class="${active}" href="#${screen.route}"><span>${screen.title.replace(module.name + " - ", "")}</span><small>${screen.moduleName}</small></a>`;
      }).join("")}
    </section>
  `;
}

function dashboard() {
  const metrics = data.portalMetrics.map((item) => [item.label, item.value]);
  return `
    <section class="hero">
      <div>
        <h1>${data.name}</h1>
        <p>${data.objective}</p>
      </div>
      <div class="actions">
        <button onclick="setRoute('${data.screens[0].route}')">Entrar al portal</button>
        <button class="secondary" onclick="setRoute('/portal/catalog')">Buscar tramite</button>
      </div>
    </section>
    <section class="grid">
      ${metrics.map(([label, value]) => `<div class="card metric"><span class="muted">${label}</span><strong>${value ?? 0}</strong></div>`).join("")}
    </section>
    <section class="module-grid">
      ${data.modules.map((mod) => `
        <article class="card module-card" style="--accent:${mod.accent}">
          <span class="muted">${data.screens.filter((screen) => screen.module === mod.id).length} servicios disponibles</span>
          <h2>${mod.name}</h2>
          <p>${data.screens.find((screen) => screen.module === mod.id)?.summary || "Modulo disponible para gestion ciudadana."}</p>
          <button onclick="setRoute('${data.screens.find((screen) => screen.module === mod.id).route}')">${data.screens.find((screen) => screen.module === mod.id)?.actions?.[0] || "Abrir"}</button>
        </article>
      `).join("")}
    </section>
  `;
}

function recordTable(screen) {
  const rows = rowsFor(screen);
  return `
    <table>
      <thead><tr><th>${screen.fields[0]}</th><th>${screen.fields[1]}</th><th>${screen.fields[2]}</th></tr></thead>
      <tbody>
        ${rows.map((row) => `<tr><td>${row[0]}</td><td>${row[1]}</td><td>${row[2]}</td></tr>`).join("")}
      </tbody>
    </table>
  `;
}

function overviewPanel(screen) {
  const rows = rowsFor(screen);
  return `
    <section class="grid three">
      ${rows.map((row, index) => `
        <div class="card metric">
          <span class="muted">${row[0]}</span>
          <strong>${index === 0 ? "98%" : index === 1 ? "12" : "3"}</strong>
          <small>${row[1]} - ${row[2]}</small>
        </div>
      `).join("")}
    </section>
    <section class="card">${recordTable(screen)}</section>
  `;
}

function formPanel(screen) {
  const rows = rowsFor(screen);
  return `
    <section class="form-grid">
      <div class="card">
        <h2>${screen.actions[0] || "Gestionar"}</h2>
        ${screen.fields.map((field, index) => `<label>${field}<input value="${rows[index % rows.length]?.[0] || ""}" /></label>`).join("")}
        <label>Estado<select><option>Recibido</option><option>En revision</option><option>Aprobado</option><option>Observado</option></select></label>
        <button onclick="runAction('${screen.route}', '${screen.actions[0] || "Guardar"}')">${screen.actions[0] || "Guardar"}</button>
      </div>
      <div class="card">
        <h2>Guia de accion</h2>
        <p class="notice">Completa la informacion solicitada y revisa el estado antes de enviar.</p>
        <ul class="check-list">
          ${screen.actions.map((action) => `<li>${action}</li>`).join("")}
          <li>Revisar datos antes de confirmar</li>
          <li>Guardar comprobante de la operacion</li>
        </ul>
      </div>
    </section>
  `;
}

function reviewPanel(screen) {
  return `
    <section class="card">
      <div class="toolbar">
        <input placeholder="Buscar en ${screen.moduleName}" />
        <select><option>Todos</option><option>Pendientes</option><option>Criticos</option></select>
        <button onclick="runAction('${screen.route}', '${screen.actions[0] || "Actualizar"}')">${screen.actions[0] || "Actualizar"}</button>
      </div>
      ${recordTable(screen)}
    </section>
    <section class="timeline">
      <div><strong>Recepcion</strong><span>Evento creado y clasificado</span></div>
      <div><strong>Revision</strong><span>Reglas de negocio aplicadas</span></div>
      <div><strong>Cierre</strong><span>Respuesta disponible para el ciudadano</span></div>
    </section>
  `;
}

function moduleBody(screen) {
  const formLayouts = ["auth-login", "auth-recovery", "profile", "contact", "privacy", "mfa", "address-current", "address-verify", "notification-settings", "consent-request", "case-detail", "support-home", "ticket-detail", "audit-export"];
  const overviewLayouts = ["dashboard", "catalog", "service-detail", "integration-status", "compliance"];
  if (overviewLayouts.includes(screen.layout)) return overviewPanel(screen);
  if (formLayouts.includes(screen.layout)) return formPanel(screen);
  return reviewPanel(screen);
}

function screenView(screen) {
  const events = recentEvents(screen);
  return `
    <section class="card screen-header" style="--accent:${screen.accent}">
      <span class="muted">${screen.moduleName}</span>
      <h1>${screen.title}</h1>
      <p>${screen.summary}</p>
      <div class="status">${screen.states.map((item) => `<span class="pill">${item}</span>`).join("")}</div>
    </section>
    ${moduleBody(screen)}
    <section class="card">
      <h2>Actividad reciente</h2>
      <table>
        <thead><tr><th>Evento</th><th>Detalle</th><th>Fecha</th></tr></thead>
        <tbody>
          ${events.length ? events.map((event) => `<tr><td>${event.type}</td><td>${event.message}</td><td>${event.createdAt}</td></tr>`).join("") : `<tr><td>Sin actividad</td><td>Esta vista aun no registra acciones</td><td>-</td></tr>`}
        </tbody>
      </table>
    </section>
  `;
}

function render() {
  const current = route();
  const screen = data.screens.find((item) => item.route === current);
  app.innerHTML = `
    <div class="shell">
      <aside class="sidebar">
        <div class="brand">
          <strong>${data.name}</strong>
          <span>Portal ciudadano</span>
        </div>
        <nav class="nav">
          <a class="${current === "/dashboard" ? "active" : ""}" href="#/dashboard"><span>Dashboard</span><small>Resumen ejecutivo</small></a>
          ${groupedScreens().map(navGroup).join("")}
        </nav>
      </aside>
      <main class="main">
        <div class="topbar">
          <div><strong>Portal ciudadano</strong><div class="muted">Gestion de identidad, domicilio digital y notificaciones</div></div>
          <div class="status"><span class="pill">ClaveUnica simulada</span><span class="pill">DDU</span><span class="pill">Auditoria</span></div>
        </div>
        ${screen ? screenView(screen) : dashboard()}
      </main>
    </div>
  `;
}

async function init() {
  app.innerHTML = `<main class="main"><section class="card"><h1>Cargando portal</h1><p>Conectando con la base local y la API.</p></section></main>`;
  try {
    await loadState();
    render();
  } catch (error) {
    app.innerHTML = `<main class="main"><section class="card"><h1>No se pudo cargar el portal</h1><p>${error.message}</p></section></main>`;
  }
}

window.addEventListener("hashchange", render);
init();
