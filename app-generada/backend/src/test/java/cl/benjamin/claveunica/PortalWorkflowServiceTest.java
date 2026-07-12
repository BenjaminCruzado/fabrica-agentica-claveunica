package cl.benjamin.claveunica;

import cl.benjamin.claveunica.dto.ProcedureRequest;
import cl.benjamin.claveunica.service.PortalWorkflowService;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.test.context.DynamicPropertyRegistry;
import org.springframework.test.context.DynamicPropertySource;
import org.testcontainers.containers.PostgreSQLContainer;
import org.testcontainers.junit.jupiter.Container;
import org.testcontainers.junit.jupiter.Testcontainers;

import static org.assertj.core.api.Assertions.assertThat;

@SpringBootTest
@Testcontainers
class PortalWorkflowServiceTest {
  @Container
  static PostgreSQLContainer<?> postgres = new PostgreSQLContainer<>("postgres:16-alpine")
    .withDatabaseName("claveunica")
    .withUsername("claveunica")
    .withPassword("claveunica");

  @DynamicPropertySource
  static void datasource(DynamicPropertyRegistry registry) {
    registry.add("spring.datasource.url", postgres::getJdbcUrl);
    registry.add("spring.datasource.username", postgres::getUsername);
    registry.add("spring.datasource.password", postgres::getPassword);
  }

  @Autowired PortalWorkflowService workflows;

  @Test
  void createProcedurePersistsAndUpdatesDashboard() {
    long before = ((Number) workflows.dashboard().get("activeProcedures")).longValue();
    workflows.createProcedure(new ProcedureRequest("Tramite test de integracion"));
    long after = ((Number) workflows.dashboard().get("activeProcedures")).longValue();
    assertThat(after).isGreaterThanOrEqualTo(before + 1);
  }
}
