from enum import StrEnum

from pydantic import BaseModel, Field


class DeliveryAction(StrEnum):
    ACK = "ack"
    RETRY = "retry"
    DEAD_LETTER = "dead-letter"


class WorkMessage(BaseModel):
    message_id: str = Field(min_length=1, max_length=128)
    attempt: int = Field(ge=0)
    payload: dict[str, str]


def delivery_action(message: WorkMessage, *, maximum_attempts: int = 3) -> DeliveryAction:
    if message.payload.get("result") == "accepted":
        return DeliveryAction.ACK
    if message.attempt < maximum_attempts:
        return DeliveryAction.RETRY
    return DeliveryAction.DEAD_LETTER


def idempotency_key(message: WorkMessage) -> str:
    return f"work-message:{message.message_id}"
