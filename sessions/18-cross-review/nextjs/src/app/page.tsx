export default function Home() {
  return (
    <main>
      <h1>Film ratings</h1>
      <ul>
        <li>
          <a href="/api/customers/search?q=smi">GET /api/customers/search?q=smi</a>
        </li>
        <li>
          <a href="/api/customers/by-email?email=mary.smith@sakilacustomer.org">GET /api/customers/by-email?email=...</a>
        </li>
        <li>
          <a href="/api/customers/1/profile">GET /api/customers/1/profile</a>
        </li>
        <li>PUT /api/admin/customers/1/profile</li>
        <li>POST /api/films/1/ratings</li>
        <li>
          <a href="/api/films/1/rating">GET /api/films/1/rating</a>
        </li>
      </ul>
    </main>
  );
}
