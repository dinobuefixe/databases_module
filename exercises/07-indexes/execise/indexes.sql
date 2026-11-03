-- Q2 and Q3 (rewritten): range scans and sorts on rented_at
CREATE INDEX idx_rented_at ON big_rental (rented_at);
-- Q1: partial index for unreturned rentals per customer
CREATE INDEX idx_customer_unreturned ON big_rental (customer_id) WHERE returned_at IS NULL;
-- Q5: customer filter plus time range, ordered by rented_at within a customer
CREATE INDEX idx_customer_rented ON big_rental (customer_id, rented_at);
-- Q4: no index (see README)
