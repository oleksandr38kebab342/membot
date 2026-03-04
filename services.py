from datetime import datetime, timezone

import repositories


def can_submit_joke(user_id, cooldown_seconds):
    user = repositories.get_user(user_id)
    if not user or not user.last_joke_at:
        return True, 0
    elapsed = (datetime.now(timezone.utc) - user.last_joke_at).total_seconds()
    if elapsed >= cooldown_seconds:
        return True, 0
    return False, int(cooldown_seconds - elapsed)


def record_joke_submission(user_id):
    repositories.set_user_last_joke_at(user_id, datetime.now(timezone.utc))
