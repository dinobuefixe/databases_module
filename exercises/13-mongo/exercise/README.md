# Pagila to MongoDB

## Setup and run order

Requires PostgreSQL with Pagila loaded, MongoDB 6 or later, `mongosh`, and Python 3.10+.

```bash
uv sync                                  # or: pip install pymongo "psycopg[binary]"

export PAGILA_DSN="postgresql://postgres:postgres@localhost:5432/pagila"
export MONGO_URI="mongodb://localhost:27017"
export MONGO_DB="pagila"

uv run python load.py                    # 1. load films, customers, rentals
mongosh "$MONGO_URI/pagila" operations.js   # 2. the eight operations (on fresh data)
mongosh "$MONGO_URI/pagila" validation.js   # 3. $jsonSchema on films + rejected inserts
uv run python load.py                    # 3b. loader still passes the validator
mongosh "$MONGO_URI/pagila" index.js     # 4. explain before/after the index
```

Run `load.py` again before `operations.js` if you want to repeat the operations, because operations 6 to 8 change data. `operations.js` deletes and recreates film 1001 itself, so it can be re-run without a reload.

`load.py` is idempotent. Each document is written with `ReplaceOne(upsert=True)` on its Pagila id, and documents whose ids no longer exist in Pagila are removed with a final `delete_many`. Remove that line if you want stale documents kept.

Expected counts after loading: `films` 1,000, `customers` 999, `rentals` 51,805.

## Why the data is shaped this way (task 1)

**Actors and categories are embedded in `films`.** Both are small and bounded: a film has a handful of categories and a cast of a few dozen actors at most. They are almost always read together with the film (the detail page, the "what is this film" answer), so embedding gives one read instead of a `$lookup` across `film_actor`, `actor`, `film_category` and `category`. They change rarely, so keeping them in sync is cheap. The cost is duplication: an actor's name appears in every film they appear in. That is acceptable because the name rarely changes.

**Only the 10 most recent rentals are embedded in `customers`.** Showing recent activity on a customer profile is the common read, and 10 entries answer it without touching `rentals`. The array is capped, so the document stays small and its size does not grow with every rental. A customer has a rental every few days, so an uncapped array would keep growing, eventually approach MongoDB's 16 MB document limit, and force rewriting a large document on each update. `rental_count` is stored alongside so the total is available without counting. The "ten most recent" rule must be maintained on each new rental, which is what operation 7 does with `$push` plus `$slice`.

**The full history is in `rentals`.** The history grows without bound, so it cannot be embedded in a parent document. Queries over it (rentals in a date range, rentals of one film, revenue per store, rentals per category) need to scan it independently of any customer or film, which a separate collection with indexes supports. Keeping it separate also means `films` and `customers` stay small. Each rental copies the title and categories at the time of rental. This is a deliberate snapshot: a rental is a historical fact, and it should keep the title it had. The trade-off is that a film renamed later will still show its old title in `rentals`. `customers.recent_rentals` has the same snapshot behaviour.

## Operations (task 2)

Record the actual values from your `mongosh` run. The expected values come from the spec. Do not copy the expected column into the actual column without checking.

| # | Operation | Expected | Actual |
|---|---|---|---|
| 1 | PG-13 films longer than 120 min | 118 | _run and record_ |
| 2 | films with actor 1 | 19 | _run and record_ |
| 3 | Horror films, rental_rate 0.99 | 43 | _run and record_ |
| 4 | customers with an unreturned embedded rental (`$elemMatch`) | 56 | _run and record_ |
| 5 | customer 1 projection: names and 10 titles | 10 titles | _run and record_ |
| 6 | NC-17 under 60 min, rate `$inc` +0.50 (modified) | 21 | _run and record_ |
| 7 | `$push` new rental to customer 1, `$slice` 10 | 10 items, new rental first | _run and record_ |
| 8 | upsert film 1001 twice (`$setOnInsert`) | run 1 upserts 1; run 2 matches 1, modifies 0 | _run and record_ |

Operation 4 reads "at least one rental not returned among their `recent_rentals`" as: at least one embedded rental with `return_date: null`. Rentals older than the embedded 10 are not checked, because they are not in the customer document.

## Validation (task 3)

`validation.js` applies a `$jsonSchema` validator to `films` with `validationLevel: "strict"` and `validationAction: "error"`. The schema requires only `title`. Making other fields required would make operation 8 (which inserts a film with only a title) fail after validation is applied. The rest of the rules apply to any field that is present: `rating` must be one of the five values, `length` must be an integer from 1 to 999, `rental_rate` must be a decimal, `categories` must be an array of strings, and `actors` must be an array of objects with an integer `actor_id` and a string `name`.

`load.py` must still run after the validator is in place. It writes `rental_rate` as Decimal128, `length` as int32, and `actors` with integer `actor_id`, so all data should pass. If it does not, check for a Pagila film with a `NULL` length or rating, because those would fail the schema.

### Rejected inserts (fill in from your run)

| _id | Problem | Expected error | Actual |
|---|---|---|---|
| 2001 | `rating: "XXX"` | `MongoServerError`, code 121 (`DocumentValidationFailure`), "Document failed validation" | _run and record_ |
| 2002 | `length: "long"` | same as above | _run and record_ |

## Index comparison (task 4)

`index.js` runs `find({"actors.actor_id": 1}).explain("executionStats")` once with no index, then creates an index named `actors.actor_id_1` and runs it again.

| | stage (top) | plan | totalDocsExamined | totalKeysExamined | nReturned |
|---|---|---|---|---|---|
| before index | COLLSCAN | COLLSCAN | _run and record_ | 0 | _run and record_ |
| after index | FETCH | FETCH <- IXSCAN | _run and record_ | _run and record_ | _run and record_ |

The expected result is that the plan changes from `COLLSCAN` to `IXSCAN`, with `totalDocsExamined` equal to `nReturned` (19) after the index is created. Before the index, `totalDocsExamined` equals the number of films (1,000). The top-level stage after the index is `FETCH`, because the index plan fetches full documents from the `IXSCAN` child. The `IXSCAN` stage is the one that shows the index is used.

## Done-when checklist

- [ ] `films` 1,000, `customers` 999, `rentals` 51,805 after `load.py`
- [ ] Running `load.py` twice gives the same counts
- [ ] All 8 operations match expected values on fresh data
- [ ] Both invalid inserts are rejected, with error text recorded above
- [ ] `load.py` passes after the validator is applied
- [ ] Explain plan changes from `COLLSCAN` to `IXSCAN`, with 19 documents examined
