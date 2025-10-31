from rest_framework.throttling import UserRateThrottle, AnonRateThrottle


class AuthRateThrottle(AnonRateThrottle):
    """
    Rate limiting pour les endpoints d'authentification (login, OTP)
    Limite: 10 requêtes par minute
    """
    scope = 'auth'


class TransactionRateThrottle(UserRateThrottle):
    """
    Rate limiting pour les transactions financières
    Limite: 50 requêtes par minute
    """
    scope = 'transactions'
