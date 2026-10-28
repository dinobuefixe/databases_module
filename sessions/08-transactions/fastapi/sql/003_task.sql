-- A work queue. done_by is NULL while the task waits. runs counts how many times the task was
-- processed: when the queue is empty, every task must have runs = 1.
CREATE TABLE IF NOT EXISTS task (
    id      int GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    done_by text,
    runs    int NOT NULL DEFAULT 0
);
