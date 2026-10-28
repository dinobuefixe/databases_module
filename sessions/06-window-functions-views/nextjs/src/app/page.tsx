export default function Home() {
  return (
    <main>
      <h1>Session 06: window functions and views</h1>
      <ul>
        <li>
          <a href="/api/films/longest-per-rating?top=2">GET /api/films/longest-per-rating?top=2</a>: DENSE_RANK per
          rating
        </li>
        <li>
          <a href="/api/customers/1/payments">GET /api/customers/1/payments</a>: running total with SUM OVER
        </li>
        <li>
          <a href="/api/customers/1/rental-gaps">GET /api/customers/1/rental-gaps</a>: time since the previous rental
          with LAG
        </li>
        <li>
          <a href="/api/daily-rentals?from=2022-05-24&days=10">GET /api/daily-rentals</a>: read the materialised view
        </li>
        <li>POST /api/daily-rentals/refresh: REFRESH MATERIALIZED VIEW CONCURRENTLY</li>
      </ul>
    </main>
  );
}
