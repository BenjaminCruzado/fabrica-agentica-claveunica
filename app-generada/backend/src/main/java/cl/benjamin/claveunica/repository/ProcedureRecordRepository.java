package cl.benjamin.claveunica.repository;

import cl.benjamin.claveunica.domain.ProcedureRecord;
import org.springframework.data.jpa.repository.JpaRepository;
import java.util.UUID;

public interface ProcedureRecordRepository extends JpaRepository<ProcedureRecord, UUID> {}
