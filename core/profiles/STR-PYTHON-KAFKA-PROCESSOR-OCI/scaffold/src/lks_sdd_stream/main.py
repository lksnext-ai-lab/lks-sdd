import asyncio
import json
import os

from aiokafka import AIOKafkaConsumer

from .processor import StreamEvent, next_committable_offset, partition_key


async def run() -> None:
    consumer = AIOKafkaConsumer(
        "events.v1",
        bootstrap_servers=os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092"),
        group_id="lks-sdd-reference",
        enable_auto_commit=False,
    )
    await consumer.start()
    try:
        async for record in consumer:
            event = StreamEvent.model_validate(json.loads(record.value))
            assert record.key == partition_key(event)
            assert next_committable_offset(record.offset) > record.offset
            await consumer.commit()
    finally:
        await consumer.stop()


if __name__ == "__main__":
    asyncio.run(run())
