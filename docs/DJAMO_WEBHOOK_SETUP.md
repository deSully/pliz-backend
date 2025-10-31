# 🔔 Configuration Webhook Djamo

## 📍 Endpoint webhook
```
https://core.plizmoney.com/api/transaction/webhooks/djamo/
```

## 🔧 Enregistrement du webhook

Tu dois enregistrer ce webhook chez Djamo pour les 3 événements :

### 1. Transaction Started
```bash
curl -X POST \
  -H 'Authorization: Bearer <DJAMO_API_KEY>' \
  -H 'Content-type: application/json' \
  -d '{
    "topic": "transactions/started",
    "url": "https://core.plizmoney.com/api/transaction/webhooks/djamo/"
  }' \
  https://api.djamo.io/v1/webhooks
```

### 2. Transaction Completed
```bash
curl -X POST \
  -H 'Authorization: Bearer <DJAMO_API_KEY>' \
  -H 'Content-type: application/json' \
  -d '{
    "topic": "transactions/completed",
    "url": "https://core.plizmoney.com/api/transaction/webhooks/djamo/"
  }' \
  https://api.djamo.io/v1/webhooks
```

### 3. Transaction Failed
```bash
curl -X POST \
  -H 'Authorization: Bearer <DJAMO_API_KEY>' \
  -H 'Content-type: application/json' \
  -d '{
    "topic": "transactions/failed",
    "url": "https://core.plizmoney.com/api/transaction/webhooks/djamo/"
  }' \
  https://api.djamo.io/v1/webhooks
```

---

## ✅ Vérifier les webhooks enregistrés

```bash
curl -X GET \
  -H 'Authorization: Bearer <DJAMO_API_KEY>' \
  https://api.djamo.io/v1/webhooks
```

---

## 🧪 Tester le webhook

### En local (avec ngrok)
```bash
# 1. Démarrer ngrok
ngrok http 8000

# 2. Copier l'URL ngrok (ex: https://abc123.ngrok.io)

# 3. Enregistrer le webhook avec l'URL ngrok
curl -X POST \
  -H 'Authorization: Bearer <DJAMO_API_KEY>' \
  -H 'Content-type: application/json' \
  -d '{
    "topic": "transactions/completed",
    "url": "https://abc123.ngrok.io/api/transaction/webhooks/djamo/"
  }' \
  https://api.djamo.io/v1/webhooks

# 4. Faire une transaction de test
# 5. Observer les logs dans ngrok et ton serveur
```

---

## 🔒 Sécurité

Le webhook vérifie automatiquement la signature HMAC avec `DJAMO_SECRET_KEY`.

**Ne jamais exposer le SECRET_KEY !**

---

## 📊 Ce qui se passe

1. User fait un TopUp via Wave/Orange Money
2. Ton API appelle Djamo → Reçoit `status: "pending"`
3. Transaction stockée en `PENDING` dans ta DB
4. **Djamo traite le paiement mobile money**
5. **Djamo envoie un webhook `transactions/completed`**
6. Ton endpoint met à jour la transaction en `SUCCESS`
7. Notification MQTT envoyée à l'utilisateur
8. Frais appliqués
9. Wallet crédité

---

## 🐛 Debug

Logs à surveiller :
```bash
tail -f logs/transactions.log | grep Djamo
```

En cas d'erreur :
- Vérifier que `DJAMO_SECRET_KEY` est configuré
- Vérifier la signature HMAC
- Vérifier que la transaction existe (order_id)
- Vérifier les logs de Djamo (dashboard)
