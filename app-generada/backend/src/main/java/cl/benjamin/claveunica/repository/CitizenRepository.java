package cl.benjamin.claveunica.repository;

import cl.benjamin.claveunica.domain.Citizen;
import org.springframework.data.jpa.repository.JpaRepository;
import java.util.UUID;

public interface CitizenRepository extends JpaRepository<Citizen, UUID> {}
