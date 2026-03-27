# MQTT Resilience & Graceful Degradation

## Stratégie de Résilience

Les notifications MQTT sont **non-bloquantes** : si HiveMQ est indisponible, les transactions continuent normalement.

### Comportement

#### 1. **Initialisation**
- Si les credentials MQTT sont manquants → Warning + désactivation des notifications
- Si la connexion échoue → Error log + désactivation des notifications
- Les transactions continuent dans tous les cas

#### 2. **Publication de Notifications**
- Retourne `bool` : `True` si succès, `False` si échec
- En cas d'échec : log warning/error mais **ne lève pas d'exception**
- Les transactions ne sont jamais bloquées

#### 3. **Logs Explicites**
```
WARNING: MQTT client not initialized. Skipping notification for uuid-123. Transaction processing will continue normally.
ERROR: Error publishing notification to uuid-456: Connection refused. Transaction continues normally (graceful degradation).
```

## Configuration Requise

### Variables d'Environnement
```bash
# Production
MQTT_BROKER=c5f0da6ec4494a8ab443d2a73b2d3d47.s1.eu.hivemq.cloud
MQTT_PORT=8883
MQTT_USERNAME=your_username
MQTT_PASSWORD=your_password

# Dev/Test (notifications désactivées)
# Laisser vide pour désactiver MQTT
```

## Fallback Recommendations

### Court Terme (Actuel)
✅ Graceful degradation : transactions réussies même si MQTT down
✅ Logs clairs pour monitoring
✅ Client récupère les transactions via API REST

### Long Terme (Optionnel)
- **Retry Queue** : Redis/Celery pour retry automatique des notifications échouées
- **Fallback SMS** : Envoyer SMS pour transactions critiques si MQTT down
- **Health Check** : Endpoint `/health` qui vérifie MQTT status
- **Monitoring** : Alertes Sentry/DataDog si MQTT down > 5min

## Testing

### Test avec MQTT Désactivé
```bash
# .env
MQTT_BROKER=
MQTT_USERNAME=
MQTT_PASSWORD=

# Résultat attendu
# ✅ Transactions fonctionnent
# ⚠️ Logs: "MQTT credentials not configured. Notifications will be disabled."
```

### Test avec MQTT Inaccessible
```bash
# .env
MQTT_BROKER=invalid-broker.com
MQTT_PORT=1883
MQTT_USERNAME=test
MQTT_PASSWORD=test

# Résultat attendu
# ✅ Transactions fonctionnent
# ❌ Logs: "Failed to initialize MQTT: [Errno -2] Name or address not known. Notifications will be disabled but transactions will continue."
```

## Impact Production

### Scénarios
1. **HiveMQ Cloud down** → Notifications échouent, transactions OK ✅
2. **Credentials invalides** → Notifications désactivées, transactions OK ✅
3. **Quota MQTT dépassé** → Notifications échouent, transactions OK ✅

### Monitoring Recommandé
- Graphana/Prometheus : métriques `mqtt_publish_success` / `mqtt_publish_failed`
- Sentry : alertes sur logs `ERROR: Failed to publish notification`
- Uptime check : ping HiveMQ broker toutes les 5 min

## Conclusion

**Les notifications MQTT sont une feature "nice-to-have", pas "must-have".**

La résilience garantit que :
- ✅ Les transactions financières ne sont jamais bloquées
- ✅ Les échecs MQTT sont loggés pour investigation
- ✅ Le système reste opérationnel même si HiveMQ est down
