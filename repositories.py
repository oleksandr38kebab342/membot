from datetime import datetime, timezone

from sqlalchemy import func, select

from db import get_session
from models import AttemptJoke, BlackJoke, CommonJoke, Rating, User


def upsert_user(user_id, username):
    now = datetime.now(timezone.utc)
    with get_session() as session:
        user = session.get(User, user_id)
        if user:
            user.username = username
            user.last_seen_at = now
        else:
            user = User(id=user_id, username=username, last_seen_at=now)
            session.add(user)


def get_user(user_id):
    with get_session() as session:
        user = session.get(User, user_id)
        return user


def set_user_last_joke_at(user_id, when):
    with get_session() as session:
        user = session.get(User, user_id)
        if user:
            user.last_joke_at = when


def get_all_user_ids():
    with get_session() as session:
        rows = session.execute(select(User.id)).all()
        return [row[0] for row in rows]


def add_attempt_joke(text, user_id):
    with get_session() as session:
        session.add(AttemptJoke(data=text, user_id=user_id))


def count_attempts():
    with get_session() as session:
        return session.execute(select(func.count(AttemptJoke.id))).scalar() or 0


def get_attempt_by_id(joke_id):
    with get_session() as session:
        return session.get(AttemptJoke, int(joke_id))


def delete_attempt_by_id(joke_id):
    with get_session() as session:
        joke = session.get(AttemptJoke, int(joke_id))
        if joke:
            session.delete(joke)


def get_random_attempt():
    with get_session() as session:
        return session.execute(select(AttemptJoke).order_by(func.random()).limit(1)).scalar_one_or_none()


def add_common_joke(text, user_id):
    with get_session() as session:
        session.add(CommonJoke(data=text, user_id=user_id))


def add_black_joke(text, user_id):
    with get_session() as session:
        session.add(BlackJoke(data=text, user_id=user_id))


def get_random_joke(table_name):
    model = CommonJoke if table_name == "common" else BlackJoke
    with get_session() as session:
        return session.execute(select(model).order_by(func.random()).limit(1)).scalar_one_or_none()


def add_or_update_user_rating(user_id, username, points, accepted_inc=0):
    with get_session() as session:
        rating = session.get(Rating, user_id)
        if rating:
            rating.username = username
            rating.rate += points
            rating.accepted_count += accepted_inc
        else:
            session.add(Rating(user_id=user_id, username=username, rate=points, accepted_count=accepted_inc))


def get_top_users(limit=7):
    with get_session() as session:
        rows = session.execute(
            select(Rating.username, Rating.rate).order_by(Rating.rate.desc()).limit(limit)
        ).all()
        return rows


def get_user_profile(user_id):
    with get_session() as session:
        rating = session.get(Rating, user_id)
        if not rating:
            return None
        higher_count = session.execute(
            select(func.count(Rating.user_id)).where(Rating.rate > rating.rate)
        ).scalar() or 0
        return {
            "username": rating.username,
            "rate": rating.rate,
            "accepted_count": rating.accepted_count,
            "rank": higher_count + 1,
        }
