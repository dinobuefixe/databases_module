import "dotenv/config";
import { MongoClient } from "mongodb";
import bcrypt from "bcryptjs";

// 1. As root: create the application user "app" with readWrite on this
//    project's database only (the tutorial's db.createUser).
// 2. As app: load two small collections for the login demo.
// 3. As app: show that another database is out of reach.
const dbName = process.env.MONGO_DB!;

async function main() {
  const admin = new MongoClient(process.env.MONGO_ADMIN_URL!);
  await admin.connect();
  try {
    const db = admin.db(dbName);
    const { users } = await db.command({ usersInfo: "app" });
    const roles = [{ role: "readWrite", db: dbName }];
    if (users.length === 0) {
      await db.command({ createUser: "app", pwd: process.env.MONGO_APP_PASSWORD, roles });
      console.log(`created MongoDB user app with readWrite on ${dbName}`);
    } else {
      await db.command({ updateUser: "app", pwd: process.env.MONGO_APP_PASSWORD, roles });
      console.log(`MongoDB user app already existed in ${dbName}; password and roles updated`);
    }
  } finally {
    await admin.close();
  }

  const app = new MongoClient(process.env.MONGO_URL!);
  await app.connect();
  try {
    const db = app.db(dbName);

    // Passwords are stored as bcrypt hashes. The cost factor (10) makes each
    // guess slow on purpose.
    await db.collection("users").deleteMany({});
    await db.collection("users").insertMany([
      { username: "admin", passwordHash: await bcrypt.hash("correct horse battery staple", 10), role: "admin" },
      { username: "maria", passwordHash: await bcrypt.hash("maria-local-demo", 10), role: "user" },
    ]);
    await db.collection("users").createIndex({ username: 1 }, { unique: true });

    // UNSAFE demo data: the old way, plain-text passwords compared inside the
    // query. Used only by POST /api/login-unsafe.
    await db.collection("legacy_users").deleteMany({});
    await db.collection("legacy_users").insertMany([
      { username: "admin", password: "correct horse battery staple", role: "admin" },
      { username: "maria", password: "maria-local-demo", role: "user" },
    ]);
    console.log(`loaded users (hashed) and legacy_users (plain text, unsafe demo) as app`);

    // readWrite on one database means nothing on the others.
    try {
      await app.db("admin").command({ listCollections: 1 });
      console.log("FAIL  app could list collections in the admin database");
      process.exitCode = 1;
    } catch (err) {
      console.log(`PASS  app cannot read the admin database: ${(err as Error).message}`);
    }
  } finally {
    await app.close();
  }
}

main();
