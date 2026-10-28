// Rule: a monthly report is frozen. 10 requests to create the same report at once: one 201, nine 409.
import assert from "node:assert/strict";
import { after, test } from "node:test";
import { MongoClient } from "mongodb";
import { byStatus, call } from "./helpers";

const mongo = new MongoClient(process.env.MONGO_URL!);
after(() => mongo.close());

test("10 concurrent requests for the same monthly report: one creates it", async () => {
  // Setup: remove the test month directly in MongoDB. The API itself never deletes a report.
  await mongo.db(process.env.MONGO_DB).collection("monthly_reports").deleteOne({ _id: "2022-07" as never });

  const results = await Promise.all(Array.from({ length: 10 }, () => call("POST", "/api/reports/monthly/2022-07")));

  assert.deepEqual(byStatus(results), { 201: 1, 409: 9 });
});
