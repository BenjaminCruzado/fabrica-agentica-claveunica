package cl.benjamin.claveunica.domain;

import jakarta.persistence.*;
import java.time.*;
import java.util.*;

@Entity
@Table(name = "audit_events")
public class AuditEvent {
  @Id @GeneratedValue(strategy = GenerationType.UUID)
  public UUID id;
  public String eventType;
  public String detail;
  public LocalDateTime createdAt;
}
