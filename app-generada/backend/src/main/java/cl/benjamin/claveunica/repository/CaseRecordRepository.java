package cl.benjamin.claveunica.repository;

import cl.benjamin.claveunica.domain.CaseRecord;
import org.springframework.data.jpa.repository.JpaRepository;
import java.util.UUID;

public interface CaseRecordRepository extends JpaRepository<CaseRecord, UUID> {}
