# Caso De Entrada - Portal Ciudadano ClaveUnica

## Fuente Principal

Se usa como fuente principal el archivo entregado por el profesor:

`../../proyecto licitacion 3/proyecto licitación 3/especificacion_requerimientos_funcionales-2.md`

Para esta entrega, ese archivo se considera valido y utilizable.

## Descripcion

Construir una aplicacion web local funcional basada en un Portal Ciudadano ClaveUnica con:

- portal publico;
- autenticacion simulada;
- datos personales;
- segundo factor;
- sesiones;
- Domicilio Digital Unico;
- notificaciones;
- detalle de notificaciones;
- autorizaciones de uso de datos sensibles;
- historial de datos compartidos;
- expedientes;
- ayuda publica e institucional;
- auditoria.

La aplicacion no debe depender de servicios estatales reales, pero si debe comportarse como una app real en local:

- frontend con pantallas diferenciadas por tipo de flujo;
- backend con endpoints que consulten o muten datos;
- PostgreSQL con tablas de dominio, relaciones y semillas coherentes;
- migraciones versionadas para crear y poblar la base local;
- contrato OpenAPI derivado del mismo catalogo que usa la implementacion;
- acciones visibles que actualicen metricas, listados o estados;
- pruebas que validen comportamiento, no solo cantidad de archivos.

## Rol En La Fabrica

Este caso no se implementa manualmente de inmediato. Primero la fabrica debe:

1. formalizar requisitos;
2. generar documentos de alcance;
3. validar cantidades de rubrica;
4. planificar implementacion;
5. implementar;
6. probar;
7. cerrar con evidencia.

## Minimos De Rubrica

- 10 casos de uso;
- 30 funcionalidades o flujos;
- 40 tablas;
- 40 endpoints API;
- 30 pantallas;
- 60 reglas de negocio;
- 100 validaciones/CHECK;
- pruebas automatizadas;
- pruebas de integracion backend contra PostgreSQL local o Testcontainers;
- features frontend con modelos, servicios y componentes por dominio;
- ejecucion local reproducible con Docker;
- evidencia tecnica para video.

## Gates De Realidad

- No cuenta una pantalla si es clon visual de otra con solo texto cambiado.
- No cuenta un endpoint si solo retorna `status: ok`.
- No cuenta una tabla si solo existe para rellenar cantidad y no participa en ningun flujo.
- Al menos los flujos de tramite, notificacion, consentimiento, domicilio, soporte y auditoria deben tener efecto persistente observable.
