from fastapi import HTTPException
from uuid import uuid4
import uuid
from datetime import datetime
from datetime import timedelta
from datetime import timezone
from app.config import security_settings as st
import jwt

def generate_access_token(data:dict,expiry:timedelta=timedelta(minutes=30)):
    jti = str(uuid4())
    return jwt.encode(
            payload={
                **data,
                "jti": jti,
                "jwt": jti,
                "exp":datetime.now(timezone.utc) + expiry
            },
            algorithm= st.JWT_ALGORITHM,
            key= st.JWT_SECRET)

# creating decode access ;function
def decode_access_token(token:str)->dict | None:
    try:
        return jwt.decode(
            jwt=token,
            algorithms=[st.JWT_ALGORITHM],
            key=st.JWT_SECRET
        )
    except  jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code = 401,
            detail= "Expired Token"
   )     
    except jwt.PyJWTError:
        return None