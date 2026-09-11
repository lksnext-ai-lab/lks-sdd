from .processor import ReplayWindow, replay_offsets

window = ReplayWindow(partition=0, from_offset=10, to_offset=12)
assert list(replay_offsets(window)) == [10, 11, 12]
print("replay-recovery-contract=passed")
