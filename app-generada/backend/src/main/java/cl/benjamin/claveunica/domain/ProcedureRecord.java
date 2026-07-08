package cl.benjamin.claveunica.domain;

import jakarta.persistence.*;
import java.time.*;
import java.util.*;

@Entity
@Table(name = "procedures")
public class ProcedureRecord {
  @Id @GeneratedValue(strategy = GenerationType.UUID)
  public UUID id;
  public String name;
  public String status;
  public String owner;
}
