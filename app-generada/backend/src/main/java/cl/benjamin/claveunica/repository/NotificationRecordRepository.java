package cl.benjamin.claveunica.repository;

import cl.benjamin.claveunica.domain.NotificationRecord;
import org.springframework.data.jpa.repository.JpaRepository;
import java.util.UUID;

public interface NotificationRecordRepository extends JpaRepository<NotificationRecord, UUID> {}
