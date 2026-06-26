# WeaponMerchant Docker Setup

This guide will help you run the WeaponMerchant application in a Docker container on Ubuntu.

## Prerequisites

1. Docker installed on Ubuntu
2. Docker Compose (optional but recommended)
3. Git (for cloning)

### Install Docker on Ubuntu

```bash
# Update apt
sudo apt-get update

# Install Docker
sudo apt-get install -y docker.io docker-compose

# Add your user to the docker group (optional - avoid using sudo)
sudo usermod -aU docker $USER
newgrp docker
```

## Setup Instructions

### 1. Clone the Repository

```bash
git clone https://github.com/Kantarellen1/WeaponMerchant.git
cd WeaponMerchant
```

### 2. Build and Run with Docker Compose (Recommended)

```bash
# Build and start the container
docker-compose up -d

# View logs
docker-compose logs -f

# Stop the container
docker-compose down
```

### 3. Alternative: Build and Run with Docker CLI

```bash
# Build the image
docker build -t weapon-merchant .

# Run the container
docker run -d \
  --name weapon-merchant \
  -p 8000:8000 \
  -v $(pwd)/character:/app/character \
  -v $(pwd)/merchants:/app/merchants \
  -v $(pwd)/auction_house:/app/auction_house \
  -v $(pwd)/static:/app/static \
  -v $(pwd)/lore:/app/lore \
  -v $(pwd)/guilds:/app/guilds \
  weapon-merchant

# View logs
docker logs -f weapon-merchant

# Stop the container
docker stop weapon-merchant
```

## Accessing the Application

Once the container is running, access the application at:

- **Home**: http://localhost:8000/
- **Town Square**: http://localhost:8000/town
- **Smithy**: http://localhost:8000/smithy
- **Apothecary**: http://localhost:8000/apothecary
- **General Store**: http://localhost:8000/general-store
- **Auction House**: http://localhost:8000/auction-house

## Useful Docker Commands

```bash
# List running containers
docker ps

# List all containers
docker ps -a

# Remove a container
docker rm <container_id>

# View container logs
docker logs <container_id>

# Execute command in running container
docker exec -it <container_id> bash

# Remove image
docker rmi weapon-merchant
```

## Troubleshooting

### Port 8000 already in use
Change the port mapping in docker-compose.yml:
```yaml
ports:
  - "8001:8000"  # Access at http://localhost:8001
```

### Permission denied errors
Run with sudo or add your user to the docker group:
```bash
sudo usermod -aU docker $USER
```

### Container exits immediately
Check the logs:
```bash
docker logs <container_id>
```

## Notes

- The container uses Python 3.11
- All data volumes are mounted so changes persist
- The application runs on port 8000 inside the container
