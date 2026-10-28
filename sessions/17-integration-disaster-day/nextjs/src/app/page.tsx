export default function Home() {
  return (
    <main>
      <h1>Session 17: integration and disaster day</h1>
      <ul>
        <li>
          <a href="/api/health">GET /api/health</a>: ping the three engines
        </li>
        <li>
          <a href="/api/accounts/1">GET /api/accounts/1</a>, POST /api/accounts/1/withdraw, POST
          /api/accounts/1/reset (PostgreSQL)
        </li>
        <li>
          POST /api/rentals, then <a href="/api/customers/1/films">GET /api/customers/1/films</a> (PostgreSQL, then
          Redis)
        </li>
        <li>
          <a href="/api/verify">GET /api/verify</a>: Redis against PostgreSQL
        </li>
        <li>POST and GET /api/reports/monthly/2022-07 (PostgreSQL into MongoDB)</li>
      </ul>
    </main>
  );
}
