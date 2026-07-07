# Plan De Operacion De La Fabrica

## Secuencia

1. El usuario pide crear la app desde el `.md`.
2. La fabrica normaliza la entrada.
3. La fabrica formaliza documentos exigidos.
4. La fabrica valida cantidades.
5. La fabrica implementa.
6. La fabrica prueba.
7. La fabrica cierra con evidencia.

## Gate Critico

El gate `rubric_scope` se ejecuta antes de implementar. Usa `scope-inventory.json` y produce `scope-validation.json`.

## Evidencia Esperada

- `work_order.json`
- `scope-inventory.json`
- `scope-validation.json`
- documentos generados
- `validation-report.json`
- `traceability-matrix.md`
- `final-report.json`
