# Session 18 in Django: an app to review

This is a small film review service written for the session 18 cross review. It works, and it has problems. Review it with `REVIEW_CHECKLIST.md`, as if it were another group's repository: open one issue per problem using `.github/ISSUE_TEMPLATE/review.md`, then fix them on separate branches with pull requests that say `Fixes #N`. The README itself is part of the review.

## Film reviews

Customers rate Pagila films from 1 to 5 stars and can leave a comment. Each customer has a profile page with their latest reviews.

Stack: Django 6.1, PostgreSQL 18, MongoDB 8, Redis 8.

| File | What it does |
|------|--------------|
| `demo/models.py` | Pagila `film` and `customer`, and the new `film_review` table. |
| `demo/views.py` | Film search, customer lookup by email, reviews, profiles, activity search. |
| `demo/admin_views.py` | Lets an administrator edit a customer's profile. |
| `demo/profiles.py` | Profiles cached in Redis. |
| `.github/` | Issue and pull request templates for the review. |

## Run it

From the root of the repository:

```bash
docker compose up -d
./scripts/create-db.sh s18_django --pagila
```

Then, in this folder:

```bash
cp .env.example .env
uv sync
uv run python manage.py migrate
uv run python manage.py runserver 8001
```

`uv sync` creates `.venv/` with the Python version and the exact package versions in `uv.lock`. The dependencies are declared in `pyproject.toml`.

```bash
curl 'localhost:8001/films/search?title=alien'
curl 'localhost:8001/customers/by-email?email=mary.smith@sakilacustomer.org'
curl -X POST localhost:8001/films/1/reviews -H 'content-type: application/json' -d '{"customer_id": 1, "stars": 4, "comment": "Good"}'
curl localhost:8001/films/1/reviews
curl localhost:8001/customers/1/profile
curl -X PUT localhost:8001/admin/customers/1/profile -H 'content-type: application/json' -d '{"first_name": "Mary"}'
curl -X POST localhost:8001/activity/search -H 'content-type: application/json' -d '{"customer_id": 1}'
```

## Things to try

- Before reading any code, list what the tutorial says a README must contain and tick off what this one has.
- For each issue you open, write the request or command that shows the problem (a `curl`, a `psql` statement, a `redis-cli` command), so the author can reproduce it in a minute.
- Swap issues with a classmate and fix one of theirs on a branch, with a pull request that uses `.github/pull_request_template.md`.
