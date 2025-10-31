# 💰 Système de Gestion des Frais (Fees)

## 📋 Vue d'ensemble

Le système de frais permet de :
1. **Calculer** automatiquement les frais de transaction (fixe + pourcentage)
2. **Appliquer** les frais en débitant le client et créditant la plateforme
3. **Distribuer** les frais entre les acteurs (provider, bank, merchant)

---

## 🏗️ Architecture

### Modèles

#### 1. **TariffGrid** (Grille tarifaire)
```python
TariffGrid
├── name: "Grille Standard 2025"
├── is_active: True
└── created_at: timestamp
```
Une grille tarifaire contient plusieurs règles de frais.

#### 2. **Fee** (Règle de frais)
```python
Fee
├── tariff_grid: FK vers TariffGrid
├── transaction_type: "TRANSFER" | "PAYMENT" | "TOPUP"
├── min_amount: 0
├── max_amount: 10000
├── percentage: 2.5  # 2.5%
├── fixed_amount: 50  # 50 XOF
├── merchant: FK optionnel (pour règle spécifique)
├── bank: FK optionnel (pour règle spécifique)
└── is_active: True
```

**Logique de priorisation :**
1. Règle spécifique au marchand (si `merchant` renseigné)
2. Règle spécifique à la banque (si `bank` renseigné)
3. Règle globale (si `merchant=None` et `bank=None`)
4. Pas de frais (si aucune règle trouvée)

#### 3. **FeeDistributionRule** (Règle de répartition)
```python
FeeDistributionRule
├── transaction_type: "PAYMENT"
├── merchant: FK optionnel
├── bank: FK optionnel
├── provider_percentage: 70  # 70% va au provider
├── bank_percentage: 20      # 20% va à la banque
├── merchant_percentage: 10  # 10% va au marchand
└── is_active: True

# Total doit faire 100%
```

#### 4. **FeeDistribution** (Distribution effective)
```python
FeeDistribution
├── transaction: FK vers Transaction
├── actor_type: "provider" | "bank" | "merchant"
├── actor_id: ID de l'acteur (0 pour provider)
├── amount: 122.50  # Part de frais pour cet acteur
└── created_at: timestamp
```

---

## 🔄 Flow complet

### Étape 1 : Configuration (Admin Django)

```python
# 1. Créer une grille tarifaire
grid = TariffGrid.objects.create(
    name="Grille Standard 2025",
    is_active=True
)

# 2. Créer une règle de frais globale
Fee.objects.create(
    tariff_grid=grid,
    transaction_type="PAYMENT",
    min_amount=0,
    max_amount=10000,
    percentage=2.5,      # 2.5%
    fixed_amount=50,     # 50 XOF
    merchant=None,       # Règle globale
    bank=None,
    is_active=True
)

# 3. Créer une règle de frais spécifique pour un marchand
Fee.objects.create(
    tariff_grid=grid,
    transaction_type="PAYMENT",
    min_amount=0,
    max_amount=100000,
    percentage=1.5,      # Taux réduit pour ce marchand
    fixed_amount=25,
    merchant=merchant_airtime,  # Règle spécifique
    is_active=True
)

# 4. Créer une règle de distribution globale
FeeDistributionRule.objects.create(
    transaction_type="PAYMENT",
    provider_percentage=70,   # Provider garde 70%
    bank_percentage=20,       # Banque reçoit 20%
    merchant_percentage=10,   # Marchand reçoit 10%
    is_active=True
)

# 5. Règle de distribution spécifique pour un marchand
FeeDistributionRule.objects.create(
    transaction_type="PAYMENT",
    merchant=merchant_airtime,
    provider_percentage=60,   # Provider garde moins
    bank_percentage=15,
    merchant_percentage=25,   # Marchand garde plus
    is_active=True
)
```

### Étape 2 : Application automatique dans le code

**IMPORTANT : L'ordre des opérations**

