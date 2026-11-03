// index.js: explain before and after creating an index on actors.actor_id.
//   mongosh "mongodb://localhost:27017/pagila" index.js

const INDEX_NAME = "actors.actor_id_1";

function explainSummary(label, cursor) {
  const ex = cursor.explain("executionStats");
  const es = ex.executionStats;
  const chain = [];
  for (let s = ex.queryPlanner.winningPlan; s; s = s.inputStage) {
    chain.push(s.stage);
  }
  return {
    label,
    stage: chain[0],
    plan: chain.join(" <- "),
    totalDocsExamined: es.totalDocsExamined,
    totalKeysExamined: es.totalKeysExamined,
    nReturned: es.nReturned,
  };
}

const query = () => db.films.find({ "actors.actor_id": 1 });

// Baseline: make sure no index exists yet.
try {
  db.films.dropIndex(INDEX_NAME);
} catch (e) {
  // index was not there; nothing to drop
}

const before = explainSummary("before index", query());

db.films.createIndex({ "actors.actor_id": 1 }, { name: INDEX_NAME });

const after = explainSummary("after index", query());

print(JSON.stringify([before, after], null, 2));
