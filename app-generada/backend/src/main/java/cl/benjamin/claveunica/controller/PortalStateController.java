package cl.benjamin.claveunica.controller;

import cl.benjamin.claveunica.dto.ActionRequest;
import cl.benjamin.claveunica.service.PortalWorkflowService;
import jakarta.validation.Valid;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.web.bind.annotation.*;
import java.util.*;

@RestController
@RequestMapping("/api/v1")
@CrossOrigin
public class PortalStateController {
  private final JdbcTemplate jdbc;
  private final PortalWorkflowService workflows;
  public PortalStateController(JdbcTemplate jdbc, PortalWorkflowService workflows) { this.jdbc = jdbc; this.workflows = workflows; }

  @GetMapping("/app-state")
  public Map<String, Object> appState() {
    Map<String, Object> db = new LinkedHashMap<>();
    db.put("citizens", jdbc.queryForList("select * from citizens order by created_at desc"));
    db.put("services", jdbc.queryForList("select * from services order by name"));
    db.put("procedures", jdbc.queryForList("select * from procedures order by updated_at desc"));
    db.put("notifications", jdbc.queryForList("select * from notifications order by priority"));
    db.put("sessions", jdbc.queryForList("select * from sessions order by device"));
    db.put("consents", jdbc.queryForList("select * from consents order by institution"));
    db.put("addresses", jdbc.queryForList("select * from digital_addresses order by verified_at nulls first"));
    db.put("cases", jdbc.queryForList("select * from cases order by status"));
    db.put("tickets", jdbc.queryForList("select * from support_tickets order by updated_at desc"));
    db.put("profileChanges", jdbc.queryForList("select * from profile_changes order by changed_at desc"));
    db.put("events", jdbc.queryForList("select * from audit_events order by created_at desc limit 10"));
    List<Map<String, Object>> metrics = List.of(
      Map.of("label", "Tramites activos", "value", jdbc.queryForObject("select count(*) from procedures where status <> 'completado'", Long.class)),
      Map.of("label", "Mensajes nuevos", "value", jdbc.queryForObject("select count(*) from notifications where read_at is null", Long.class)),
      Map.of("label", "Sesiones protegidas", "value", jdbc.queryForObject("select count(*) from sessions where active = true", Long.class)),
      Map.of("label", "Autorizaciones vigentes", "value", jdbc.queryForObject("select count(*) from consents where status = 'vigente'", Long.class))
    );
    return Map.of("name", "Portal Ciudadano ClaveUnica", "portalMetrics", metrics, "db", db);
  }

  @PostMapping("/actions")
  public Map<String, Object> action(@Valid @RequestBody ActionRequest request) { return workflows.runAction(request); }
}