```python
from transaction.services.fee import FeeService

# Dans ton serializer/service
# 1. Créer la transaction
transaction = TransactionService.create_pending_transaction(...)

# 2. Débiter/Créditer le MONTANT de la transaction
TransactionService.debit_wallet(sender_wallet, transaction.amount, transaction)
TransactionService.credit_wallet(receiver_wallet, transaction.amount, transaction)

# 3. Appliquer les FRAIS (APRÈS le débit/crédit principal)
fee_amount = FeeService.apply_fee(
    user=request.user,           # L'utilisateur qui paie
    wallet=sender_wallet,        # Le wallet à débiter (pour les frais)
    transaction=transaction,     # La transaction créée
    transaction_type="PAYMENT",  # Type de transaction
    merchant=merchant,           # Optionnel
    bank=bank                    # Optionnel
)

# 4. Finaliser
TransactionService.update_transaction_status(transaction, "SUCCESS")
```

**Ce que fait `apply_fee()` automatiquement :**
1. Trouve la bonne règle de frais (spécifique ou globale)
2. Calcule le montant : (amount × percentage) + fixed_amount
3. **Débite le wallet du client (pour les frais)**
4. **Crédite le wallet de la plateforme (collecte les frais)**
5. Met à jour `transaction.fee_applied`
6. Crée les `FeeDistribution` selon les règles de répartition

**Résultat final pour le client :**
```
Débit total du wallet = montant_transaction + fee_amount
```

---

## 📊 Exemple concret

### Scénario : Paiement de 5000 XOF chez un marchand

#### Configuration
```python
# Règle de frais pour ce marchand
Fee:
  percentage = 2.5%
  fixed_amount = 50 XOF
  
# Règle de distribution
FeeDistributionRule:
  provider_percentage = 70%
  bank_percentage = 20%
  merchant_percentage = 10%
```

#### Calcul
```python
# 1. Calcul du frais total
fee = (5000 × 2.5%) + 50
fee = 125 + 50
fee = 175 XOF

# 2. Distribution
provider_share = 175 × 70% = 122.50 XOF
bank_share     = 175 × 20% =  35.00 XOF
merchant_share = 175 × 10% =  17.50 XOF
Total                       = 175.00 XOF ✓

# 3. Mouvements de fonds
Client :      5000 (transaction) + 175 (frais) = -5175 XOF
Marchand :    +5000 XOF (reçoit le paiement)
Plateforme :  +175 XOF (collecte les frais)

# 4. Enregistrements créés
Transaction.fee_applied = 175 XOF

FeeDistribution #1:
  actor_type = "provider"
  actor_id = 0
  amount = 122.50 XOF

FeeDistribution #2:
  actor_type = "bank"
  actor_id = 15
  amount = 35.00 XOF

FeeDistribution #3:
  actor_type = "merchant"
  actor_id = 42
  amount = 17.50 XOF
```

---

## 🎯 Méthodes du FeeService

### 1. `get_applicable_fee(transaction_type, amount, merchant=None, bank=None)`
Trouve la règle de frais applicable selon la priorité.

**Retourne :** Objet `Fee` ou `None`

### 2. `calculate_fee_amount(fee, amount)`
Calcule le montant du frais à partir d'une règle.

**Formule :** `(amount × percentage / 100) + fixed_amount`

**Retourne :** `Decimal` arrondi à 2 décimales

### 3. `apply_fee(user, wallet, transaction, transaction_type, merchant=None, bank=None)`
**MÉTHODE PRINCIPALE** - Applique tout le processus automatiquement.

**Fait :**
1. Vérifie si l'utilisateur est abonné (si `user.is_subscribed = True` → pas de frais)
2. Trouve la règle de frais applicable
3. Calcule le montant du frais
4. Débite le wallet du client
5. Crédite le wallet de la plateforme
6. Met à jour `transaction.fee_applied`
7. Appelle `distribute_fee()` pour créer les distributions

**Retourne :** `Decimal` - Montant du frais appliqué

### 4. `distribute_fee(transaction, fee_amount, merchant=None, bank=None)`
Distribue les frais entre les acteurs selon les règles.

