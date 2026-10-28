export default function Home() {
  return (
    <main>
      <h1>Session 19: delivery demo</h1>
      <ul>
        <li>
          <a href="/api/health">GET /api/health</a>
        </li>
        <li>
          <a href="/api/accounts/1">GET /api/accounts/1</a> and POST /api/accounts/1/withdraw
        </li>
        <li>
          <a href="/api/verify">GET /api/verify</a>: Redis against PostgreSQL
        </li>
      </ul>
      <p>
        The demo itself runs from the terminal: <code>npm run demo:concurrency</code>, <code>npm run demo:rebuild</code>,{" "}
        <code>npm run demo:explain</code>.
      </p>
    </main>
  );
}
