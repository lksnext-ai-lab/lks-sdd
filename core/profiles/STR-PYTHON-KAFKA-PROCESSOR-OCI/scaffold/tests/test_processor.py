import pytest
from pydantic import ValidationError

from lks_sdd_stream.processor import (
    ReplayWindow,
    StreamEvent,
    next_committable_offset,
    partition_key,
    replay_offsets,
)


def test_contract_requires_stable_identifiers() -> None:
    with pytest.raises(ValidationError):
        StreamEvent(event_id="", aggregate_id="", schema_version=0, payload={})


def test_contract_partition_key_preserves_aggregate_order() -> None:
    event = StreamEvent(event_id="e-1", aggregate_id="a-1", schema_version=1, payload={})
    assert partition_key(event) == b"a-1"


def test_offset_commit_uses_next_offset() -> None:
    assert next_committable_offset(41) == 42
    with pytest.raises(ValueError):
        next_committable_offset(-1)


def test_replay_is_bounded_and_inclusive() -> None:
    window = ReplayWindow(partition=0, from_offset=2, to_offset=4)
    assert list(replay_offsets(window)) == [2, 3, 4]
    with pytest.raises(ValueError):
        replay_offsets(ReplayWindow(partition=0, from_offset=5, to_offset=4))
