.PHONY: help clean test run migrate makemigrations shell superuser install dev docker-build docker-up docker-down docker-logs

help:
	@echo "Commandes disponibles:"
	@echo "  make clean          - Nettoie les fichiers __pycache__, .pyc, .pyo"
	@echo "  make install        - Installe les dépendances"
	@echo "  make dev            - Lance le serveur de développement"
	@echo "  make migrate        - Applique les migrations"
	@echo "  make makemigrations - Crée de nouvelles migrations"
	@echo "  make shell          - Ouvre le shell Django"
	@echo "  make superuser      - Crée un super utilisateur"
	@echo "  make test           - Lance les tests"
	@echo "  make docker-build   - Build les conteneurs Docker"
	@echo "  make docker-up      - Démarre les conteneurs Docker"
	@echo "  make docker-down    - Arrête les conteneurs Docker"
	@echo "  make docker-logs    - Affiche les logs Docker"

clean:
	@echo "🧹 Nettoyage des fichiers Python..."
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.py~" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name ".DS_Store" -delete
	@echo "✅ Nettoyage terminé!"

install:
	@echo "📦 Installation des dépendances..."
	pip install -r requirements.txt
	@echo "✅ Dépendances installées!"

dev:
	@echo "🚀 Démarrage du serveur de développement..."
	python manage.py runserver

migrate:
	@echo "🔄 Application des migrations..."
	python manage.py migrate
	@echo "✅ Migrations appliquées!"

makemigrations:
	@echo "📝 Création des migrations..."
	python manage.py makemigrations
	@echo "✅ Migrations créées!"

shell:
	@echo "🐍 Ouverture du shell Django..."
	python manage.py shell

superuser:
	@echo "👤 Création d'un super utilisateur..."
	python manage.py createsuperuser

test:
	@echo "🧪 Lancement des tests..."
	python manage.py test

docker-build:
	@echo "🐳 Build des conteneurs Docker..."
	docker-compose build
	@echo "✅ Build terminé!"

docker-up:
	@echo "🐳 Démarrage des conteneurs Docker..."
	docker-compose up -d
	@echo "✅ Conteneurs démarrés!"

docker-down:
	@echo "🐳 Arrêt des conteneurs Docker..."
	docker-compose down
	@echo "✅ Conteneurs arrêtés!"

docker-logs:
	@echo "📋 Logs des conteneurs Docker..."
	docker-compose logs -f

docker-restart:
	@echo "🔄 Redémarrage des conteneurs Docker..."
	docker-compose restart
	@echo "✅ Conteneurs redémarrés!"

docker-clean:
	@echo "🧹 Nettoyage Docker complet..."
	docker-compose down -v
	@echo "✅ Nettoyage Docker terminé!"
