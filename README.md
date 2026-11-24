# YeastMode

[![CI](https://github.com/Tbubbs662/yeast-mode/actions/workflows/ci.yml/badge.svg)](https://github.com/Tbubbs662/yeast-mode/actions/workflows/ci.yml)

### Description
YeastMode is an app that allows home brewers to track their recipes, brew sessions, and inventory all in one place.

### Stack
- Django for App
- Postgres for the Database
- Docker 

### Features

#### Current
- Recipe list where you can keep track of all your recipes.
- Session tracking with statuses of where each session is at in the process. 
- Navigation between your dashboard, recipe list and sessions.
- Dashboard that shows all current sessions separated by their status. 

### How to Run

#### Prerequisites
- Docker installed
- Docker Compose installed
- Git installed

1. Clone the repository locally. Run `git clone https://github.com/Tbubbs662/yeast-mode.git`
2. Navigate into the folder with `cd yeast-mode`
3. Start Docker with `docker compose up -d`
4. Run migrations with `docker compose exec web python manage.py migrate`
5. Create a super user with `docker compose exec web python manage.py createsuperuser`
6. Open `http://localhost:8000` in your browser. 

After initial setup, you can use `./dev.sh` to start the app each time. (dev.sh is meant for linux. Windows users will need to run the commands manually to start the app.)

### Configuration

Settings come from environment variables. `docker-compose.yml` sets them all for local development, so you only need these when running the app somewhere else.

| Variable | Required | Default | Notes |
|---|---|---|---|
| `DATABASE_URL` | Yes | none | e.g. `postgres://user:password@host:5432/yeastmode` |
| `SECRET_KEY` | Yes, unless `DEBUG` is on | development key when `DEBUG` is on | Use a long random value. The app refuses to start without one, or with the development key, when `DEBUG` is off. |
| `DEBUG` | No | `False` | Turn on only for local development; it shows detailed error pages. |
| `DJANGO_ALLOWED_HOSTS` | No | `localhost,127.0.0.1` | Comma-separated host names the site is served on. |

To generate a secret key:

```
docker compose exec web python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```
