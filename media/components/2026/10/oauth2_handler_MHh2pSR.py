"""
OAuth2 Grant Handler Utility
"""
import urllib.parse
import json

class OAuth2Client:
    def __init__(self, client_id, client_secret, auth_url, token_url):
        self.client_id = client_id
        self.client_secret = client_secret
        self.auth_url = auth_url
        self.token_url = token_url

    def get_authorization_url(self, redirect_uri: str, state: str, scope: str = 'read') -> str:
        params = {
            'client_id': self.client_id,
            'redirect_uri': redirect_uri,
            'response_type': 'code',
            'state': state,
            'scope': scope,
        }
        return f"{self.auth_url}?{urllib.parse.urlencode(params)}"
