export default function Home() {
  return (
    <main>
      <h1>Session 14: aggregation pipelines and reports</h1>
      <ul>
        <li>
          <a href="/api/films/by-rating">GET /api/films/by-rating</a>: $group by rating with $avg
        </li>
        <li>
          <a href="/api/actors/top">GET /api/actors/top</a>: $unwind the embedded actors, top 10
        </li>
        <li>
          <a href="/api/rentals/per-month">GET /api/rentals/per-month</a>: $dateTrunc on the embedded rentals
        </li>
        <li>
          <a href="/api/customers/by-activity">GET /api/customers/by-activity</a>: $bucket on total rentals
        </li>
        <li>
          <a href="/api/customers/summary">GET /api/customers/summary</a>: $facet, per store and the 3 most active
        </li>
        <li>
          <a href="/api/rentals/latest">GET /api/rentals/latest</a>: $lookup the film of the 5 latest rentals
        </li>
        <li>
          <a href="/api/rentals/match-position">GET /api/rentals/match-position</a>: $match late and early, with
          explain
        </li>
        <li>POST /api/reports/rentals-per-month: $merge rentals per month into a collection (same result every run)</li>
        <li>POST /api/reports/monthly/2022-07: freeze a monthly report (201, then 409)</li>
        <li>
          <a href="/api/reports/monthly/2022-07">GET /api/reports/monthly/2022-07</a>: read it
        </li>
      </ul>
    </main>
  );
}
