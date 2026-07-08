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
        return `<a class="${active}" href="#${screen.route}"><span>${screen.title.replace(module.name + " - ", "")}</span><small>${screen.id}</small></a>`;
      }).join("")}
    </section>
  `;
}

function dashboard() {
  const counts = data.counts;
  const metrics = [
    ["Casos de uso", counts.use_cases],
    ["Flujos", counts.features_or_flows],
    ["Tablas", counts.tables],
    ["Endpoints", counts.api_endpoints],
    ["Pantallas", counts.screens],
    ["Reglas", counts.business_rules],
    ["Checks", counts.validations_checks]
  ];
  return `
    <section class="hero">
      <div>
        <h1>${data.name}</h1>
        <p>${data.objective}</p>
      </div>
      <div class="actions">
        <button onclick="setRoute('${data.screens[0].route}')">Entrar al portal</button>
        <a class="button secondary" href="/api/v1/scope" target="_blank">Ver contrato API</a>
      </div>
    </section>
    <section class="grid">
      ${metrics.map(([label, value]) => `<div class="card metric"><span class="muted">${label}</span><strong>${value ?? 0}</strong></div>`).join("")}
    </section>
    <section class="module-grid">
      ${data.modules.map((mod) => `
        <article class="card module-card" style="--accent:${mod.accent}">
          <span class="muted">${mod.component}</span>
          <h2>${mod.name}</h2>
          <p>${mod.purpose}</p>
          <button onclick="setRoute('${data.screens.find((screen) => screen.module === mod.id).route}')">${mod.primaryAction}</button>
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
        <h2>${screen.primaryAction}</h2>
        ${screen.fields.map((field, index) => `<label>${field}<input value="${screen.records[index % screen.records.length][0]}" /></label>`).join("")}
        <label>Estado<select><option>Recibido</option><option>En revision</option><option>Aprobado</option><option>Observado</option></select></label>
        <button onclick="alert('Flujo simulado por la fabrica: ${screen.component}')">Guardar</button>
      </div>
      <div class="card">
        <h2>Validaciones de la vista</h2>
        <ul class="check-list">
          <li>Formato de RUN y correo</li>
          <li>Permisos por modulo ${screen.moduleName}</li>
          <li>Consistencia de estado y auditoria</li>
          <li>Mensaje de error y recuperacion</li>
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
  if (screen.variant === "overview") return overviewPanel(screen);
  if (screen.variant === "form") return formPanel(screen);
  return reviewPanel(screen);
}

function screenView(screen) {
  return `
    <section class="card screen-header" style="--accent:${screen.accent}">
      <span class="muted">${screen.id} - ${screen.component} - ${screen.route}</span>
      <h1>${screen.title}</h1>
      <p>${screen.summary}</p>
      <div class="status">${screen.states.map((item) => `<span class="pill">${item}</span>`).join("")}</div>
    </section>
    ${moduleBody(screen)}
    <section class="card">
      <h2>Contrato y trazabilidad</h2>
      <table>
        <tbody>
          <tr><th>Endpoint mock</th><td>/api/v1/${screen.module}/recurso-${screen.id.slice(-2)}</td></tr>
          <tr><th>Fingerprint UI</th><td>${screen.fingerprint}</td></tr>
          <tr><th>Regla cubierta</th><td>Validacion, permisos, auditoria y estado</td></tr>
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
          <span>Generada por ${data.generatedBy}</span>
          <span>Run ${data.runId}</span>
        </div>
        <nav class="nav">
          <a class="${current === "/dashboard" ? "active" : ""}" href="#/dashboard"><span>Dashboard</span><small>Resumen ejecutivo</small></a>
          ${groupedScreens().map(navGroup).join("")}
        </nav>
      </aside>
      <main class="main">
        <div class="topbar">
          <div><strong>Ambiente demo</strong><div class="muted">Datos mock, API local y trazabilidad de fabrica</div></div>
          <div class="status"><span class="pill">ClaveUnica simulada</span><span class="pill">DDU</span><span class="pill">Auditoria</span></div>
        </div>
        ${screen ? screenView(screen) : dashboard()}
      </main>
    </div>
  `;
}

window.addEventListener("hashchange", render);
render();
