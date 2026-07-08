package cl.benjamin.claveunica.domain;

import jakarta.persistence.*;
import java.time.*;
import java.util.*;

@Entity
@Table(name = "notifications")
public class NotificationRecord {
  @Id @GeneratedValue(strategy = GenerationType.UUID)
  public UUID id;
  public String subject;
  public String priority;
  public LocalDateTime readAt;
}
