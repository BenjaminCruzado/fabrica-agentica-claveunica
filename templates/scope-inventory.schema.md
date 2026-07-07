# Template Scope Inventory

La fabrica debe producir `scope-inventory.json` con esta estructura conceptual:

```json
{
  "counts": {
    "use_cases": 21,
    "features_or_flows": 40,
    "tables": 40,
    "api_endpoints": 40,
    "screens": 30,
    "business_rules": 60,
    "validations_checks": 100
  },
  "ids": {}
}
```

El validador `rubric_scope` usa estos conteos para bloquear o aprobar la fase previa a implementacion.
