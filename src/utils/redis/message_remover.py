from typing import Optional

from redis.asyncio import Redis


async def process_message(
    redis: Redis, user_id: int, new_message_id: Optional[int] = None
) -> Optional[int]:
    old_message_id = await redis.get("message_id:{user_id}".format(user_id=user_id))

    if new_message_id:
        await redis.set("message_id:{user_id}".format(user_id=user_id), new_message_id)

    return old_message_id
