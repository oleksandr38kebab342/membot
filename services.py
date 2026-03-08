from datetime import datetime, timezone

import repositories


def can_submit_joke(user_id, cooldown_seconds):
    user = repositories.get_user(user_id)
    if not user or not user.last_joke_at:
        return True, 0
    last_joke_at = user.last_joke_at.replace(tzinfo=timezone.utc) if user.last_joke_at.tzinfo is None else user.last_joke_at
    elapsed = (datetime.now(timezone.utc) - last_joke_at).total_seconds()
    if elapsed >= cooldown_seconds:
        return True, 0
    return False, int(cooldown_seconds - elapsed)


def record_joke_submission(user_id):
    repositories.set_user_last_joke_at(user_id, datetime.now(timezone.utc))
