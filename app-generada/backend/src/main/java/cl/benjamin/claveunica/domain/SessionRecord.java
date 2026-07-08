package cl.benjamin.claveunica.domain;

import jakarta.persistence.*;
import java.time.*;
import java.util.*;

@Entity
@Table(name = "sessions")
public class SessionRecord {
  @Id @GeneratedValue(strategy = GenerationType.UUID)
  public UUID id;
  public String device;
  public String location;
  public Boolean active;
}
