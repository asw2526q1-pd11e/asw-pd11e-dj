from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
from accounts.models import Profile  # <-- ajusta al teu projecte real


class APIKeyAuthentication(BaseAuthentication):
    """
    Autenticació basada en API-Key via header: X-API-Key
    """
    def authenticate(self, request):
        api_key = request.headers.get('X-API-Key')

        if not api_key:
            return None  # no hi ha header → prova altres autenticacions

        try:
            profile = Profile.objects.select_related('user'
                                                     ).get(api_key=api_key)
        except Profile.DoesNotExist:
            raise AuthenticationFailed("API Key no vàlida")

        # Torna un tuple (usuari, auth info)
        return (profile.user, None)
