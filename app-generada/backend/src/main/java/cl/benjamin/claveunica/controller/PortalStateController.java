package cl.benjamin.claveunica.controller;

import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.web.bind.annotation.*;
import java.util.*;

@RestController
@RequestMapping("/api/v1")
@CrossOrigin
public class PortalStateController {
  private final JdbcTemplate jdbc;
  public PortalStateController(JdbcTemplate jdbc) { this.jdbc = jdbc; }

  @GetMapping("/app-state")
  public Map<String, Object> appState() {
    Map<String, Object> db = new LinkedHashMap<>();
    db.put("citizens", jdbc.queryForList("select * from citizens order by created_at desc"));
    db.put("procedures", jdbc.queryForList("select * from procedures order by updated_at desc"));
    db.put("notifications", jdbc.queryForList("select * from notifications order by priority"));
    db.put("sessions", jdbc.queryForList("select * from sessions order by device"));
    db.put("consents", jdbc.queryForList("select * from consents order by institution"));
    db.put("cases", jdbc.queryForList("select * from cases order by status"));
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
  public Map<String, Object> action(@RequestBody Map<String, Object> payload) {
    String action = String.valueOf(payload.getOrDefault("action", "Actualizar"));
    if (action.contains("Marcar")) {
      jdbc.update("update notifications set read_at = now() where id = (select id from notifications where read_at is null limit 1)");
    }
    jdbc.update("insert into audit_events(event_type, detail) values (?, ?)", "USER_ACTION", action + " ejecutado desde Angular");
    return Map.of("status", "ok", "action", action);
  }
}
