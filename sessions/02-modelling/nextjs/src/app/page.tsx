export default function Home() {
  return (
    <main>
      <h1>Session 02: modelling and normalisation</h1>
      <ul>
        <li>
          <a href="/api/recipes">GET /api/recipes</a>: list recipes with the stored kcal per serving
        </li>
        <li>POST /api/recipes: create a recipe with its ingredients</li>
        <li>
          <a href="/api/recipes/1">GET /api/recipes/1</a>: recipe detail with author and ingredients
        </li>
        <li>PUT /api/recipes/:id/ingredients: replace the ingredients and recalculate kcal</li>
        <li>DELETE /api/recipes/:id: delete a recipe and its lines</li>
        <li>
          <a href="/api/ingredients">GET /api/ingredients</a> and POST /api/ingredients
        </li>
        <li>
          <a href="/api/authors">GET /api/authors</a>: authors with their recipe count
        </li>
      </ul>
    </main>
  );
}
