# Fabrica Agentica Evaluacion Final

## Proposito

Esta fabrica recibe una entrada realista de trabajo, la formaliza, la planifica, la reparte entre agentes especializados, valida sus cantidades minimas, conduce la implementacion de una aplicacion web y cierra con evidencia tecnica.

La aplicacion web no se desarrolla como trabajo manual aislado. La aplicacion es el producto generado y gobernado por la fabrica.

## Entrada Inicial

La entrada principal de esta entrega es el caso ficticio basado en la licitacion del Portal Ciudadano ClaveUnica, DDU, notificaciones y autorizaciones.

El archivo `project/input/caso_claveunica.md` resume el caso. El archivo fuente del profesor se considera valido y utilizable.

## Flujo Obligatorio

```text
prompt inicial
-> work order
-> refinamiento de requisitos
-> planificacion
-> diseno de alcance de rubrica
-> validacion de cantidades
-> implementacion
-> pruebas
-> validacion final
-> evidencia
-> cierre tecnico
```

## Gate Principal

La fabrica no debe pasar a implementacion si `scope-validation.json` no esta en estado `complete`.

Minimos controlados:

- 10 casos de uso
- 30 funcionalidades o flujos
- 40 tablas
- 40 endpoints API
- 30 pantallas
- 60 reglas de negocio
- 100 validaciones/CHECK

## Base Heredada

- Orquestador, arnes, registros, validadores y runs: Semana 10.
- Constitucion, reglas SDD y estados de gobierno: Semana 8.
- Explicacion simple de flujo agentico: Semana 7.

## Cierre

Cada corrida debe dejar evidencia en `project/runs/RUN-*`, incluyendo plan, artefactos generados, matriz de trazabilidad, validacion de alcance, reportes de prueba y reporte final.
