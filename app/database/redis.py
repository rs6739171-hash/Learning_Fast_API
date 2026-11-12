from app.config import db_settings
from redis.asyncio import Redis

_redis_url = db_settings.REDIS_URL.strip().removeprefix("redis-cli -u").strip()
_db = Redis.from_url(url=_redis_url, decode_responses=True)

async def add_jti_to_blacklist(jti: str):
    if jti:
        await _db.set(jti, "blacklisted")

async def is_jti_blacklisted(jti: str) -> bool:
    if not jti:
        return False
    return bool(await _db.exists(jti))
