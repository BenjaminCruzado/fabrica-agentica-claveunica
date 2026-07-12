# Product Generation Brief

## 1. Objetivo

La fabrica debe generar una aplicacion web local funcional, moderna y completa basada en la especificacion oficial del profesor.

La aplicacion no debe parecer una maqueta, demo estatica, wireframe ni plantilla generica. Debe comportarse como un producto real, con frontend, backend, base de datos, Docker, pruebas y validaciones internas.

## 2. Stack tecnologico obligatorio

La aplicacion debe usar:

- Frontend: Angular
- Backend: Spring Boot
- Base de datos: PostgreSQL
- Contenedores: Docker Compose
- Migraciones: Flyway o Liquibase
- Pruebas E2E: Playwright
- Pruebas backend: JUnit o equivalente
- API: REST JSON

La fabrica puede agregar librerias necesarias, pero no debe cambiar este stack sin aprobacion.

## 3. Prohibiciones importantes

La aplicacion no debe mostrar en el frontend:

- Validaciones internas de la fabrica
- Trazabilidad tecnica
- IDs de rubrica
- Checks internos
- Logs de agentes
- Mensajes tipo "ejecutado desde Angular"
- Paneles de debug
- Actividad reciente artificial
- Texto generico de plantilla
- Pantallas que solo listan requerimientos

El usuario final debe ver una aplicacion ciudadana real, no los mecanismos internos de generacion.

## 4. Principio de producto real

Cada pantalla debe tener proposito funcional claro.

Cada boton importante debe producir un cambio real:

- Cambiar estado en pantalla
- Llamar al backend
- Leer o escribir en PostgreSQL cuando corresponda
- Mostrar feedback al usuario
- Manejar errores
- Refrescar datos

Esta prohibido que un boton solamente registre una accion en una tabla de actividad.

## 5. Dominio esperado

La fabrica debe derivar el modelo de dominio desde la especificacion oficial, pero como minimo debe considerar:

- Ciudadanos
- Perfil ciudadano
- ClaveUnica / autenticacion simulada
- Recuperacion de acceso
- MFA / dispositivos
- Tramites
- Solicitudes de tramite
- Notificaciones
- Mensajes
- Domicilio Digital Unico
- Datos personales
- Datos de contacto
- Autorizaciones de uso de datos
- Sesiones activas
- Auditoria interna

## 6. Base de datos

La fabrica debe disenar automaticamente una base de datos PostgreSQL real.

Debe crear:

- Tablas normalizadas
- Claves primarias
- Claves foraneas
- Estados de negocio
- Fechas de creacion/actualizacion
- Migraciones versionadas
- Datos semilla realistas
- Relaciones entre entidades

No se aceptan datos hardcodeados como fuente principal de la aplicacion.

Los datos semilla deben permitir probar todos los flujos principales sin depender de servicios externos reales.

## 7. API backend

El backend debe exponer endpoints reales por dominio.

Ejemplos esperados:

- Login ciudadano simulado
- Obtener dashboard ciudadano
- Listar tramites
- Ver detalle de tramite
- Iniciar tramite
- Actualizar datos personales
- Actualizar datos de contacto
- Configurar domicilio digital
- Listar notificaciones
- Marcar notificacion como leida
- Listar autorizaciones
- Revocar autorizacion
- Listar sesiones activas
- Cerrar sesion activa
- Listar dispositivos MFA
- Desactivar dispositivo MFA

Cada endpoint debe tener validaciones, respuestas de error y conexion real con la base de datos.

## 8. Frontend

El frontend debe ser una aplicacion ciudadana moderna.

Debe incluir:

- Navegacion clara
- Dashboard ciudadano
- Formularios reales
- Estados de carga
- Estados vacios
- Mensajes de error
- Confirmaciones
- Feedback visual despues de acciones
- Diseno responsive
- Jerarquia visual clara
- Componentes reutilizables

No debe verse como HTML basico ni como una lista de requerimientos.

## 9. Pantallas minimas

La aplicacion debe incluir como minimo:

- Login ClaveUnica simulado
- Recuperacion de acceso
- Dashboard ciudadano
- Catalogo de tramites
- Detalle de tramite
- Inicio de tramite
- Datos personales
- Datos de contacto
- Domicilio digital
- Notificaciones
- Detalle de notificacion
- Autorizaciones de datos
- Solicitud de autorizacion
- Sesiones activas
- Dispositivos y MFA
- Preferencias de privacidad

## 10. Comportamientos esperados

Ejemplos de acciones reales:

- Iniciar sesion debe crear o validar sesion simulada.
- Iniciar tramite debe crear una solicitud en la base de datos.
- Marcar notificacion como leida debe actualizar su estado.
- Revocar autorizacion debe cambiar su estado a revocada.
- Actualizar domicilio debe guardar cambios en PostgreSQL.
- Cerrar sesion activa debe marcarla como cerrada.
- Desactivar MFA debe actualizar el dispositivo.
- Cambiar datos de contacto debe persistir los nuevos datos.

## 11. Seguridad y restricciones

Como es una aplicacion local academica, no debe integrarse con servicios reales del Estado.

Debe simular:

- Login
- MFA
- Validacion de identidad
- Recuperacion de acceso
- Notificaciones
- Autorizaciones

Pero la simulacion debe ser coherente y persistente, no decorativa.

## 12. Docker

La fabrica debe entregar Docker Compose funcional.

Debe levantar:

- frontend
- backend
- postgres

Opcionalmente puede levantar:

- redis
- pgadmin
- servicio de migraciones

Docker debe permitir probar la aplicacion localmente con un solo comando.

## 13. Pruebas obligatorias

La fabrica debe crear y ejecutar pruebas que verifiquen:

- Docker build correcto
- Docker compose up correcto
- Healthcheck backend
- Frontend accesible
- Login funcional
- Navegacion principal
- Botones con efecto real
- Persistencia en DB
- Endpoints principales
- Flujos criticos con Playwright

Si estas pruebas fallan, la fabrica no debe declarar la app como completa.

## 14. Criterios de rechazo

La aplicacion debe rechazarse si:

- Parece plantilla generica
- Muestra validaciones internas al usuario
- Muestra trazabilidad tecnica en la UI
- Los botones solo registran actividad
- No existe base de datos real
- No hay migraciones
- No hay datos semilla
- El backend no tiene logica de dominio
- El frontend usa datos hardcodeados como fuente principal
- Docker no levanta
- Playwright no puede probar flujos reales
- La app no representa correctamente la especificacion oficial

## 15. Agentes de revision

Antes de finalizar, la fabrica debe pasar por agentes/revisores de:

- UX/UI Product Reviewer
- Arquitecto de Software
- QA E2E
- Runtime/Docker
- Product Owner funcional
- Revisor de cumplimiento de requerimientos

Si alguno detecta una falla critica, debe enviar la app a reparacion automatica antes de finalizar.

## 16. Relacion con la especificacion oficial

La especificacion oficial del profesor es la fuente principal de requerimientos.

Este documento no reemplaza esa fuente. Este documento agrega reglas de generacion para que la fabrica convierta los requerimientos en una aplicacion real, usable, persistente y verificable.

## 17. Resultado esperado

El resultado final debe ser una aplicacion local completa que pueda abrirse en el navegador, probarse con datos semilla, ejecutar acciones reales, persistir cambios y pasar pruebas automaticas.

La fabrica solo puede marcar la ejecucion como completa si existe evidencia tecnica de que frontend, backend, base de datos, Docker y pruebas funcionan correctamente.
