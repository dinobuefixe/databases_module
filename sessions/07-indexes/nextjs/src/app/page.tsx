export default function Home() {
  return (
    <main>
      <h1>Session 07: indexes and optimisation</h1>
      <p>EXPLAIN (ANALYZE, BUFFERS) for each tutorial query. Create and drop indexes with npm run index.</p>
      <ul>
        <li>
          <a href="/api/explain/customer-latest?customer=42">GET /api/explain/customer-latest?customer=42</a>
        </li>
        <li>
          <a href="/api/explain/open-rentals">GET /api/explain/open-rentals</a>
        </li>
        <li>
          <a href="/api/explain/customer-email?email=MARY.SMITH@sakilacustomer.org">
            GET /api/explain/customer-email?email=MARY.SMITH@sakilacustomer.org
          </a>
        </li>
        <li>
          <a href="/api/explain/recent-rentals?days=730">GET /api/explain/recent-rentals?days=730</a> (add{" "}
          <code>&amp;force_index=1</code> to time the index scan the planner rejected)
        </li>
        <li>
          <a href="/api/indexes">GET /api/indexes</a>: indexes that exist now, with their size
        </li>
      </ul>
    </main>
  );
}
