"""
Custom JWT authentication with blacklist support
"""
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken
from rest_framework_simplejwt.tokens import AccessToken


class BlacklistAwareJWTAuthentication(JWTAuthentication):
    """
    JWT Authentication that properly checks the blacklist
    """
    
    def get_validated_token(self, raw_token):
        """
        Validates an encoded JSON web token and returns a validated token
        wrapper object.
        """
        messages = []
        for AuthToken in self.get_auth_token_classes():
            try:
                # For AccessToken, we need to check the blacklist
                if AuthToken == AccessToken:
                    # Decode the token to get the JTI
                    token = AuthToken(raw_token)
                    jti = token.get('jti')
                    
                    # Check if the token is blacklisted
                    if jti and BlacklistedToken.objects.filter(token__jti=jti).exists():
                        print(f"DEBUG: Token with JTI {jti} is blacklisted!")
                        raise InvalidToken('Token is blacklisted')
                
                return AuthToken(raw_token)
            except TokenError as e:
                messages.append({'token_class': AuthToken.__name__,
                                'token_type': AuthToken.token_type,
                                'message': e.args[0]})

        raise InvalidToken({
            'detail': 'Given token not valid for any token type',
            'messages': messages,
        })
    
    def get_auth_token_classes(self):
        """
        Return the token classes that this authentication class supports.
        """
        from rest_framework_simplejwt.tokens import AccessToken, RefreshToken
        return [AccessToken, RefreshToken]
