from authlib.jose import jwt
from flask import current_app
from authlib.jose import jwt
from datetime import datetime, timedelta



# 生成 token
def generate_token(data,SECRET_KEY,expires_in=3600):
    header = {'alg': 'HS256'}
    payload = data.copy()
    payload['exp'] = (datetime.utcnow() + timedelta(seconds=expires_in)).timestamp()
    return jwt.encode(header, payload, SECRET_KEY).decode('utf-8')

# 验证 token
def verify_token(token,SECRET_KEY):
    try:
        claims = jwt.decode(token,SECRET_KEY)
        # 检查过期
        if datetime.utcnow().timestamp() > claims['exp']:
            return None
        return claims
    except Exception:
        return None
