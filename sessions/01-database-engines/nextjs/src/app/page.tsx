export default function Home() {
  return (
    <main>
      <h1>Session 01: database engines</h1>
      <ul>
        <li>
          <a href="/api/health">GET /api/health</a>: ping PostgreSQL, MongoDB and Redis
        </li>
        <li>
          <a href="/api/hello">GET /api/hello</a>: read the last messages from each engine
        </li>
        <li>POST /api/hello with {`{"msg": "..."}`}: write a message to each engine</li>
      </ul>
    </main>
  );
}
