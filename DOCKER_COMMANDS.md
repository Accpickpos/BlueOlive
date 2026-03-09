# Docker Commands for BlueOlive Application

## Start all services (first time or after reset)
```bash
docker-compose up -d
```

## Start only the backend (if frontend is running locally)
```bash
docker-compose up -d backend
```

## Start only the frontend (if backend is running locally)
```bash
docker-compose up -d frontend
```

## Stop all services
```bash
docker-compose down
```

## Stop and remove volumes (full reset - WARNING: deletes database)
```bash
docker-compose down -v
```

## Rebuild and restart a specific service
```bash
# Rebuild backend
docker-compose build backend
docker-compose up -d --force-recreate backend

# Rebuild frontend
docker-compose build frontend
docker-compose up -d --force-recreate frontend
```

## View logs
```bash
# All services
docker-compose logs

# Specific service
docker-compose logs -f backend
docker-compose logs -f frontend

# Last 50 lines
docker logs blueolive-backend --tail 50
docker logs blueolive-frontend --tail 50
```

## Check container status
```bash
docker ps
```

## Access the application
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000

## Common troubleshooting
# Restart a specific container
docker restart blueolive-frontend
docker restart blueolive-backend

# Check if a service is responding
curl http://localhost:8000/api/v1/users/auth/profile/
curl http://localhost:3000

## Memory Issues (ENOMEM)
If you encounter ENOMEM errors, try the following:

### 1. Increase Docker Desktop/Engine memory limits
- **Docker Desktop (Windows/Mac)**: Settings > Resources > Memory (allocate at least 6GB)
- **Docker Engine (Linux)**: Edit `/etc/docker/daemon.json` and add `"default-shm-size": "4g"`

### 2. Rebuild containers with new memory limits
```bash
docker-compose down
docker-compose build --no-cache frontend
docker-compose up -d
```

### 3. Clear Docker cache
```bash
docker system prune -a
```

### 4. Check container memory usage
```bash
docker stats
```

### 5. Run frontend in production mode (less memory intensive)
Edit docker-compose.yml and change the frontend command to use `npm run start` instead of `npm run dev`
