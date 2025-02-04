from datetime import datetime, timedelta, timezone
from jose import JWTError, jwt

SECRET_KEY = "your-secret-key-here"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7

def create_access_token(data: dict) -> str:
    # Header
    header = {
        "alg": ALGORITHM,
        "typ": "JWT"
    }
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({
        "exp": expire,
        "iat": datetime.now(timezone.utc),  # timezone-aware UTC time
        "type": "access"          # token type
    })
    
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM, headers=header)