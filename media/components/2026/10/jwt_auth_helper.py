"""
JWT Authentication Helper Module
Reusable component for HMAC-SHA256 JWT creation and validation.
"""
import hmac
import hashlib
import base64
import json
import time

def b64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b'=').decode('utf-8')

def b64url_decode(data: str) -> bytes:
    padding = '=' * (4 - (len(data) % 4))
    return base64.urlsafe_b64decode(data + padding)

def create_jwt(payload: dict, secret: str, expires_in_sec: int = 3600) -> str:
    header = {"alg": "HS256", "typ": "JWT"}
    payload_copy = payload.copy()
    payload_copy['exp'] = int(time.time()) + expires_in_sec
    payload_copy['iat'] = int(time.time())

    h_enc = b64url_encode(json.dumps(header).encode('utf-8'))
    p_enc = b64url_encode(json.dumps(payload_copy).encode('utf-8'))
    signing_input = f"{h_enc}.{p_enc}".encode('utf-8')
    
    signature = hmac.new(secret.encode('utf-8'), signing_input, hashlib.sha256).digest()
    s_enc = b64url_encode(signature)
    return f"{h_enc}.{p_enc}.{s_enc}"

def verify_jwt(token: str, secret: str) -> dict:
    parts = token.split('.')
    if len(parts) != 3:
        raise ValueError("Invalid token format")
    h_enc, p_enc, s_enc = parts
    signing_input = f"{h_enc}.{p_enc}".encode('utf-8')
    expected_sig = hmac.new(secret.encode('utf-8'), signing_input, hashlib.sha256).digest()
    actual_sig = b64url_decode(s_enc)
    
    if not hmac.compare_digest(expected_sig, actual_sig):
        raise ValueError("Signature mismatch")
        
    payload = json.loads(b64url_decode(p_enc).decode('utf-8'))
    if 'exp' in payload and time.time() > payload['exp']:
        raise ValueError("Token expired")
    return payload
