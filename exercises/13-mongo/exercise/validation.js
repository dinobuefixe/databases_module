// validation.js: $jsonSchema validator on films (strict, error).
//   mongosh "mongodb://localhost:27017/pagila" validation.js

const filmSchema = {
  $jsonSchema: {
    bsonType: "object",
    required: ["title"],
    properties: {
      title: { bsonType: "string" },
      rating: { enum: ["G", "PG", "PG-13", "R", "NC-17"] },
      length: { bsonType: ["int", "long"], minimum: 1, maximum: 999 },
      rental_rate: { bsonType: "decimal" },
      categories: { bsonType: "array", items: { bsonType: "string" } },
      actors: {
        bsonType: "array",
        items: {
          bsonType: "object",
          required: ["actor_id", "name"],
          properties: {
            actor_id: { bsonType: ["int", "long"] },
            name: { bsonType: "string" },
          },
        },
      },
    },
  },
};

const res = db.runCommand({
  collMod: "films",
  validator: filmSchema,
  validationLevel: "strict",
  validationAction: "error",
});
print(`collMod ok: ${res.ok === 1}`);

// Invalid documents. Each has one problem: a bad rating, or a non-integer length.
const invalid = [
  {
    _id: 2001, title: "BAD RATING", rating: "XXX", length: NumberInt(90),
    rental_rate: NumberDecimal("0.99"), categories: [], actors: [],
  },
  {
    _id: 2002, title: "BAD LENGTH", rating: "PG", length: "long",
    rental_rate: NumberDecimal("0.99"), categories: [], actors: [],
  },
];

for (const doc of invalid) {
  try {
    db.films.insertOne(doc);
    print(`${doc._id}: UNEXPECTEDLY ACCEPTED`);
  } catch (e) {
    print(`${doc._id}: rejected, code ${e.code} ${e.codeName ?? ""}`);
    print(`   ${e.message}`);
  }
}

print(`invalid documents stored: ${db.films.countDocuments({ _id: { $in: [2001, 2002] } })}`);
