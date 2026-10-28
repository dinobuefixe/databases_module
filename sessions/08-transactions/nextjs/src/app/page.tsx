export default function Home() {
  return (
    <main>
      <h1>Session 08: transactions and concurrency</h1>
      <ul>
        <li>
          <a href="/api/accounts">GET /api/accounts</a>
        </li>
        <li>POST /api/accounts/reset with {`{"balance": 100}`}</li>
        <li>POST /api/accounts/:id/withdraw?strategy=naive|atomic|lock with {`{"amount": 10}`}</li>
      </ul>
      <p>Concurrency test: npm run concurrency. Deadlock demo: npm run deadlock.</p>
    </main>
  );
}
