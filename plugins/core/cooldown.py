import time


DRAW_COOLDOWN_SECONDS = 10
_draw_cooldowns = {}


def check_draw_cooldown(sender, seconds=DRAW_COOLDOWN_SECONDS):
    now = time.monotonic()
    available_at = _draw_cooldowns.get(sender, 0)
    if available_at > now:
        return False, max(1, int(available_at - now + 0.999))
    _draw_cooldowns[sender] = now + seconds
    return True, 0
