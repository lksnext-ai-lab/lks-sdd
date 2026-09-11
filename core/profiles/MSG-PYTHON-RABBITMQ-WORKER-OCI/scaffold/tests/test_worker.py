import pytest
from pydantic import ValidationError

from lks_sdd_worker.worker import DeliveryAction, WorkMessage, delivery_action, idempotency_key


def test_contract_rejects_invalid_message() -> None:
    with pytest.raises(ValidationError):
        WorkMessage(message_id="", attempt=-1, payload={})


def test_contract_has_stable_idempotency_key() -> None:
    message = WorkMessage(message_id="m-1", attempt=0, payload={"result": "accepted"})
    assert idempotency_key(message) == "work-message:m-1"


def test_retry_is_bounded() -> None:
    message = WorkMessage(message_id="m-2", attempt=2, payload={"result": "failed"})
    assert delivery_action(message) is DeliveryAction.RETRY


def test_dead_letter_after_maximum_attempts() -> None:
    message = WorkMessage(message_id="m-3", attempt=3, payload={"result": "failed"})
    assert delivery_action(message) is DeliveryAction.DEAD_LETTER
