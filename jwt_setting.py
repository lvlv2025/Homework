from authlib.jose import jwt
from datetime import datetime, timedelta


# 生成 token
def generate_token(data, SECRET_KEY, expires_in=3600):
    header = {'alg': 'HS256'}
    payload = data.copy()
    payload['exp'] = int((datetime.utcnow() + timedelta(seconds=expires_in)).timestamp())
    token = jwt.encode(header, payload, SECRET_KEY)
    if isinstance(token, bytes):
        token = token.decode('utf-8')
    return token

# 验证 token
def verify_token(token, SECRET_KEY):
    try:
        claims = jwt.decode(token, SECRET_KEY)
        claims.validate()  # 验证过期时间等
        return claims
    except Exception:
        return None
