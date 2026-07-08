package cl.benjamin.claveunica.repository;

import cl.benjamin.claveunica.domain.SessionRecord;
import org.springframework.data.jpa.repository.JpaRepository;
import java.util.UUID;

public interface SessionRecordRepository extends JpaRepository<SessionRecord, UUID> {}
