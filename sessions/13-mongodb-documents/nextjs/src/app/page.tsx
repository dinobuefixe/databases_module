export default function Home() {
  return (
    <main>
      <h1>Session 13: MongoDB documents, CRUD and validation</h1>
      <ul>
        <li>
          <a href="/api/stores?country=Canada">GET /api/stores?country=Canada</a>: find with dot notation and a
          projection
        </li>
        <li>
          <a href="/api/stores/1">GET /api/stores/1</a>: one store document
        </li>
        <li>POST /api/stores/1/staff with {`{"staff_id": 3, "name": "New Hire"}`}: $push</li>
        <li>POST /api/stores/1/visits: $inc</li>
        <li>POST /api/stores with a document: rejected with 422 when it fails the validator</li>
        <li>
          <a href="/api/stores/explain?country=Canada">GET /api/stores/explain?country=Canada</a>: executionStats for
          the find by country
        </li>
      </ul>
    </main>
  );
}
