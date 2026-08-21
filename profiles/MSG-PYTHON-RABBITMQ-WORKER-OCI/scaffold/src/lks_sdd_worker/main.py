import asyncio
import json
import os

import aio_pika

from .worker import DeliveryAction, WorkMessage, delivery_action


async def run() -> None:
    connection = await aio_pika.connect_robust(
        os.getenv("AMQP_URL", "amqp://guest:guest@rabbitmq/")
    )
    async with connection:
        channel = await connection.channel()
        await channel.set_qos(prefetch_count=16)
        queue = await channel.declare_queue("work.v1", durable=True)
        async with queue.iterator() as messages:
            async for incoming in messages:
                message = WorkMessage.model_validate(json.loads(incoming.body))
                action = delivery_action(message)
                if action is DeliveryAction.ACK:
                    await incoming.ack()
                elif action is DeliveryAction.RETRY:
                    await incoming.nack(requeue=True)
                else:
                    await incoming.reject(requeue=False)


if __name__ == "__main__":
    asyncio.run(run())
