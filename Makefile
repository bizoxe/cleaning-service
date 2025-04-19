prod:
	TARGET_ENV=production docker compose build
	POSTGRES_PASSWORD=supersecretpassword docker compose up -d

dev:
	TARGET_ENV=development docker compose build
	POSTGRES_PASSWORD=supersecretpassword docker compose up -d

keys:
	mkdir -p fastapi-application/certs
	rm -f fastapi-application/certs/jwt-private.pem fastapi-application/certs/jwt-public.pem
	openssl genrsa -out fastapi-application/certs/jwt-private.pem 2048
	openssl rsa -in fastapi-application/certs/jwt-private.pem -outform PEM -pubout -out fastapi-application/certs/jwt-public.pem

init_roles:
	docker exec -it fastapi-cleaning-service alembic upgrade head
	docker exec -it fastapi-cleaning-service python commands.py

stop:
	docker compose stop

up:
	docker compose up -d

down:
	docker compose down

test:
	docker compose run app test
