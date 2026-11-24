# YeastMode

[![CI](https://github.com/Tbubbs662/yeast-mode/actions/workflows/ci.yml/badge.svg)](https://github.com/Tbubbs662/yeast-mode/actions/workflows/ci.yml)

### Description
YeastMode is an app that allows home brewers to track their recipes, brew sessions, and inventory all in one place.

### Stack
- Django for App
- Postgres for the Database
- Docker 

### Features

- **Recipes:** grain bill, hop schedule, adjuncts and yeast, with target gravities and calculated ABV. Search by name or style, filter by brew type, and sort by recently updated, name, ABV or most brewed.
- **Brew sessions:** log each batch of a recipe with brew date, original and final gravity, ABV and notes.
- **Dashboard:** a board of fermenting, conditioning and ready batches. Each card shows the day count, days in its current status, OG/ABV and a one-click "Move to next status" button.
- **Needs attention:** the dashboard flags batches that have fermented for two weeks (check gravity) or conditioned for three (probably ready).
- **Brew history:** every batch you've brewed, with search, filters by status, type and year, and pagination.

### Screenshots

Screenshots use a demo account with sample data. To retake them with the app running, use `docs/screenshots/take.sh`.

**Dashboard:** batches that need attention, the status board and charts.

![YeastMode dashboard with a "Needs attention" list and a board of fermenting, conditioning and ready batches](docs/screenshots/dashboard.png)

**Recipes:** search, filter and sort your recipes.

![Recipe list with search, brew type filter and sort controls above six recipe cards](docs/screenshots/recipe-list.png)

**Brew session:** gravity readings, ABV and notes for a batch.

![Brew session page for a saison showing brew date, original and final gravity, ABV and notes](docs/screenshots/session-detail.png)

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
