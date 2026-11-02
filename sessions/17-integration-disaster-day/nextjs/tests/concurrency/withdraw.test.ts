// Rule: an account balance never goes below 0. 50 withdrawals of 10 from 100 at the same time:
// exactly 10 succeed. Needs the API running (npm run dev or npm start).
import assert from "node:assert/strict";
import { test } from "node:test";
import { byStatus, call } from "./helpers";

test("50 concurrent withdrawals of 10 from 100: exactly 10 succeed", async () => {
  await call("POST", "/api/accounts/1/reset", { balance: 100 });

  const results = await Promise.all(
    Array.from({ length: 50 }, () => call("POST", "/api/accounts/1/withdraw", { amount: 10 })),
  );

  assert.deepEqual(byStatus(results), { 200: 10, 409: 40 });
  const account = await call("GET", "/api/accounts/1");
  assert.equal(Number(account.body.balance), 0);
});
