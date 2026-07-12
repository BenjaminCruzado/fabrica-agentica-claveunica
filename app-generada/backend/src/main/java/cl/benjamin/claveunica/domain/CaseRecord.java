package cl.benjamin.claveunica.domain;

import jakarta.persistence.*;
import java.time.*;
import java.util.*;

@Entity
@Table(name = "cases")
public class CaseRecord {
  @Id @GeneratedValue(strategy = GenerationType.UUID)
  public UUID id;
  public String status;
  public String responsible;
  public UUID procedureId;
}
