# Define the base command
DOCKER_COMPOSE = docker compose

# -----------------------------------------------------------------------------
# DEVELOPMENT
# Uses dev.env
# -----------------------------------------------------------------------------
dev:
	@echo "Starting Development Environment..."
	$(DOCKER_COMPOSE) --env-file dev.env -f docker-compose.dev.yaml up --build

dev-down:
	@echo "Stopping Development Environment..."
	$(DOCKER_COMPOSE) --env-file dev.env -f docker-compose.dev.yaml down

# -----------------------------------------------------------------------------
# PRODUCTION
# Uses .env
# -----------------------------------------------------------------------------
prod:
	@echo "Starting Production Environment..."
	$(DOCKER_COMPOSE) --env-file prod.env -f docker-compose.yaml up --build

prod-down:
	@echo "Stopping Production Environment..."
	$(DOCKER_COMPOSE) --env-file prod.env -f docker-compose.yaml down

# -----------------------------------------------------------------------------
# UTILS
# -----------------------------------------------------------------------------

help:
	@echo "Available commands:"
	@echo "  make dev       - Start development environment"
	@echo "  make dev-down  - Stop development environment"
	@echo "  make prod      - Start production environment"
	@echo "  make prod-down - Stop production environment"
