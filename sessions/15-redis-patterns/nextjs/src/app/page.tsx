export default function Home() {
  return (
    <main>
      <h1>Session 15: Redis data structures and patterns</h1>
      <ul>
        <li>POST /api/films/42/views: INCR a counter</li>
        <li>
          PUT /api/films/42/hash, then <a href="/api/films/42/hash">GET /api/films/42/hash</a>: HSET and HGETALL
        </li>
        <li>
          POST /api/visitors with {`{"customer_id": 5}`}, then <a href="/api/visitors">GET /api/visitors</a>: SADD and
          SCARD
        </li>
        <li>
          <a href="/api/search?q=alien">GET /api/search?q=alien</a>: ZINCRBY the term; rate limited to 10 per minute
        </li>
        <li>
          <a href="/api/search/popular">GET /api/search/popular</a>: ZRANGE ... REV WITHSCORES
        </li>
        <li>
          <a href="/api/customers/5">GET /api/customers/5</a>: cache-aside (hit or miss); PATCH deletes the key
        </li>
      </ul>
    </main>
  );
}
