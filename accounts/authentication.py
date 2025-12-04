from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
from accounts.models import Profile


class APIKeyAuthentication(BaseAuthentication):
    """
    Autenticació basada en API-Key via header: X-API-Key
    Exemple d'ús:
    curl -H "X-API-Key: la_teva_clau_api" http://localhost:8000/api/posts/
    """
    def authenticate(self, request):
        # Obtenim l'API key del header X-API-Key
        api_key = request.headers.get('X-API-Key')
        if not api_key:
            raise AuthenticationFailed("Cal proporcionar una clau API vàlida")

        try:
            # Busquem el perfil que té aquesta API key
            profile = Profile.objects.select_related(
                'user').get(api_key=api_key)
        except Profile.DoesNotExist:
            raise AuthenticationFailed("Clau API no vàlida")
        except Exception as e:
            # Per capturar qualsevol altre error i evitar 500
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error en autenticació API Key: {str(e)}")
            raise AuthenticationFailed("Error en l'autenticació")

        # Retornem (user, None) per indicar autenticació correcta
        return (profile.user, None)

    def authenticate_header(self, request):  # type: ignore
        return 'X-API-Key'