**Fait :**
1. Trouve la règle de distribution applicable
2. Calcule la part de chaque acteur
3. Crée les entrées `FeeDistribution`

**Retourne :** `list[FeeDistribution]` - Liste des distributions créées

### 5. `_create_distributions(transaction, fee_amount, rule, merchant, bank)` (privée)
Crée les entrées de distribution concrètes.

---

## 🔍 Vérification et debug

### Voir les frais appliqués à une transaction
```python
transaction = Transaction.objects.get(order_id="TRX123")
print(f"Frais appliqué : {transaction.fee_applied} XOF")

# Voir la distribution
distributions = FeeDistribution.objects.filter(transaction=transaction)
for dist in distributions:
    print(f"{dist.actor_type}: {dist.amount} XOF (ID: {dist.actor_id})")
```

### Tester le calcul sans appliquer
```python
fee = FeeService.get_applicable_fee(
    transaction_type="PAYMENT",
    amount=Decimal('10000'),
    merchant=None
)

if fee:
    amount = FeeService.calculate_fee_amount(fee, Decimal('10000'))
    print(f"Frais calculé : {amount} XOF")
```

### Voir toutes les règles actives
```python
# Toutes les règles de frais
fees = Fee.objects.filter(is_active=True)
for fee in fees:
    print(f"{fee.transaction_type} [{fee.min_amount}-{fee.max_amount}]")
    print(f"  Percentage: {fee.percentage}%, Fixed: {fee.fixed_amount}")
    print(f"  Target: {fee.merchant or fee.bank or 'Global'}")

# Toutes les règles de distribution
rules = FeeDistributionRule.objects.filter(is_active=True)
for rule in rules:
    print(f"{rule.transaction_type}")
    print(f"  Provider: {rule.provider_percentage}%")
    print(f"  Bank: {rule.bank_percentage}%")
    print(f"  Merchant: {rule.merchant_percentage}%")
    print(f"  Total: {rule.total_percentage()}%")
```

---

## ⚠️ Points importants

### 1. Utilisateurs abonnés
Si `user.is_subscribed = True`, **aucun frais n'est appliqué**.

### 2. Wallet plateforme
Il doit exister un wallet avec `is_platform=True` pour collecter les frais.

### 3. Arrondissement
Tous les montants sont arrondis à 2 décimales (`.quantize(Decimal('0.01'))`).

### 4. Atomicité
`apply_fee()` utilise `@db_transaction.atomic` pour garantir que tout se passe ou rien.

### 5. Logs
Le service log toutes les opérations importantes :
```python
logger.info(f"Fee of {fee_amount} applied to transaction {transaction.order_id}")
logger.warning(f"No distribution rule found for transaction {transaction.order_id}")
logger.error(f"Error distributing fee: {e}")
```

---

## 📝 Checklist d'implémentation

### Configuration initiale
- [ ] Créer une `TariffGrid` active
- [ ] Créer au moins une règle `Fee` globale par type de transaction
- [ ] Créer au moins une `FeeDistributionRule` globale
- [ ] Créer un wallet plateforme (`is_platform=True`)

### Dans le code
- [ ] Importer `FeeService`
- [ ] Appeler `FeeService.apply_fee()` après la création de la transaction
- [ ] Vérifier que `transaction.fee_applied` est bien mis à jour
- [ ] Tester avec un utilisateur abonné (pas de frais)

### Tests
- [ ] Tester le calcul des frais
- [ ] Tester la distribution entre acteurs
- [ ] Tester avec règle globale vs règle spécifique
- [ ] Tester avec utilisateur abonné
- [ ] Vérifier les logs

---

## 🚀 Prochaines améliorations possibles

1. **Dashboard des fees** : Visualiser les fees collectés par période
2. **API de statistiques** : Voir la répartition des fees par acteur
3. **Règles dynamiques** : Changer les pourcentages sans redéployer
4. **Plafonds** : Limite max de frais par transaction
5. **Promotions** : Réduction temporaire des frais pour certains marchands
