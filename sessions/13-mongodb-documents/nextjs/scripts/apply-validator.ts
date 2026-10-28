// Adds the $jsonSchema validator to the stores collection, then tries the tutorial's invalid insert.
import "dotenv/config";
import { MongoServerError } from "mongodb";
import { mongo, mongoDb } from "@/lib/mongo";
import { storeValidator, stores } from "@/lib/stores";

async function main() {
  const db = mongoDb();
  if (!(await db.listCollections({ name: "stores" }).hasNext())) await db.createCollection("stores");

  // collMod changes the options of an existing collection without touching its documents.
  await db.command({
    collMod: "stores",
    validator: storeValidator,
    validationLevel: "strict", // also check updates to documents that are already invalid
    validationAction: "error", // reject the write ("warn" would only log it)
  });
  console.log("Validator applied to stores");

  // The tutorial uses _id 99, but Pagila has a store 99 here, so use an id that is free.
  try {
    await stores().insertOne({ _id: 9999, address: { city: 42 } } as never);
    console.log("Inserted: the validator is not active");
  } catch (err) {
    if (!(err instanceof MongoServerError) || err.code !== 121) throw err;
    console.log(`Rejected: ${err.message}`);
    console.log(JSON.stringify(err.errInfo?.details, null, 2));
  }
}

main().finally(() => mongo.close());
