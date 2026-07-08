package cl.benjamin.claveunica.domain;

import jakarta.persistence.*;
import java.time.*;
import java.util.*;

@Entity
@Table(name = "consents")
public class ConsentRecord {
  @Id @GeneratedValue(strategy = GenerationType.UUID)
  public UUID id;
  public String institution;
  public String dataScope;
  public String status;
}
