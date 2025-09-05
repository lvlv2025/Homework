from authlib.jose import jwt
from datetime import datetime, timedelta, timezone
import time

# =========================
# Token 生成与验证
# =========================
def generate_token(data, SECRET_KEY, expires_in=3600):
    """生成 JWT token"""
    header = {'alg': 'HS256'}
    payload = data.copy()
    now = datetime.now(timezone.utc)
    payload['exp'] = int((now + timedelta(seconds=expires_in)).timestamp())
    token = jwt.encode(header, payload, SECRET_KEY)
    if isinstance(token, bytes):
        token = token.decode('utf-8')
    return token

def verify_token(token, SECRET_KEY):
    """验证 JWT token"""
    try:
        claims = jwt.decode(token, SECRET_KEY)
        claims.validate()  # 检查 exp 等字段
        exp = claims.get('exp')
        now = int(time.time())
        print(f"验证 token: 当前 UTC 时间={now}, token exp={exp}")
        if exp and now > exp:
            print("Token 已过期 ")
            return None
        print("Token 验证成功")
        return claims
    except Exception as e:
        print("Token 验证失败:", e)
        return None
