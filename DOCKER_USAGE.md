# Docker Usage Guide for BlueOlive

## Prerequisites
- Docker and Docker Compose installed

## 1. Build and Start All Services

```
docker-compose up --build
```
- This will start backend (Django), frontend (Next.js), celery worker, redis, and postgres.

## 2. Stopping Services

```
docker-compose down
```

## 3. Accessing Services
- **Backend (Django):** http://localhost:8000
- **Frontend (Next.js):** http://localhost:3000
- **Postgres:** localhost:5432 (user: postgres, password: '0660089932@G', db: blue_olive)
- **Redis:** localhost:6379

## 4. Environment Variables
- Backend environment variables are in `backend/core/.env`.
- Database and Redis URLs are set for Docker networking.

## 5. Running Commands in Containers
- Example: Run Django migrations
  ```
  docker-compose exec backend python manage.py migrate
  ```
- Example: Open a shell in the backend
  ```
  docker-compose exec backend bash
  ```

## 6. Data Persistence
- Postgres and Redis data are stored in Docker volumes (`postgres_data`, `redis_data`).

---

For any issues, check logs with:
```
docker-compose logs -f
```
