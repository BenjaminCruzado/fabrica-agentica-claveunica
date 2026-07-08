# App Generada - Portal Ciudadano ClaveUnica

Aplicacion full-stack generada por la fabrica.

## Stack

- Frontend: Angular standalone.
- Backend: Spring Boot REST + JPA/JdbcTemplate.
- Base de datos: PostgreSQL con 40 tablas.
- Orquestacion: Docker Compose.

## Ejecutar

```bash
docker compose up -d --build
```

- Frontend: http://localhost:3000
- Backend: http://localhost:8080/api/v1/health

## Validar estructura

```bash
npm test
```
