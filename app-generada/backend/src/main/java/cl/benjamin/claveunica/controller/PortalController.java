package cl.benjamin.claveunica.controller;

import org.springframework.jdbc.core.JdbcTemplate;
import cl.benjamin.claveunica.dto.ContactUpdateRequest;
import cl.benjamin.claveunica.dto.ProcedureRequest;
import cl.benjamin.claveunica.service.PortalWorkflowService;
import jakarta.validation.Valid;
import org.springframework.web.bind.annotation.*;
import java.util.*;

@RestController
@RequestMapping("/api/v1")
@CrossOrigin
public class PortalController {
  private final JdbcTemplate jdbc;
  private final PortalWorkflowService workflows;
  public PortalController(JdbcTemplate jdbc, PortalWorkflowService workflows) { this.jdbc = jdbc; this.workflows = workflows; }

  private UUID citizenId() { return workflows.citizenId(); }
  private void audit(String eventType, String detail) { workflows.audit(eventType, detail); }

  @GetMapping("/health")
  public Map<String, Object> health() { return Map.of("status", "ready", "service", "Portal Ciudadano ClaveUnica"); }

  @GetMapping("/dashboard")
  public Map<String, Object> dashboard() { return workflows.dashboard(); }

  @GetMapping("/citizens")
  public List<Map<String, Object>> citizens() { return jdbc.queryForList("select run, full_name, email, phone, preferred_channel from citizens order by created_at desc"); }

  @PatchMapping("/citizens/contact")
  public Map<String, Object> updateContact(@Valid @RequestBody ContactUpdateRequest request) { return workflows.updateContact(request); }

  @GetMapping("/services")
  public List<Map<String, Object>> services() { return jdbc.queryForList("select code, name, institution, available, channel from services order by name"); }

  @PostMapping("/procedures")
  public Map<String, Object> createProcedure(@Valid @RequestBody ProcedureRequest request) { return workflows.createProcedure(request); }

  @GetMapping("/procedures")
  public List<Map<String, Object>> procedures() { return jdbc.queryForList("select name, status, owner, updated_at from procedures order by updated_at desc"); }

  @PatchMapping("/procedures/{id}/status")
  public Map<String, Object> updateProcedureStatus(@PathVariable String id, @RequestBody Map<String, Object> payload) {
    String status = String.valueOf(payload.getOrDefault("status", "en revision"));
    jdbc.update("update procedures set status = ?, updated_at = now() where id = ?::uuid", status, id);
    audit("PROCEDURE_STATUS", "Estado cambiado a " + status);
    return Map.of("id", id, "status", status);
  }

  @GetMapping("/notifications")
  public List<Map<String, Object>> notifications() { return jdbc.queryForList("select id, subject, priority, channel, read_at from notifications order by read_at nulls first, priority"); }

  @PatchMapping("/notifications/{id}/read")
  public Map<String, Object> readNotification(@PathVariable String id) {
    jdbc.update("update notifications set read_at = now() where id = ?::uuid", id);
    audit("NOTIFICATION_READ", id);
    return Map.of("id", id, "read", true);
  }

  @PostMapping("/notifications/read-next")
  public Map<String, Object> readNextNotification() {
    jdbc.update("update notifications set read_at = now() where id = (select id from notifications where read_at is null order by priority limit 1)");
    audit("NOTIFICATION_READ", "Siguiente notificacion pendiente");
    return Map.of("read", true);
  }

  @PostMapping("/notifications/preferences")
  public Map<String, Object> saveNotificationPreference(@RequestBody Map<String, Object> payload) {
    String channel = String.valueOf(payload.getOrDefault("channel", "email"));
    jdbc.update("insert into notification_preferences(citizen_id, channel, quiet_hours, min_priority) values (?, ?, '22:00-08:00', 'media')", citizenId(), channel);
    audit("NOTIFICATION_PREF", channel);
    return Map.of("channel", channel, "saved", true);
  }

  @GetMapping("/sessions")
  public List<Map<String, Object>> sessions() { return jdbc.queryForList("select id, device, location, active, trusted, last_seen from sessions order by last_seen desc"); }

  @PatchMapping("/sessions/{id}/close")
  public Map<String, Object> closeSession(@PathVariable String id) {
    jdbc.update("update sessions set active = false where id = ?::uuid", id);
    audit("SESSION_CLOSED", id);
    return Map.of("id", id, "active", false);
  }

  @PostMapping("/security/close-session")
  public Map<String, Object> closeCurrentSession() {
    jdbc.update("update sessions set active = false where id = (select id from sessions where active = true order by last_seen desc limit 1)");
    audit("SESSION_CLOSED", "Sesion activa cerrada desde portal local");
    return Map.of("active", false);
  }

