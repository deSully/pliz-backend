# 🚀 Guide de Déploiement Production - PlizBack

## 📋 Checklist Pré-Déploiement

### 1. ⚙️ Configuration du fichier `.env` (OBLIGATOIRE)

Copier le fichier exemple et le remplir :
```bash
cp .env.example .env
nano .env  # ou vim .env
```

#### 🔴 Variables CRITIQUES (à changer ABSOLUMENT)

```bash
# Django - CHANGER IMPÉRATIVEMENT
SECRET_KEY=GÉNÉRER_UNE_CLÉ_SECRÈTE_ALÉATOIRE_ICI  # ⚠️ 50+ caractères aléatoires
DEBUG=False  # ⚠️ JAMAIS True en production
ALLOWED_HOSTS=core.plizmoney.com  # ⚠️ Pas de wildcard *

# Base de données
POSTGRES_DB=plizback_prod
POSTGRES_USER=plizback_user
POSTGRES_PASSWORD=MOT_DE_PASSE_FORT_ICI  # ⚠️ Min 16 caractères
DB_HOST=db
DB_PORT=5432
WEB_PORT=8000
```

#### 🟠 Variables IMPORTANTES (API Providers)

```bash
# DJAMO (Wave + Orange Money via Djamo)
DJAMO_ACCESS_TOKEN=at_xxxxxxxxxxxxx  # Token commençant par "at_"
DJAMO_SECRET_KEY=sk_xxxxxxxxxxxxx    # Pour validation HMAC webhooks
DJAMO_COMPANY_ID=comp_xxxxxxxxxxxxx  # ID de votre entreprise
DJAMO_API_BASE_URL=https://api.djamo.io

# SamirPay (Woyofal, Rapido, Airtime)
SAMIR_API_KEY=votre_clé_api_samir
SAMIR_API_BASE_URL=https://api.samirpay.com/api/account/v1
SAMIR_SECRET_KEY=votre_secret_samir

# MTN Mobile Money
MTN_API_KEY=votre_clé_mtn
MTN_API_BASE_URL=https://api.mtn.com  # URL production (pas sandbox)
MTN_SUBSCRIPTION_KEY=votre_subscription_key
MTN_API_USER=votre_user_id
MTN_API_SECRET=votre_secret
```

#### 🟡 Variables UTILES (Features optionnelles)

```bash
# OTP (Activation email/SMS)
FF_OTP_SENDING_ENABLED=True  # Mettre True en prod
OTP_SECRET_KEY=GÉNÉRER_UNE_CLÉ_ALÉATOIRE

# MQTT / HiveMQ Cloud (Notifications temps réel)
MQTT_BROKER=c5f0da6ec4494a8ab443d2a73b2d3d47.s1.eu.hivemq.cloud
MQTT_PORT=8883
MQTT_USERNAME=votre_username_hivemq
MQTT_PASSWORD=votre_password_hivemq
MQTT_USE_TLS=True

# CORS (URLs Frontend autorisées)
CORS_ALLOWED_ORIGINS=https://app.plizmoney.com,https://admin.plizmoney.com

# Security
CSRF_TRUSTED_ORIGINS=https://core.plizmoney.com
SECURE_SSL_REDIRECT=True  # ⚠️ Activer après config SSL

# Logging
LOG_LEVEL=INFO  # ou WARNING en prod
```

---

### 2. 🔐 Générer une SECRET_KEY sécurisée

```bash
# Option 1: Python
python -c "import secrets; print(secrets.token_urlsafe(50))"

# Option 2: Django
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"

# Option 3: OpenSSL
openssl rand -base64 64
```

Copier le résultat dans `.env` → `SECRET_KEY=...`

---

### 3. 📁 Créer les dossiers nécessaires

```bash
# Logs (important pour Docker)
mkdir -p logs
touch logs/transaction.log
touch logs/errors.log
chmod -R 755 logs/

# Certificats SSL (Let's Encrypt)
mkdir -p certs
mkdir -p acme-data

# Static files
mkdir -p staticfiles
mkdir -p media
```

---

### 4. 🐳 Déploiement avec Docker Compose

#### Première installation

```bash
# 1. Build les images
docker-compose build

# 2. Démarrer les services
docker-compose up -d

# 3. Vérifier que tout tourne
docker-compose ps

# 4. Voir les logs
docker-compose logs -f web
```

#### Appliquer les migrations

```bash
docker-compose exec web python manage.py migrate
```

#### Créer un super utilisateur

```bash
docker-compose exec web python manage.py createsuperuser
```

#### Collecter les fichiers statiques

```bash
docker-compose exec web python manage.py collectstatic --noinput
```

---

### 5. 🔗 Enregistrer les Webhooks Djamo

**Après le déploiement et une fois l'API accessible** :

```bash
# Via Makefile (recommandé)
docker-compose exec web make setup-webhooks

# Ou directement
docker-compose exec web python manage.py setup_djamo_webhooks --base-url https://core.plizmoney.com

# Vérifier l'enregistrement
docker-compose exec web make list-webhooks
```

Les webhooks enregistrés :
- `transactions/started` → https://core.plizmoney.com/api/transaction/webhooks/djamo/
- `transactions/completed` → https://core.plizmoney.com/api/transaction/webhooks/djamo/
- `transactions/failed` → https://core.plizmoney.com/api/transaction/webhooks/djamo/

---

### 6. ✅ Tests Post-Déploiement

#### Health Check

```bash
curl https://core.plizmoney.com/api/health/
```

