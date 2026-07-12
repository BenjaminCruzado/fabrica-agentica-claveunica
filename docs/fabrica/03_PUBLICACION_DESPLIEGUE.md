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

- `deploy/docker-compose.yml`;
- `deploy/docker-compose.prebuilt.yml`;
- `deploy/.env.images.example`;
- `deploy/.dockerignore`;
- `.github/workflows/build-app-images.yml`;
- `app-generada/docker-compose.yml`;
- `app-generada/docker-compose.prebuilt.yml`;
- `app-generada/.env.images.example`;
- `app-generada/.dockerignore`;
- `app-generada/frontend/Dockerfile`;
- `app-generada/backend/Dockerfile`;
- `docker-validation.json`.

La carpeta que se ejecuta en EC2 es `app-generada/`.

Para probar localmente se puede usar:

```bash
docker compose up -d --build
```

Para EC2 se recomienda no construir en la instancia. Primero se publican imagenes con `.github/workflows/build-app-images.yml` o desde una maquina local, y EC2 ejecuta:

```bash
docker compose -f docker-compose.prebuilt.yml pull
docker compose -f docker-compose.prebuilt.yml up -d
```

## EC2

La fase `deploy` usa `agent.deploy_ec2`.

Lee configuracion local desde:

`project/secrets/deploy-target.local.json`

Ese archivo no debe subirse a GitHub.

Si existe y `allow_execute` es `true`, la fabrica puede entrar por SSH, clonar/pullar el repo, entrar a `app-generada/`, ejecutar Docker Compose y validar la URL publica.

El modo recomendado para evitar falta de disco en EC2 es:

```json
"deploy_strategy": "prebuilt_images"
```

En ese modo EC2 solo hace `pull` y `up`, no `up --build`.

Recomendacion practica: en `deploy-target.local.json` usa una URL HTTPS del repositorio para `github_repo`, asi EC2 no necesita una llave SSH de GitHub propia.
