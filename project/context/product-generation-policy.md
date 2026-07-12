# Product Generation Policy

- status: `complete`
- source_id: `SRC-PRODUCT-GENERATION-BRIEF`
- source: `C:\Users\Benjamin Cruzado\Desktop\Ultimo Semestre\IA\PROYECTO\fabrica-final\project\input\product_generation_brief.md`

## Required Stack

- frontend: Angular
- backend: Spring Boot
- database: PostgreSQL
- containers: Docker Compose
- migrations: ['Flyway', 'Liquibase']
- e2e: Playwright
- backend_tests: ['JUnit', 'equivalent']
- api: REST JSON

## Forbidden Frontend Content

- validaciones internas de la fabrica
- trazabilidad tecnica
- IDs de rubrica
- checks internos
- logs de agentes
- ejecutado desde Angular
- paneles de debug
- actividad reciente artificial
- texto generico de plantilla
- pantallas que solo listan requerimientos

## Real Action Policy

- cada boton importante debe cambiar estado visible
- cada boton importante debe llamar backend
- cada accion relevante debe leer o escribir PostgreSQL
- cada accion relevante debe mostrar feedback
- cada accion relevante debe manejar errores
- prohibido registrar solo actividad sin efecto de dominio

## Rejection Criteria

- parece plantilla generica
- muestra validaciones internas al usuario
- muestra trazabilidad tecnica en la UI
- botones solo registran actividad
- no existe base de datos real
- no hay migraciones
- no hay datos semilla
- backend sin logica de dominio
- frontend usa datos hardcodeados como fuente principal
- docker no levanta
- playwright no prueba flujos reales
- no representa la especificacion oficial