Réponse attendue :
```json
{
  "status": "healthy",
  "database": "connected",
  "timestamp": "2025-10-31T12:00:00Z"
}
```

#### Swagger API Documentation

Ouvrir dans le navigateur :
```
https://core.plizmoney.com/swagger/
```

#### Test Transaction (Topup)

```bash
# 1. Créer un compte
curl -X POST https://core.plizmoney.com/api/actor/register/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@plizmoney.com",
    "password": "TestPassword123!",
    "phone_number": "+221771234567",
    "first_name": "Test",
    "last_name": "User"
  }'

# 2. Se connecter
curl -X POST https://core.plizmoney.com/api/actor/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@plizmoney.com",
    "password": "TestPassword123!"
  }'

# 3. Faire une recharge (avec le token obtenu)
curl -X POST https://core.plizmoney.com/api/transaction/topup/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "amount": 1000,
    "phone_number": "+221771234567",
    "provider": "wave"
  }'
```

---

### 7. 📊 Monitoring et Logs

#### Voir les logs en temps réel

```bash
# Logs globaux
docker-compose logs -f

# Logs de l'application seulement
docker-compose logs -f web

# Logs de la base de données
docker-compose logs -f db

# Logs fichiers (transactions)
docker-compose exec web tail -f logs/transaction.log

# Logs fichiers (erreurs)
docker-compose exec web tail -f logs/errors.log
```

#### Surveiller les webhooks

```bash
# Filtrer les logs webhooks
docker-compose exec web tail -f logs/transaction.log | grep "webhook"
```

---

### 8. 🔄 Mises à jour et Redéploiement

```bash
# 1. Récupérer les derniers changements
git pull origin main

# 2. Rebuild si changements dans Dockerfile/requirements.txt
docker-compose build web

# 3. Redémarrer les services
docker-compose restart web

# 4. Appliquer nouvelles migrations si nécessaire
docker-compose exec web python manage.py migrate

# 5. Recollecte des static files
docker-compose exec web python manage.py collectstatic --noinput
```

---

### 9. 🛡️ Sécurité Post-Déploiement

#### Vérifications importantes

- [ ] `DEBUG=False` dans `.env`
- [ ] `SECRET_KEY` unique et complexe (50+ chars)
- [ ] `ALLOWED_HOSTS` limité aux domaines réels
- [ ] `SECURE_SSL_REDIRECT=True` après config SSL
- [ ] Certificats SSL actifs (Let's Encrypt via acme-companion)
- [ ] Firewall configuré (ports 80, 443 ouverts uniquement)
- [ ] PostgreSQL accessible uniquement depuis le conteneur web
- [ ] Variables `.env` jamais commitées dans Git

#### Tester la sécurité SSL

```bash
# Vérifier le certificat SSL
curl -I https://core.plizmoney.com

# Test SSL Labs (optionnel mais recommandé)
# Ouvrir : https://www.ssllabs.com/ssltest/analyze.html?d=core.plizmoney.com
```

---

### 10. 📞 Support et Dépannage

#### Problèmes fréquents

**❌ 502 Bad Gateway**
```bash
# Vérifier que web est démarré
docker-compose ps
docker-compose restart web
```

**❌ Database connection error**
```bash
# Vérifier les credentials dans .env
docker-compose exec db psql -U plizback_user -d plizback_prod
```

**❌ Webhooks non reçus**
```bash
# Vérifier que les webhooks sont enregistrés
docker-compose exec web make list-webhooks

# Re-enregistrer si nécessaire
docker-compose exec web make delete-webhooks
docker-compose exec web make setup-webhooks
```

**❌ Logs introuvables**
```bash
# Vérifier permissions
docker-compose exec web ls -la logs/
docker-compose exec web chmod -R 755 logs/
```

#### Commandes utiles

```bash
# Arrêter tous les services
docker-compose down

# Arrêter et supprimer volumes (⚠️ efface la DB)
docker-compose down -v

# Reconstruire tout from scratch
docker-compose down
docker-compose build --no-cache
docker-compose up -d

# Accéder au shell du conteneur
docker-compose exec web bash

# Accéder au shell Django
docker-compose exec web python manage.py shell

# Backup de la base de données
docker-compose exec db pg_dump -U plizback_user plizback_prod > backup.sql

# Restore de la base de données
cat backup.sql | docker-compose exec -T db psql -U plizback_user plizback_prod
```

---

## 🎯 Checklist Finale Avant Go-Live

- [ ] Fichier `.env` configuré avec toutes les variables
- [ ] `DEBUG=False` et `SECRET_KEY` unique
- [ ] Services Docker démarrés (`docker-compose ps`)
- [ ] Migrations appliquées
- [ ] Super utilisateur créé
- [ ] Static files collectés
- [ ] SSL/HTTPS fonctionnel
- [ ] Health check répond `/api/health/`
- [ ] Webhooks Djamo enregistrés
- [ ] Test d'une transaction end-to-end réussie
- [ ] Logs accessibles et monitored
- [ ] Backup automatique configuré (optionnel)

---

## 📚 Ressources

- **Documentation API** : https://core.plizmoney.com/swagger/
- **Logs** : `docker-compose logs -f web`
- **Health Check** : https://core.plizmoney.com/api/health/
- **Admin Django** : https://core.plizmoney.com/admin/

---

## 🆘 Contact Technique

En cas de problème critique :
1. Vérifier les logs : `docker-compose logs -f`
2. Vérifier le health check : `curl https://core.plizmoney.com/api/health/`
3. Redémarrer les services : `docker-compose restart`

---

**🎉 Bon déploiement ! 🚀**
