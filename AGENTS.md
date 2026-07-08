# Agentes De La Fabrica

## Orquestador

Controla el ciclo completo. Normaliza el prompt como `work_order.json`, selecciona agentes, registra routing, ejecuta el arnes, valida gates y cierra con evidencia.

Origen: Semana 10, adaptado a la rubrica final.

## Agente De Requisitos

Convierte la entrada del profesor en especificacion usable, aclaraciones, criterios y primeros artefactos de trabajo.

Origen: Semana 10, adaptado.

## Agente Arquitecto

Define plan tecnico, contratos, tareas y decisiones de arquitectura.

Origen: Semana 10.

## Agente De Diseno De Alcance Rubrica

Formaliza antes de codificar:

- 40 tablas;
- 40 endpoints;
- 30 pantallas;
- 60 reglas de negocio;
- 100 validaciones/CHECK;
- inventario de cantidades;
- validacion de alcance.

Origen: nuevo.

## Agente UI

Define buenas practicas de interfaz, pantallas, estados y experiencia usable.

Origen: Semana 10.

## Agente API Y Seguridad

Define contratos API seguros, autorizacion, validaciones de entrada/salida y criterios de seguridad.

Origen: Semana 10.

## Agente Implementador

Convierte planes y documentos aprobados en codigo dentro del proyecto generado.

Origen: Semana 10, adaptado.

## Agente QA

Valida checklist, pruebas, cobertura, consistencia y cierre.

Origen: Semana 10.

## Agente Docker Packaging

Genera artefactos Docker para que la app pueda ejecutarse de forma reproducible en EC2.

Origen: nuevo.

## Agente GitHub Publication

Prepara o ejecuta publicacion del codigo al repositorio GitHub cuando hay remoto y autorizacion local.

Origen: nuevo.

## Agente Deploy EC2

Lee configuracion local segura, prepara SSH, despliega con Docker Compose y valida URL publica cuando esta autorizado.

Origen: nuevo.

## Agente Evidencia Y Cierre

Produce documentacion tecnica, decisiones, estado de corrida, errores, trazabilidad y reporte final.

Origen: Semana 10, adaptado.

## Capa De Gobernanza WEBFORGE Adaptada

No es un agente separado; es una capa automatica del cierre de corrida.

Produce:

- `principle-ledger.json` con P01-P12;
- `phase-ledger.json` con fase, agente, status, gates y artefactos;
- `claim-map.md` para claims criticos y evidencia;
- `project-manifest.json`, `project-sandboxes.json` y `project-memory-policy.json`;
- `frontend-template-manifest.json`;
- `secrets-report.json`, `dependency-report.json`, `sbom.json`, `rollback-plan.md`;
- `PRBundle.md`.

Origen: nuevo, inspirado en la fabrica del profesor.

## Lo Que No Existe Como Agente

No existe agente de video final. El video lo hace el estudiante. La fabrica solo puede generar evidencia, orden de demostracion o guion de apoyo.
