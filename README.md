# Fabrica Final

Fabrica agentica para la evaluacion final integradora.

## Comandos Basicos

Listar agentes:

```bash
python -m factory.cli list
```

Ejecutar una corrida:

```bash
python -m factory.cli run --project project --objective "Crear app web ficticia ClaveUnica desde el md del profesor, formalizar rubrica, validar cantidades antes de codificar y dejar evidencia de fabrica"
```

Ejecutar solo una fase:

```bash
python -m factory.cli run --project project --objective "Validar alcance" --phase scope_design
```

Reanudar desde una fase:

```bash
python -m factory.cli resume --project project --from-phase implement
```

Verificar la ultima corrida:

```bash
python -m factory.cli verify --project project
```

## Gate De Rubrica

La corrida debe producir:

- `scope-inventory.json`
- `scope-validation.json`

Si `scope-validation.json` no esta en estado `complete`, la fabrica no deberia pasar a implementacion.

## Mejoras Incorporadas

- ejecucion por fase;
- reanudacion desde fase;
- fases `containerize`, `publish` y `deploy`;
- soporte Docker para despliegue reproducible;
- soporte GitHub para commit/push si hay remoto configurado;
- soporte EC2 mediante `project/secrets/deploy-target.local.json`;
- contexto compacto en `project/context`;
- cache de alcance en `project/cache/scope_design`;
- validacion de documentos de fabrica;
- validacion de trazabilidad;
- presupuesto registrado por corrida;
- plantillas estrictas para tablas, endpoints y pantallas;
- reporte ejecutivo por corrida;
- separacion de evidencia en carpetas `evidence`, `generated-docs`, `reports` y `logs`.

## Configuracion Local Para Un Paso Completo

Estructura principal:

```text
factory/       # codigo de la fabrica
app-generada/  # app desplegable producida por la fabrica
docs/          # documentacion
project/       # entrada/contexto y estado local
```

Crear este archivo solo en tu PC:

```text
project/secrets/deploy-target.local.json
```

Ejemplo:

```json
{
  "github_repo": "https://github.com/usuario/repo.git",
  "github_branch": "main",
  "host": "IP_PUBLICA_EC2",
  "user": "ubuntu",
  "ssh_key_path": "C:/Users/Benjamin Cruzado/Downloads/llave.pem",
  "remote_app_dir": "/home/ubuntu/app",
  "app_port": 3000,
  "public_url": "http://IP_PUBLICA_EC2:3000",
  "allow_execute": false
}
```

Cuando `allow_execute` sea `true`, la fabrica queda autorizada para intentar publicar y desplegar.
