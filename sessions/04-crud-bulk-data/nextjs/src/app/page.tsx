export default function Home() {
  return (
    <main>
      <h1>Session 04: CRUD, upsert and bulk data</h1>
      <ul>
        <li>
          <a href="/api/films?rating=R&q=love&sort=length&order=desc&limit=10">
            GET /api/films?rating=R&amp;q=love&amp;sort=length&amp;order=desc&amp;limit=10
          </a>
          : filter, search, sort and paginate
        </li>
        <li>POST /api/actors: insert and get the generated id back</li>
        <li>POST /api/films/rental-rate: update checked against an expected row count</li>
        <li>POST /api/films/:id/views: upsert a view counter</li>
      </ul>
      <p>Bulk loads are scripts: npm run bulk:person and npm run bulk:reading.</p>
    </main>
  );
}
