# Notifications temps réel (MQTT)

## Résumé rapide

1. Au login, tu reçois un champ `uuid`
2. Tu te connectes au broker MQTT
3. Tu t'abonnes au topic `pliz/{uuid}/notifications`
4. Tu reçois des notifications en temps réel
5. Tu affiches le `title` et `message` à l'utilisateur

---

## Récupération de l'UUID

### Réponse Login
```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "uuid": "550e8400-e29b-41d4-a716-446655440000",
  "phone_number": "+221771234567"
}
```

---

## Configuration MQTT

```
Broker: c5f0da6ec4494a8ab443d2a73b2d3d47.s1.eu.hivemq.cloud
Port TLS: 8883
Port WebSocket: 8884
Topic: pliz/{user_uuid}/notifications
```

---

## Format des messages

```json
{
  "type": "transaction",
  "title": "Envoi réussi",
  "message": "Envoi de 5000 FCFA réussi",
  "data": {
    "action": "send_money",
    "status": "success",
    "transaction_id": "PLZ-123",
    "amount": 5000.0
  }
}
```

---

## 🔔 Types de messages

### Type: `transaction`
Toutes les notifications liées aux transactions

**Actions possibles (`data.action`):**
- `send_money` - Envoi d'argent
- `receive_money` - Réception d'argent
- `topup` - Recharge de compte
- `payment` - Paiement marchand

**Status possibles (`data.status`):**
- `pending` - En cours
- `success` - Réussi
- `failed` - Échoué

### Type: `system`
Messages système (maintenance, mises à jour, etc.)

