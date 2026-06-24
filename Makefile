COMPOSE=docker compose

.PHONY: up down logs ps build smoke

build:
	$(COMPOSE) build

up:
	$(COMPOSE) up -d --build

down:
	$(COMPOSE) down

logs:
	$(COMPOSE) logs -f

ps:
	$(COMPOSE) ps

smoke:
	curl http://localhost:8080/healthz
