const questions = [
  ["rentals-per-staff", "How many rentals has each staff member handled, per store?"],
  ["frequent-customers", "Which customers rented more than 40 films? (HAVING)"],
  ["rentals-per-customer", "How many rentals has each customer made, including customers with none? (LEFT JOIN)"],
  ["films-without-inventory", "Which films have no copy in any store? (anti-join)"],
  ["customers-without-rentals", "Which customers have never rented a film? (LEFT JOIN anti-join)"],
  ["duplicate-customer-names", "Which customers share their name with another customer? (self join)"],
  ["films-longer-than-average", "Which films are longer than the average film? (subquery in WHERE)"],
  ["films-above-rating-average", "Which films are longer than the average for their rating? (correlated subquery)"],
  ["customer-totals", "How many rentals and how much paid per customer? (subqueries in FROM)"],
  ["above-average-spenders", "Which customers spent more than the average customer? (CTE)"],
];

export default function Home() {
  return (
    <main>
      <h1>Session 05: joins, aggregation, subqueries and CTEs</h1>
      <p>Each question has a Prisma version (?impl=orm) and a SQL version (?impl=sql). The server log shows the SQL.</p>
      <ul>
        {questions.map(([path, question]) => (
          <li key={path}>
            {question} <a href={`/api/${path}?impl=orm`}>orm</a> | <a href={`/api/${path}?impl=sql`}>sql</a>
          </li>
        ))}
      </ul>
    </main>
  );
}
