from rest_framework_simplejwt.tokens import RefreshToken

class TokenService:
    @staticmethod
    def generate_tokens_for_user(user):
        """
        Génère des tokens JWT pour un utilisateur donné.
        """
        refresh = RefreshToken.for_user(user)
        return {
            "refresh": str(refresh),
            "access": str(refresh.access_token),
        }
