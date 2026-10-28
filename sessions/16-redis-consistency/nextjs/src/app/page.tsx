export default function Home() {
  return (
    <main>
      <h1>Session 16: source of truth, rebuild and persistence</h1>
      <ul>
        <li>
          <a href="/api/customers/1/films">GET /api/customers/1/films</a>: the derived set customer:1:films
        </li>
        <li>
          <a href="/api/verify">GET /api/verify</a>: compare every set with PostgreSQL (200 or 409)
        </li>
        <li>
          <a href="/api/redis/persistence">GET /api/redis/persistence</a>: CONFIG GET for the persistence settings
        </li>
        <li>
          PUT /api/customers/5/username with {`{"username": "ana", "method": "watch"}`} or{" "}
          <code>&quot;method&quot;: &quot;lua&quot;</code>
        </li>
      </ul>
      <p>
        Scripts: <code>npm run flush</code>, <code>npm run rebuild</code>, <code>npm run rebuild:fast</code>,{" "}
        <code>npm run verify</code>.
      </p>
    </main>
  );
}
