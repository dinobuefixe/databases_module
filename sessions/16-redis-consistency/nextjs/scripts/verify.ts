// Compares every customer:{id}:films set with PostgreSQL, member by member. Exit code 0 when they match,
// 1 otherwise, so it can run in CI, on a schedule or as the last step of a restore.
import "dotenv/config";
import { disconnectAll, verify, type Mismatch } from "@/lib/films-sets";
import { getRedis } from "@/lib/redis";

const ids = (members: string[]) =>
  members.length <= 5 ? members.join(", ") : `${members.slice(0, 5).join(", ")} ... (${members.length} in total)`;

function describe(m: Mismatch) {
  if (m.orphan) return `${m.key}: no such customer in PostgreSQL (${m.extra.length} members)`;
  const parts = [];
  if (m.missing.length) parts.push(`missing ${ids(m.missing)}`);
  if (m.extra.length) parts.push(`extra ${ids(m.extra)}`);
  return `${m.key}: ${parts.join("; ")}`;
}

async function main() {
  const redis = await getRedis();
  const { checked, mismatches } = await verify(redis);
  for (const m of mismatches.slice(0, 20)) console.error(describe(m));
  if (mismatches.length > 20) console.error(`... and ${mismatches.length - 20} more`);
  console.log(`${checked} customers checked, ${mismatches.length} mismatches`);
  await redis.quit();
  await disconnectAll();
  process.exitCode = mismatches.length ? 1 : 0;
}

main();
