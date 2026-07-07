# Publicacion Y Despliegue

La fabrica soporta un flujo completo:

```text
prompt
-> documentacion
-> validacion rubrica
-> codigo
-> pruebas
-> docker
-> github
-> ec2
-> validacion url
-> cierre
```

## GitHub

La fase `publish` usa `agent.github_publication`.

Puede preparar o ejecutar:

- `git add`;
- `git commit`;
- `git push`;
- registro en `git-publication.json`.

Para ejecutar push debe existir un remoto `origin` y configuracion local con `allow_execute: true`.

## Docker

La fase `containerize` usa `agent.docker_packaging`.

Genera:

- `deploy/Dockerfile`;
- `deploy/docker-compose.yml`;
- `deploy/.dockerignore`;
- `docker-validation.json`.

## EC2

La fase `deploy` usa `agent.deploy_ec2`.

Lee configuracion local desde:

`project/secrets/deploy-target.local.json`

Ese archivo no debe subirse a GitHub.

Si existe y `allow_execute` es `true`, la fabrica puede entrar por SSH, clonar/pullar el repo, ejecutar Docker Compose y validar la URL publica.
