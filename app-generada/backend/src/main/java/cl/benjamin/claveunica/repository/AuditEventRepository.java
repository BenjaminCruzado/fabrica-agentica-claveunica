package cl.benjamin.claveunica.repository;

import cl.benjamin.claveunica.domain.AuditEvent;
import org.springframework.data.jpa.repository.JpaRepository;
import java.util.UUID;

public interface AuditEventRepository extends JpaRepository<AuditEvent, UUID> {}
