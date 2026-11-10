from app.config import db_settings
from redis.asyncio import Redis

_db = Redis.from_url(url=db_settings.REDIS_URL,decode_response=True)

async def add_jti_to_blacklist(jti:str):
    _db.set(jti,"blacklisted")

async def is_jti_blacklisted(jti:str)->bool:
    return await _db.exists(jti)