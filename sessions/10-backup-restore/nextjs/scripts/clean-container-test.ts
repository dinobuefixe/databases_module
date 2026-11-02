import path from "node:path";
import { DB, dumpFile, psql, run, seconds } from "./shell";

// npm run clean-container-test -- [dump]
// Restores the dump into a brand-new postgres:18 container that shares nothing
// with the usual setup, then compares a known count with the live database.
// The container is named s10-nextjs-pgtest and removed at the end.
const CONTAINER = process.env.TEST_CONTAINER ?? "s10-nextjs-pgtest";
const sleep = (ms: number) => new Promise((r) => setTimeout(r, ms));

async function main() {
  const dump = dumpFile(process.argv[2]);
  console.log(`Starting ${CONTAINER} (postgres:18)`);
  // --rm: Docker deletes the container when it stops. No port is published.
  await run("docker", ["run", "--rm", "-d", "--name", CONTAINER, "-e", "POSTGRES_PASSWORD=test", "postgres:18"]);
  try {
    // Wait until the server inside accepts connections.
    for (let i = 0; ; i++) {
      const ready = await run("docker", ["exec", CONTAINER, "pg_isready", "-U", "postgres"], { allowFailure: true });
      if (ready.code === 0) break;
      if (i > 60) throw new Error("the test container did not become ready");
      await sleep(500);
    }
    await sleep(1000); // the image restarts the server once after initialising

    await run("docker", ["exec", CONTAINER, "createdb", "-U", "postgres", "restore_test"]);
    const start = performance.now();
    const restore = await run(
      "docker",
      ["exec", "-i", CONTAINER, "pg_restore", "-U", "postgres", "-d", "restore_test", "--no-owner"],
      { stdinFile: dump, allowFailure: true },
    );
    console.log(`Restored ${path.basename(dump)} in ${seconds(start)} s (exit code ${restore.code})`);
    if (restore.code !== 0) console.log(restore.stderr.trim());

    const sql = "SELECT count(*) FROM rental";
    const inContainer = (
      await run("docker", ["exec", CONTAINER, "psql", "-U", "postgres", "-d", "restore_test", "-tA", "-c", sql])
    ).stdout.trim();
    const live = (await psql(DB, sql)).stdout.trim();
    const same = inContainer === live;
    console.log(`${sql}: ${inContainer} in the clean container, ${live} in ${DB} -> ${same ? "OK" : "MISMATCH"}`);
    if (!same) process.exitCode = 1;
  } finally {
    await run("docker", ["stop", CONTAINER], { allowFailure: true });
    console.log(`Stopped and removed ${CONTAINER}`);
  }
}

main().catch((err) => {
  console.error(err.message);
  process.exitCode = 1;
});
