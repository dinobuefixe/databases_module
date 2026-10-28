// explain("executionStats") for a find by country, before and after an index on address.country.
import "dotenv/config";
import { mongo } from "@/lib/mongo";
import { explainByCountry, stores } from "@/lib/stores";

const country = process.argv[2] ?? "India";
const indexName = "address.country_1";

async function main() {
  const indexes = await stores().indexes();
  if (indexes.some((i) => i.name === indexName)) await stores().dropIndex(indexName);

  const before = await explainByCountry(country);
  await stores().createIndex({ "address.country": 1 });
  const after = await explainByCountry(country);

  console.log(`find({"address.country": "${country}"})`);
  console.table({ before, after });
}

main().finally(() => mongo.close());
