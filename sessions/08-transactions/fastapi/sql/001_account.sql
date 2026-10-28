-- The constraint is the last line of defence: whatever the code does, no balance goes below zero.
CREATE TABLE IF NOT EXISTS account (
    id      int PRIMARY KEY,
    balance numeric NOT NULL CHECK (balance >= 0)
);
