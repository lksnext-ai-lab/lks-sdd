from .worker import DeliveryAction, WorkMessage, delivery_action, idempotency_key

message = WorkMessage(message_id="recovery-probe", attempt=3, payload={"result": "failed"})
assert delivery_action(message) is DeliveryAction.DEAD_LETTER
assert idempotency_key(message) == "work-message:recovery-probe"
print("recovery-contract=passed")
