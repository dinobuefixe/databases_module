export default function Home() {
  return (
    <main>
      <h1>Session 11: ORM and the N+1 problem</h1>
      <ul>
        <li>
          <a href="/api/customers?limit=20&eager=false">GET /api/customers?limit=20&amp;eager=false</a>: one query per
          customer (N+1)
        </li>
        <li>
          <a href="/api/customers?limit=20&eager=true">GET /api/customers?limit=20&amp;eager=true</a>: rentals loaded
          with <code>include</code>; add <code>&amp;strategy=join</code> or <code>&amp;strategy=count</code>
        </li>
        <li>
          <a href="/api/customers/top?limit=5">GET /api/customers/top?limit=5</a>: top customers by rentals
        </li>
      </ul>
    </main>
  );
}
