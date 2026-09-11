from pydantic import BaseModel, Field


class StreamEvent(BaseModel):
    event_id: str = Field(min_length=1, max_length=128)
    aggregate_id: str = Field(min_length=1, max_length=128)
    schema_version: int = Field(ge=1)
    payload: dict[str, str]


class ReplayWindow(BaseModel):
    partition: int = Field(ge=0)
    from_offset: int = Field(ge=0)
    to_offset: int = Field(ge=0)

    def is_bounded(self) -> bool:
        return self.to_offset >= self.from_offset


def partition_key(event: StreamEvent) -> bytes:
    return event.aggregate_id.encode("utf-8")


def next_committable_offset(processed_offset: int) -> int:
    if processed_offset < 0:
        raise ValueError("offset cannot be negative")
    return processed_offset + 1


def replay_offsets(window: ReplayWindow) -> range:
    if not window.is_bounded():
        raise ValueError("replay window is inverted")
    return range(window.from_offset, window.to_offset + 1)
