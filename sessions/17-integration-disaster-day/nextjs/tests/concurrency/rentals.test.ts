// Rule: customer:{id}:films in Redis matches PostgreSQL after every write, even concurrent ones.
import assert from "node:assert/strict";
import { test } from "node:test";
import { byStatus, call } from "./helpers";

test("20 concurrent rentals keep the Redis sets equal to PostgreSQL", async () => {
  // Start from a consistent state, as the runbook does.
  assert.equal((await call("GET", "/api/verify")).status, 200, "Redis is not consistent before the test; rebuild it");

  const inventoryIds = Array.from({ length: 20 }, () => 1 + Math.floor(Math.random() * 4000));
  const results = await Promise.all(
    inventoryIds.map((inventory_id) => call("POST", "/api/rentals", { customer_id: 1, inventory_id })),
  );
  assert.deepEqual(byStatus(results), { 201: 20 });

  const films = await call("GET", "/api/customers/1/films");
  for (const r of results) assert.ok(films.body.films.includes(r.body.film_id), `film ${r.body.film_id} missing`);

  const verify = await call("GET", "/api/verify");
  assert.equal(verify.status, 200, JSON.stringify(verify.body));
});
