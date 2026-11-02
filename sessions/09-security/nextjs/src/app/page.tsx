export default function Home() {
  return (
    <main>
      <h1>Session 09: security</h1>
      <p>Local demonstration. The endpoints marked UNSAFE are vulnerable on purpose.</p>
      <ul>
        <li>
          <a href="/api/whoami">GET /api/whoami</a>: the user the app connects as on each engine
        </li>
        <li>
          <a href="/api/customers/search?email=MARY.SMITH@sakilacustomer.org">GET /api/customers/search?email=</a>:
          parameterised
        </li>
        <li>GET /api/customers/search-unsafe?email=: UNSAFE, SQL built from the input</li>
        <li>POST /api/login: type checks and bcrypt</li>
        <li>POST /api/login-unsafe: UNSAFE, MongoDB filter built from the request body</li>
      </ul>
    </main>
  );
}
