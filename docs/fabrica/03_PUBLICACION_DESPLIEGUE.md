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
- `app-generada/Dockerfile`;
- `app-generada/docker-compose.yml`;
- `app-generada/.dockerignore`;
- `docker-validation.json`.

La carpeta que se ejecuta en EC2 es `app-generada/`.

## EC2

La fase `deploy` usa `agent.deploy_ec2`.

Lee configuracion local desde:

`project/secrets/deploy-target.local.json`

Ese archivo no debe subirse a GitHub.

Si existe y `allow_execute` es `true`, la fabrica puede entrar por SSH, clonar/pullar el repo, entrar a `app-generada/`, ejecutar Docker Compose y validar la URL publica.

Recomendacion practica: en `deploy-target.local.json` usa una URL HTTPS del repositorio para `github_repo`, asi EC2 no necesita una llave SSH de GitHub propia.
