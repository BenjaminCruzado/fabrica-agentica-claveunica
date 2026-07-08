const data = window.APP_DATA;
const app = document.querySelector("#app");

function route() {
  return location.hash.replace("#", "") || "/dashboard";
}

function setRoute(next) {
  location.hash = next;
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
  return `
    <table>
      <thead><tr><th>${screen.fields[0]}</th><th>${screen.fields[1]}</th><th>${screen.fields[2]}</th></tr></thead>
      <tbody>
        ${screen.records.map((row) => `<tr><td>${row[0]}</td><td>${row[1]}</td><td>${row[2]}</td></tr>`).join("")}
      </tbody>
    </table>
  `;
}

function overviewPanel(screen) {
  return `
    <section class="grid three">
      ${screen.records.map((row, index) => `
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
  return `
    <section class="form-grid">
      <div class="card">
        <h2>${screen.actions[0] || "Gestionar"}</h2>
        ${screen.fields.map((field, index) => `<label>${field}<input value="${screen.records[index % screen.records.length][0]}" /></label>`).join("")}
        <label>Estado<select><option>Recibido</option><option>En revision</option><option>Aprobado</option><option>Observado</option></select></label>
        <button onclick="alert('Solicitud registrada para ${screen.title}')">${screen.actions[0] || "Guardar"}</button>
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
        <button>${screen.primaryAction}</button>
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
        <thead><tr><th>Elemento</th><th>Detalle</th><th>Estado</th></tr></thead>
        <tbody>
          ${screen.records.map((row) => `<tr><td>${row[0]}</td><td>${row[1]}</td><td>${row[2]}</td></tr>`).join("")}
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

window.addEventListener("hashchange", render);
render();
