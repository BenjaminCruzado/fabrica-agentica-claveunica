package cl.benjamin.claveunica.domain;

import jakarta.persistence.*;
import java.time.*;
import java.util.*;

@Entity
@Table(name = "citizens")
public class Citizen {
  @Id @GeneratedValue(strategy = GenerationType.UUID)
  public UUID id;
  public String run;
  public String fullName;
  public String email;
  public String phone;
}
