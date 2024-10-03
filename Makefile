MANAGE = python manage.py

# List of fixtures in the correct loading order
FIXTURES_ORDERED = \
    apps/product_management/fixtures/001-product-fixture.json \
    apps/product_management/fixtures/002-producttree-fixture.json \
    apps/product_management/fixtures/003-productarea-fixture-part1.json \
    apps/product_management/fixtures/004-productarea-fixture-part2.json \
    apps/product_management/fixtures/005-misc-fixtures.json

help:
	@echo "help               -- Print this help showing all commands.         "
	@echo "run                -- run the django development server             "
	@echo "test               -- run all tests                                 "
	@echo "cov                -- run all tests with coverage                   "
	@echo "cov_html           -- run all tests with html coverage              "
	@echo "migrate            -- prepare migrations and migrate                "
	@echo "admin              -- Created superuser and it prompt for password  "
	@echo "seed               -- Seed or load data from each app		 	   "
	@echo "setup              -- load all the data from the fixture to the app "
	@echo "dumpdata           -- Backup the data from the running django app   "
	@echo "tailwindcss        -- Generate Tailwindcss 						   "


rmpyc:
	find . | grep -E "__pycache__|\.pyc|\.pyo" | xargs sudo rm -rf

run:
	$(MANAGE) runserver

migrate:
	$(MANAGE) makemigrations
	$(MANAGE) migrate

seed:
	${MANAGE} loaddata security talent
	for fixture in $(FIXTURES_ORDERED); do \
		${MANAGE} loaddata $$fixture; \
	done
	${MANAGE} loaddata apps/product_management/fixtures/006-bounty_fixtures.json
	${MANAGE} loaddata apps/product_management/fixtures/007-competition.json
	${MANAGE} loaddata canopy commerce engagement
	${MANAGE} loaddata apps/talent/fixtures/bountyclaim.json
	${MANAGE} loaddata apps/security/fixtures/product_role_assignment.json

setup:
	python reset_database.py
	make migrate
	${MANAGE} loaddata security talent
	for fixture in $(FIXTURES_ORDERED); do \
		${MANAGE} loaddata $$fixture; \
	done
	${MANAGE} loaddata apps/product_management/fixtures/006-bounty_fixtures.json
	${MANAGE} loaddata apps/product_management/fixtures/007-competition.json
	${MANAGE} loaddata canopy commerce engagement
	${MANAGE} loaddata apps/talent/fixtures/bountyclaim.json
	${MANAGE} loaddata apps/security/fixtures/product_role_assignment.json

	make test
dumpdata:
	${MANAGE} dumpdata canopy --output apps/canopy/fixtures/canopy.json
	${MANAGE} dumpdata commerce --output apps/commerce/fixtures/commerce.json
	${MANAGE} dumpdata engagement --output apps/engagement/fixtures/engagement.json
	${MANAGE} dumpdata product_management --output apps/product_management/fixtures/product_management.json
	${MANAGE} dumpdata security --output apps/security/fixtures/security.json
	${MANAGE} dumpdata talent --output apps/talent/fixtures/talent.json
	make format_fixtures

admin:
	$(MANAGE) createsuperuser --username=admin --email=admin@gmail.com

test:
	pytest .

tailwindcss:
	tailwindcss -o ./static/styles/tailwind.css --minify

format_fixtures:
	jsonformat 	apps/canopy/fixtures/canopy.json
	jsonformat	apps/commerce/fixtures/commerce.json
	jsonformat	apps/engagement/fixtures/engagement.json
	jsonformat	apps/product_management/fixtures/product_management.json
	jsonformat	apps/security/fixtures/security.json
	jsonformat	apps/talent/fixtures/talent.json

cov:
	pytest --cov

cov_html:
	pytest --cov  --cov-report html --cov-fail-under=50