  @PostMapping("/security/login-attempt")
  public Map<String, Object> loginAttempt(@RequestBody Map<String, Object> payload) {
    String run = String.valueOf(payload.getOrDefault("run", "demo"));
    jdbc.update("insert into sessions(citizen_id, device, ip, location, active, trusted) values (?, 'Portal local', '127.0.0.1', 'Local', true, true)", citizenId());
    audit("LOGIN_OK", "Ingreso local validado para " + run);
    return Map.of("authenticated", true, "run", run);
  }

  @PostMapping("/mfa-methods")
  public Map<String, Object> createMfa(@RequestBody Map<String, Object> payload) {
    String method = String.valueOf(payload.getOrDefault("method", "app"));
    jdbc.update("insert into mfa_methods(citizen_id, method, status, backup_enabled) values (?, ?, 'activo', true)", citizenId(), method);
    audit("MFA_ENABLED", method);
    return Map.of("method", method, "enabled", true);
  }

  @GetMapping("/digital-addresses/current")
  public List<Map<String, Object>> currentAddress() { return jdbc.queryForList("select address_line, comuna, status, verified_at from digital_addresses order by verified_at nulls first"); }

  @PostMapping("/digital-addresses")
  public Map<String, Object> createAddress(@RequestBody Map<String, Object> payload) {
    String address = String.valueOf(payload.getOrDefault("addressLine", payload.getOrDefault("address", "Nueva direccion demo 456")));
    jdbc.update("insert into digital_addresses(citizen_id, address_line, comuna, status) values (?, ?, 'Santiago', 'pendiente')", citizenId(), address);
    jdbc.update("insert into address_history(citizen_id, address_line, source) values (?, ?, 'portal')", citizenId(), address);
    audit("ADDRESS_UPDATED", address);
    return Map.of("address", address, "status", "pendiente");
  }

  @GetMapping("/digital-addresses/history")
  public List<Map<String, Object>> addressHistory() { return jdbc.queryForList("select address_line, source, changed_at from address_history order by changed_at desc"); }

  @GetMapping("/consents")
  public List<Map<String, Object>> consents() { return jdbc.queryForList("select id, institution, data_scope, status, expires_at from consents order by expires_at"); }

  @PostMapping("/consent-requests")
  public Map<String, Object> requestConsent(@RequestBody Map<String, Object> payload) {
    String requester = String.valueOf(payload.getOrDefault("requester", "Servicio demo"));
    jdbc.update("insert into consent_requests(citizen_id, requester, purpose, duration_days) values (?, ?, 'validacion de datos', 30)", citizenId(), requester);
    audit("CONSENT_REQUESTED", requester);
    return Map.of("requester", requester, "requested", true);
  }

  @PatchMapping("/consents/{id}/revoke")
  public Map<String, Object> revokeConsent(@PathVariable String id) {
    jdbc.update("update consents set status = 'revocado' where id = ?::uuid", id);
    jdbc.update("insert into consent_history(consent_id, action, actor) values (?::uuid, 'revocar', 'ciudadano')", id);
    audit("CONSENT_REVOKED", id);
    return Map.of("id", id, "status", "revocado");
  }

  @PostMapping("/consents/revoke-next")
  public Map<String, Object> revokeNextConsent() {
    jdbc.update("update consents set status = 'revocado' where id = (select id from consents where status = 'vigente' order by expires_at limit 1)");
    jdbc.update("insert into consent_history(consent_id, action, actor) select id, 'revocar', 'ciudadano' from consents where status = 'revocado' order by expires_at limit 1");
    audit("CONSENT_REVOKED", "Autorizacion vigente revocada desde portal local");
    return Map.of("status", "revocado");
  }

  @GetMapping("/consents/history")
  public List<Map<String, Object>> consentHistory() { return jdbc.queryForList("select action, actor, created_at from consent_history order by created_at desc"); }

  @GetMapping("/cases")
  public List<Map<String, Object>> cases() { return jdbc.queryForList("select id, status, responsible, priority from cases order by priority"); }

  @PostMapping("/cases/{id}/comments")
  public Map<String, Object> commentCase(@PathVariable String id, @RequestBody Map<String, Object> payload) {
    String detail = String.valueOf(payload.getOrDefault("detail", "Comentario ciudadano"));
    jdbc.update("insert into case_events(case_id, event_type, detail) values (?::uuid, 'COMMENT', ?)", id, detail);
    audit("CASE_COMMENT", detail);
    return Map.of("caseId", id, "commented", true);
  }

  @PostMapping("/cases/comment-next")
  public Map<String, Object> commentNextCase(@RequestBody Map<String, Object> payload) {
    String detail = String.valueOf(payload.getOrDefault("comment", "Comentario ciudadano"));
    jdbc.update("insert into case_events(case_id, event_type, detail) select id, 'COMMENT', ? from cases order by priority limit 1", detail);
    audit("CASE_COMMENT", detail);
    return Map.of("commented", true);
  }

