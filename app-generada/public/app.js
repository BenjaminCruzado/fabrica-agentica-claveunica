const data = window.APP_DATA;
const app = document.querySelector("#app");

function route() {
  return location.hash.replace("#", "") || "/dashboard";
}

function setRoute(next) {
  location.hash = next;
}

function navItem(screen) {
  const active = route() === screen.route ? "active" : "";
  return `<a class="${active}" href="#${screen.route}"><strong>${screen.title}</strong><small>${screen.id} - ${screen.moduleName}</small></a>`;
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
        <button onclick="setRoute('${data.screens[0].route}')">Abrir primera vista</button>
        <a class="button secondary" href="/api/v1/scope" target="_blank">Ver API mock</a>
      </div>
    </section>
    <section class="grid">
      ${metrics.map(([label, value]) => `<div class="card metric"><span class="muted">${label}</span><strong>${value ?? 0}</strong></div>`).join("")}
    </section>
    <section class="card">
      <h2>Modulos principales</h2>
      <table>
        <thead><tr><th>Modulo</th><th>Estado</th><th>Uso en demo</th></tr></thead>
        <tbody>
          ${data.modules.map((mod) => `<tr><td>${mod.name}</td><td>simulado</td><td>Portal, formularios, tablas y estados de usuario</td></tr>`).join("")}
        </tbody>
      </table>
    </section>
  `;
}

function screenView(screen) {
  return `
    <section class="card screen-header" style="--accent:${screen.accent}">
      <span class="muted">${screen.id} - ${screen.route}</span>
      <h1>${screen.title}</h1>
      <p>${screen.summary}</p>
      <div class="status">${screen.states.map((item) => `<span class="pill">${item}</span>`).join("")}</div>
    </section>
    <section class="form-grid">
      <div class="card">
        <h2>Operacion ciudadana</h2>
        <label>RUN ciudadano<input value="${data.mockUser.run}" /></label>
        <label>Correo<input value="${data.mockUser.email}" /></label>
        <label>Estado<select><option>Solicitud recibida</option><option>En revision</option><option>Resuelta</option></select></label>
        <button onclick="alert('Accion simulada por la fabrica')">Guardar simulacion</button>
      </div>
      <div class="card">
        <h2>Resumen seguro</h2>
        <p class="notice">Autenticacion ClaveUnica simulada con MFA ${data.mockUser.mfa}. No se usan datos reales ni integraciones estatales.</p>
        <table>
          <tbody>
            <tr><th>Modulo</th><td>${screen.moduleName}</td></tr>
            <tr><th>Endpoint</th><td>/api/v1/${screen.module}/recurso-${screen.id.slice(-2)}</td></tr>
            <tr><th>Validacion</th><td>Entrada, permisos, estado y consistencia</td></tr>
          </tbody>
        </table>
      </div>
    </section>
    <section class="card">
      <h2>Bitacora mock</h2>
      <table>
        <thead><tr><th>Fecha</th><th>Evento</th><th>Resultado</th></tr></thead>
        <tbody>
          <tr><td>2026-07-07</td><td>Ingreso a ${screen.title}</td><td>Permitido</td></tr>
          <tr><td>2026-07-07</td><td>Validacion de datos</td><td>Completa</td></tr>
          <tr><td>2026-07-07</td><td>Auditoria</td><td>Registrada</td></tr>
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
          <a class="${current === "/dashboard" ? "active" : ""}" href="#/dashboard"><strong>Dashboard</strong><small>Resumen de rubrica</small></a>
          ${data.screens.map(navItem).join("")}
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
