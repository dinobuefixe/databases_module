import type { Document } from "mongodb";
import { mongoDb } from "@/lib/mongo";

// A store as one document: manager, address and staff are embedded because they are
// always read with the store, belong to it, and stay small.
export type StoreDoc = {
  _id: number;
  manager: { staff_id: number; name: string };
  address: { line: string; city: string; country: string };
  staff: { staff_id: number; name: string }[];
  visits?: number;
};

export const stores = () => mongoDb().collection<StoreDoc>("stores");

// The $jsonSchema from the tutorial.
export const storeValidator: Document = {
  $jsonSchema: {
    bsonType: "object",
    required: ["manager", "address"],
    properties: {
      manager: { bsonType: "object", required: ["staff_id", "name"] },
      address: {
        bsonType: "object",
        required: ["city", "country"],
        properties: { city: { bsonType: "string" }, country: { bsonType: "string" } },
      },
      staff: { bsonType: "array" },
    },
  },
};

// Summarises explain("executionStats") into the numbers the tutorial asks you to compare.
export async function explainByCountry(country: string) {
  const plan = await stores().find({ "address.country": country }).explain("executionStats");
  const stats = plan.executionStats;
  const stages: string[] = [];
  for (let s = plan.queryPlanner.winningPlan; s; s = s.inputStage) stages.push(s.stage);
  return {
    stages, // COLLSCAN without the index, FETCH <- IXSCAN with it
    nReturned: stats.nReturned,
    totalDocsExamined: stats.totalDocsExamined,
    totalKeysExamined: stats.totalKeysExamined,
    executionTimeMillis: stats.executionTimeMillis,
  };
}