  @PostMapping("/case-documents")
  public Map<String, Object> caseDocument(@RequestBody Map<String, Object> payload) {
    jdbc.update("insert into case_documents(case_id, document_name, status) select id, ?, 'recibido' from cases order by priority limit 1", String.valueOf(payload.getOrDefault("name", "documento.pdf")));
    audit("CASE_DOCUMENT", "Documento adjunto");
    return Map.of("uploaded", true);
  }

  @GetMapping("/cases/{id}/timeline")
  public List<Map<String, Object>> caseTimeline(@PathVariable String id) { return jdbc.queryForList("select event_type, detail, created_at from case_events where case_id = ?::uuid order by created_at desc", id); }

  @GetMapping("/faq")
  public List<Map<String, Object>> faq() { return jdbc.queryForList("select question, category, answer, helpful_count from faq_entries order by helpful_count desc"); }

  @PostMapping("/support-tickets")
  public Map<String, Object> supportTicket(@RequestBody Map<String, Object> payload) {
    String topic = String.valueOf(payload.getOrDefault("topic", "Consulta ciudadana"));
    jdbc.update("insert into support_tickets(citizen_id, topic, channel) values (?, ?, 'portal')", citizenId(), topic);
    audit("SUPPORT_TICKET", topic);
    return Map.of("topic", topic, "created", true);
  }

  @PatchMapping("/support-tickets/{id}/close")
  public Map<String, Object> closeTicket(@PathVariable String id) {
    jdbc.update("update support_tickets set status = 'cerrado', updated_at = now() where id = ?::uuid", id);
    audit("SUPPORT_CLOSED", id);
    return Map.of("id", id, "status", "cerrado");
  }

  @GetMapping("/audit-events")
  public List<Map<String, Object>> auditEvents() { return jdbc.queryForList("select event_type, detail, created_at from audit_events order by created_at desc limit 25"); }

  @PostMapping("/audit-exports")
  public Map<String, Object> auditExport(@RequestBody Map<String, Object> payload) {
    String format = String.valueOf(payload.getOrDefault("format", "CSV"));
    jdbc.update("insert into audit_exports(requested_by, format, range_label) values (?, ?, 'ultimos 30 dias')", citizenId(), format);
    audit("AUDIT_EXPORT", format);
    return Map.of("format", format, "status", "pendiente");
  }

  @GetMapping("/integration-status")
  public List<Map<String, Object>> integrationStatus() { return jdbc.queryForList("select service_name, status, latency_ms, checked_at from integration_status order by latency_ms desc"); }

  @GetMapping("/security-alerts")
  public List<Map<String, Object>> securityAlerts() { return jdbc.queryForList("select severity, title, resolved, created_at from security_alerts order by created_at desc"); }

  @GetMapping("/business-rules")
  public List<Map<String, Object>> businessRules() { return jdbc.queryForList("select rule_code, module, description, active from business_rules order by rule_code"); }

  @GetMapping("/validation-rules")
  public List<Map<String, Object>> validationRules() { return jdbc.queryForList("select rule_code, field_name, expression, message from validation_rules order by rule_code"); }

  @GetMapping("/roles")
  public List<Map<String, Object>> roles() { return jdbc.queryForList("select r.code, r.name, r.description from roles r order by r.code"); }

  @PostMapping("/favorites")
  public Map<String, Object> favorite() {
    jdbc.update("insert into favorites(citizen_id, service_id) select ?, id from services order by name limit 1", citizenId());
    audit("FAVORITE_CREATED", "Servicio guardado");
    return Map.of("favorite", true);
  }

  @PostMapping("/workflow-events")
  public Map<String, Object> workflowEvent(@RequestBody Map<String, Object> payload) {
    String feature = String.valueOf(payload.getOrDefault("feature", "portal"));
    String action = String.valueOf(payload.getOrDefault("action", "accion"));
    audit("WORKFLOW_EVENT", feature + ": " + action);
    return Map.of("feature", feature, "action", action, "recorded", true);
  }

  @GetMapping("/scope")
  public Map<String, Object> scope() { return Map.of("screens", 30, "endpoints", 40, "quality", "functional-local"); }

  @GetMapping("/screens")
  public List<Map<String, Object>> screens() { return jdbc.queryForList("select module, description from business_rules order by module"); }

  @GetMapping("/audit-summary")
  public Map<String, Object> auditSummary() { return Map.of("events", jdbc.queryForObject("select count(*) from audit_events", Long.class)); }

  @GetMapping("/sla-rules")
  public List<Map<String, Object>> slaRules() { return jdbc.queryForList("select module, priority, max_hours from sla_rules order by max_hours"); }

  @GetMapping("/api-clients")
  public List<Map<String, Object>> apiClients() { return jdbc.queryForList("select client_name, scope, active from api_clients order by client_name"); }
}
