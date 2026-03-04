# membot

## Docker Compose

```bash
set BOT_TOKEN=your-token
set JOKE_DAY_TIME=13:00
set TIMEZONE=Europe/Kyiv
docker-compose up --build
```


## Local Run

```bash
set BOT_TOKEN=your-token
python blackjack.py
```

## Migrations (Alembic)

```bash
alembic upgrade head
```