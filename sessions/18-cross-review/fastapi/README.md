# Session 18 in FastAPI: a project to review

A small film review API on top of Pagila, with customer profiles cached in Redis. It is the project you review in this session: work through `REVIEW_CHECKLIST.md`, write one issue per problem with the template in `.github/ISSUE_TEMPLATE/review.md`, and fix them one branch and one pull request at a time.

| File | What it shows |
|------|---------------|
| `sql/001_film_review.sql` | The `film_review` table and its index. |
| `sql/002_seed_reviews.sql` | About 58,000 generated reviews. |
| `scripts/init_db.py` | Applies the SQL files; the seed only runs on an empty table. |
| `app/config.py` | Settings read from `.env`. |
| `app/db.py` | SQLAlchemy engine and Redis client. |
| `app/profiles.py` | `get_profile()`: customer profile with a review count, cached in Redis for 5 minutes. |
| `app/main.py` | Customer search, profiles, the admin profile update, reviews and average rating per film. |
| `REVIEW_CHECKLIST.md` | What to check, item by item. |
| `.github/ISSUE_TEMPLATE/review.md` | Problem / Where / Why it matters / Suggestion. |
| `.github/pull_request_template.md` | The pull request description, with `Fixes #`. |

## Rules

- A rating is a whole number from 1 to 5.
- A customer reviews a film at most once.

## Stack

FastAPI, SQLAlchemy 2 (Core `text()` queries), PostgreSQL 18 with Pagila, Redis 8.

## Run it

From the root of the repository, start the engines and create this project's database as a copy of Pagila:

```bash
docker compose up -d
./scripts/create-db.sh s18_fastapi --pagila
```

Then, in this folder:

```bash
cp .env.example .env
uv sync
uv run python -m scripts.init_db
uv run uvicorn app.main:app --reload --port 8000
```

`uv sync` creates `.venv/` with the Python version and the exact package versions in `uv.lock`. The dependencies are declared in `pyproject.toml`.

```bash
curl 'localhost:8000/customers/search?name=SMI'
curl localhost:8000/customers/1/profile
curl -X POST localhost:8000/films/1/reviews -H 'content-type: application/json' -d '{"customer_id": 1, "rating": 4, "body": "Good"}'
curl 'localhost:8000/films/1/reviews?limit=5'
curl localhost:8000/films/1/rating
```

## Things to try

- Review the project with `REVIEW_CHECKLIST.md`. Prove each problem before you report it: a `curl` call, a row inserted in `psql`, an `EXPLAIN (ANALYZE, BUFFERS)`, a `TTL` in `redis-cli -n 1`. Put the proof in "Why it matters".
- Write each issue as in the tutorial: the file and line, what goes wrong, and a fix someone can make in five minutes.
- Fix one issue per branch (`git switch -c fix/<issue-number>`), open a pull request whose description says `Fixes #<issue-number>`, and ask someone else to review it before merging.
- Compare this README with the list in the tutorial and add what is missing.
