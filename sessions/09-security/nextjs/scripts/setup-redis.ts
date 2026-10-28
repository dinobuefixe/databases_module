import "dotenv/config";
import { createClient } from "redis";

// Creates the Redis ACL user for this project: every command except the
// dangerous ones (FLUSHALL, FLUSHDB, CONFIG, KEYS, ...), as in the tutorial:
//   ACL SETUSER app on >CHANGE_ME ~* +@all -@dangerous
// The user is named s09_nextjs_app because Redis users are server-wide and
// other projects share this server.
const user = process.env.REDIS_APP_USER!;
const password = process.env.REDIS_APP_PASSWORD!;

async function main() {
  const admin = createClient({ url: process.env.REDIS_ADMIN_URL });
  await admin.connect();
  // "reset" first so running the script again leaves exactly these rules.
  await admin.sendCommand(["ACL", "SETUSER", user, "reset", "on", `>${password}`, "~*", "+@all", "-@dangerous"]);
  console.log(`ACL user ${user} configured`);

  // ACL DRYRUN asks Redis whether the user may run a command, without running it.
  const dryRun = String(await admin.sendCommand(["ACL", "DRYRUN", user, "FLUSHALL"]));
  console.log(`ACL DRYRUN ${user} FLUSHALL -> ${dryRun}`);
  await admin.quit();

  const app = createClient({ url: process.env.REDIS_URL });
  await app.connect();
  console.log(`connected as ${String(await app.sendCommand(["ACL", "WHOAMI"]))}`);
  console.log(`SET s09:check 1 -> ${await app.set("s09:check", "1")}`);

  // Only send FLUSHALL when the dry run has confirmed it will be refused.
  if (dryRun === "OK") {
    console.log("FAIL  the ACL allows FLUSHALL; not sending it");
    process.exitCode = 1;
  } else {
    try {
      await app.sendCommand(["FLUSHALL"]);
      console.log("FAIL  FLUSHALL was accepted");
      process.exitCode = 1;
    } catch (err) {
      console.log(`PASS  FLUSHALL refused: ${(err as Error).message}`);
    }
  }
  await app.del("s09:check");
  await app.quit();
}

main();
