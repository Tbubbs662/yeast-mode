#!/bin/bash
echo "Fixing Permissions..."
sudo chown -R $USER:$USER .

echo "Starting Docker..."
docker compose up -d

echo "Running migrations..."
docker compose exec web python manage.py migrate

echo "Opening browser..." 
xdg-open http://localhost:8000

echo "Done!"