import redis
import json
import os

redis_client = redis.Redis.from_url(os.getenv("REDIS_URL", "redis://localhost:6379/0"))

def get_cached_item(key: str):
    data = redis_client.get(key)
    if data:
        return json.loads(data)
    return None

def set_cached_item(key: str, value: dict, ttl: int = 3600):
    redis_client.setex(key, ttl, json.dumps(value))\n