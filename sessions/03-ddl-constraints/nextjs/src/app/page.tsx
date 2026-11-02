export default function Home() {
  return (
    <main>
      <h1>Session 03: DDL, data types and constraints</h1>
      <p>Constraint violations come back as 409 or 422 with the constraint name.</p>
      <ul>
        <li>
          <a href="/api/authors">GET /api/authors</a>, POST /api/authors, DELETE /api/authors/:id (RESTRICT)
        </li>
        <li>
          <a href="/api/ingredients">GET /api/ingredients</a>, POST /api/ingredients
        </li>
        <li>
          <a href="/api/recipes">GET /api/recipes</a>, POST /api/recipes, DELETE /api/recipes/:id (CASCADE)
        </li>
      </ul>
    </main>
  );
}
