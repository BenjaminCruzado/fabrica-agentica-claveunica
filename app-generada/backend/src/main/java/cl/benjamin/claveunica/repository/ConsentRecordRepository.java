package cl.benjamin.claveunica.repository;

import cl.benjamin.claveunica.domain.ConsentRecord;
import org.springframework.data.jpa.repository.JpaRepository;
import java.util.UUID;

public interface ConsentRecordRepository extends JpaRepository<ConsentRecord, UUID> {}
