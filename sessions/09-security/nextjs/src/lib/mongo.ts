import { MongoClient } from "mongodb";

// Prisma 7 does not support MongoDB, so we use the official driver.
const globalForMongo = globalThis as unknown as { mongo?: MongoClient };

export const mongo = globalForMongo.mongo ?? new MongoClient(process.env.MONGO_URL!);

if (process.env.NODE_ENV !== "production") globalForMongo.mongo = mongo;

export const mongoDb = () => mongo.db(process.env.MONGO_DB);
