// Starts two worker processes at the same time. Only one of them runs the job.
import { spawn } from "node:child_process";

const run = (name: string) =>
  new Promise<void>((resolve) => {
    spawn("npx", ["tsx", "scripts/lock-worker.ts", name], { stdio: "inherit" }).on("exit", () => resolve());
  });

async function main() {
  console.log("Starting worker-a and worker-b together");
  await Promise.all([run("worker-a"), run("worker-b")]);
  console.log("\nBoth finished. Run it again: the lock was released, so one of them gets it again.");
}

main();
