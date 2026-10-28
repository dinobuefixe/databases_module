export default function Home() {
  return (
    <main>
      <h1>Session 12: migrations, transactions and API</h1>
      <ul>
        <li>
          <a href="/api/customers/1">GET /api/customers/1</a>: a customer with the new <code>tier</code> and{" "}
          <code>balance</code> columns
        </li>
        <li>POST /api/customers/1/top-up with {`{"amount": 50}`}: add to the balance</li>
        <li>
          POST /api/customers/1/charge with {`{"amount": 10.5}`}: charge inside a transaction with a row lock (404, 409,
          422)
        </li>
      </ul>
    </main>
  );
}
