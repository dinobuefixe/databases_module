import "dotenv/config";

// Fire N withdrawals of 10 at the same time against a balance of 100, for each
// strategy, through the running API. The rule: money taken out must equal
// what left the account, so exactly 10 withdrawals may succeed.
// Usage: npm run concurrency -- [requests]   (default 50; start the app first)
const API = process.env.API_URL ?? "http://localhost:3000";
const requests = Number(process.argv[2] ?? 50);
const AMOUNT = 10;
const START = 100;

async function post(path: string, body: unknown) {
  const res = await fetch(`${API}${path}`, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify(body),
  });
  return { status: res.status, body: await res.json() };
}

async function main() {
  let broken = false;
  for (const strategy of ["naive", "atomic", "lock"]) {
    await post("/api/accounts/reset", { balance: START });
    const results = await Promise.all(
      Array.from({ length: requests }, () => post(`/api/accounts/1/withdraw?strategy=${strategy}`, { amount: AMOUNT })),
    );
    const ok = results.filter((r) => r.status === 200).length;
    const refused = results.filter((r) => r.status === 409).length;
    const errors = results.length - ok - refused;
    const accounts: { id: number; balance: string }[] = await (await fetch(`${API}/api/accounts`)).json();
    const final = Number(accounts.find((a) => a.id === 1)!.balance);
    const holds = ok * AMOUNT === START - final && ok === START / AMOUNT;
    broken ||= strategy !== "naive" && !holds;
    console.log(
      `${strategy.padEnd(7)} ${String(ok).padStart(3)} succeeded, ${String(refused).padStart(3)} refused, ` +
        `${errors} errors, final balance ${final} -> ${holds ? "rule holds" : `RULE BROKEN: paid out ${ok * AMOUNT}, balance fell by ${START - final}`}`,
    );
  }
  // naive is expected to break; the script fails only if a fix does.
  process.exitCode = broken ? 1 : 0;
}

main();
