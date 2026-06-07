# YeastMode

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