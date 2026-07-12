package cl.benjamin.claveunica.service;

import cl.benjamin.claveunica.dto.*;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import java.util.*;

@Service
public class PortalWorkflowService {
  private final JdbcTemplate jdbc;
  public PortalWorkflowService(JdbcTemplate jdbc) { this.jdbc = jdbc; }

  public UUID citizenId() {
    return jdbc.queryForObject("select id from citizens order by created_at limit 1", UUID.class);
  }

  public void audit(String eventType, String detail) {
    jdbc.update("insert into audit_events(citizen_id, event_type, detail) values (?, ?, ?)", citizenId(), eventType, detail);
  }

  public Map<String, Object> dashboard() {
    return Map.of(
      "activeProcedures", jdbc.queryForObject("select count(*) from procedures where status <> 'completado'", Long.class),
      "unreadNotifications", jdbc.queryForObject("select count(*) from notifications where read_at is null", Long.class),
      "activeConsents", jdbc.queryForObject("select count(*) from consents where status = 'vigente'", Long.class),
      "openTickets", jdbc.queryForObject("select count(*) from support_tickets where status <> 'cerrado'", Long.class)
    );
  }

  @Transactional
  public Map<String, Object> createProcedure(ProcedureRequest request) {
    jdbc.update("insert into procedures(citizen_id, service_id, name, status, owner) select ?, id, ?, 'pendiente', institution from services order by name limit 1", citizenId(), request.name());
    audit("PROCEDURE_CREATED", request.name());
    return Map.of("created", true, "name", request.name());
  }

  @Transactional
  public Map<String, Object> updateContact(ContactUpdateRequest request) {
    jdbc.update("update citizens set email = ? where id = ?", request.email(), citizenId());
    jdbc.update("insert into profile_changes(citizen_id, field_name, old_value, new_value) values (?, 'email', 'seed', ?)", citizenId(), request.email());
    audit("CONTACT_UPDATED", "Correo actualizado desde portal");
    return Map.of("email", request.email(), "updated", true);
  }

  @Transactional
  public Map<String, Object> runAction(ActionRequest request) {
    String action = request.action();
    if (action.contains("Marcar")) {
      jdbc.update("update notifications set read_at = now() where id = (select id from notifications where read_at is null limit 1)");
    } else if (action.contains("Iniciar") || action.contains("Continuar")) {
      jdbc.update("insert into procedures(citizen_id, service_id, name, status, owner) select c.id, s.id, 'Tramite iniciado desde UI', 'pendiente', s.institution from citizens c cross join services s order by s.name limit 1");
    } else if (action.contains("Revocar")) {
      jdbc.update("update consents set status = 'revocado' where id = (select id from consents where status = 'vigente' limit 1)");
    } else if (action.contains("Crear ticket")) {
      jdbc.update("insert into support_tickets(citizen_id, topic, channel) select id, 'Ticket creado desde UI', 'portal' from citizens limit 1");
    } else if (action.contains("Cerrar sesion")) {
      jdbc.update("update sessions set active = false where id = (select id from sessions where active = true limit 1)");
    }
    audit("WORKFLOW_EVENT", action + " ejecutado desde portal local");
    return Map.of("status", "ok", "action", action);
  }
}
