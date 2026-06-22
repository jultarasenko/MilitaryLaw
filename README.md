# MilitaryLaw Bot

A Telegram bot that walks a user through a legal decision tree to estimate
how long a deferral (відстрочка) they're entitled to after their military
service contract ends, based on Ukrainian law. The legal logic was provided
by advokat Daria Tarasenko; this repository implements it as an interactive,
stateful bot.

## Tech stack

- **Python 3.13**, fully type-hinted
- [`python-telegram-bot`](https://github.com/python-telegram-bot/python-telegram-bot) (async, `ConversationHandler`-based dialogue)
- **pytest** for unit tests of the legal/date logic
- **ruff** for linting and formatting
- **Docker** / **docker-compose** for deployment, with a named volume for persistent conversation state

## Architecture

The code is split into two layers with a one-way dependency: `bot` depends
on `domain`, never the other way around. This keeps the legal rules
testable without mocking Telegram, and keeps the conversation flow free of
business-rule details.

```
src/militarylaw_bot/
├── domain/              # Framework-free business logic
│   ├── deferral.py      #   decision-tree rules: which terms apply and how they're computed
│   ├── dates.py         #   parsing & validating user-supplied date ranges
│   └── formatting.py    #   renders a result as user-facing text
├── bot/                 # Telegram adapter layer
│   ├── app.py           #   builds and runs the Application
│   ├── conversation.py  #   wires states to handlers (ConversationHandler)
│   ├── handlers.py      #   one async function per conversation step
│   ├── states.py        #   conversation state enum
│   ├── session.py       #   typed wrapper around per-chat user_data
│   ├── keyboards.py     #   inline keyboard builders
│   ├── callback_data.py #   button callback-data constants
│   └── texts.py         #   all user-facing Ukrainian copy
└── config.py            # environment-driven settings
```

**Why this split:** the decision tree (which deferral components apply, and
how their durations are computed from dates) is the part of this project
that is legally load-bearing and most likely to need a careful review or
update. Isolating it in `domain/`, with no `telegram` import anywhere in
that package, means:

- it can be unit tested directly (see `tests/`) without spinning up a bot
  or mocking Telegram's API,
- a future change to the rules (e.g. a new government resolution) touches
  one module, not the conversation flow,
- the conversation flow (`bot/`) stays a thin adapter: each handler reads
  the user's choice, asks `domain` what happens next, and renders the
  result.

## Decision tree

The bot encodes this flow (see `domain/deferral.py` for the implementation):

1. Does the user have a contract in effect as of 24.02.2022? If not, contract-end
   discharge isn't available under this flow.
2. Which contract governs their service — Постанова КМУ №768, №1538, or a
   general-grounds contract signed after 24.02.2022?
3. Depending on the answer, the bot asks follow-up questions (contract term,
   age at signing, discharge timing) and, where the legal formula requires
   it, asks for the user's contract-signing date, combat-participation
   period(s), and/or pre-24.02.2022 service period(s).
4. The final deferral term is a sum of components — some fixed, some
   computed as months-per-30-days of combat participation, months-per-year
   of service from 24.02.2022 to the contract's signing date, or
   months-per-year of continuous service before 24.02.2022.

## Running locally

```bash
cp .env.example .env        # fill in TELEGRAM_BOT_TOKEN
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
militarylaw-bot
```

## Running with Docker

```bash
docker compose up -d --build
```

Conversation state is persisted to a Docker volume (`bot-data`), so
in-progress conversations survive a container restart.

## Tests

```bash
pytest          # unit tests for domain/dates.py and domain/deferral.py
ruff check .    # lint
ruff format .   # format
```
