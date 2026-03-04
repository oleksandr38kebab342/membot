import threading
import time
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import repositories


def _seconds_until_next(target_time, tz_name):
    now = datetime.now(ZoneInfo(tz_name))
    cleaned = target_time.strip().split()[0].replace(".", ":")
    hour, minute = [int(part) for part in cleaned.split(":", 1)]
    target = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
    if target <= now:
        target += timedelta(days=1)
    return (target - now).total_seconds()


def _choose_joke_of_day():
    joke = repositories.get_random_joke("common")
    if joke:
        return joke.data
    joke = repositories.get_random_joke("black")
    return joke.data if joke else None


class JokeOfDayScheduler(threading.Thread):
    def __init__(self, bot, target_time, tz_name):
        super().__init__(daemon=True)
        self.bot = bot
        self.target_time = target_time
        self.tz_name = tz_name

    def run(self):
        while True:
            try:
                sleep_seconds = _seconds_until_next(self.target_time, self.tz_name)
            except Exception:
                time.sleep(3600)
                continue
            time.sleep(sleep_seconds)
            joke_text = _choose_joke_of_day()
            if not joke_text:
                continue
            user_ids = repositories.get_all_user_ids()
            for user_id in user_ids:
                try:
                    self.bot.send_message(user_id, f"Жарт дня:\n\n{joke_text}")
                except Exception:
                    continue


def start_joke_of_day_scheduler(bot, target_time, tz_name):
    scheduler_thread = JokeOfDayScheduler(bot, target_time, tz_name)
    scheduler_thread.start()
    return scheduler_thread
