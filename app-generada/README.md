# App Generada - Portal Ciudadano ClaveUnica

Aplicacion full-stack local funcional generada por la fabrica.

## Stack

- Frontend: Angular standalone.
- Backend: Spring Boot REST + JPA/JdbcTemplate.
- Base de datos: PostgreSQL con 40 tablas de dominio.
- Orquestacion: Docker Compose.

## Criterio De Realidad

- Pantallas diferenciadas por tipo de flujo.
- Endpoints con consultas o mutaciones reales sobre PostgreSQL.
- Acciones de UI que actualizan metricas, listados o auditoria.
- Tests anti-clon y anti-endpoint decorativo.

## Ejecutar

```bash
docker compose up -d --build
```

## Ejecutar en EC2 con imagenes preconstruidas

```bash
cp .env.images.example .env
docker compose -f docker-compose.prebuilt.yml pull
docker compose -f docker-compose.prebuilt.yml up -d
```

- Frontend: http://localhost:3000
- Backend: http://localhost:8080/api/v1/health

## Validar estructura

```bash
npm test
```
