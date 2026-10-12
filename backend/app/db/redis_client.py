
import redis

from app.core.config import settings

redis_client = redis.Redis.from_url(
    settings.REDIS_URL,
    decode_responses=True,
    socket_connect_timeout=3,
    socket_timeout=3,
    health_check_interval=30,
)


def check_redis_connection() -> bool:
    try:
        return redis_client.ping()
    except redis.RedisError:
        return False
