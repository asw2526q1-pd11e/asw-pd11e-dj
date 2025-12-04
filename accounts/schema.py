from drf_spectacular.extensions import OpenApiAuthenticationExtension

class APIKeyScheme(OpenApiAuthenticationExtension):
    target_class = 'accounts.authentication.APIKeyAuthentication'
    name = 'APIKeyAuth'

    def get_security_definition(self, auto_schema):
        return {
            'type': 'apiKey',
            'name': 'X-API-Key',
            'in': 'header',
        }
