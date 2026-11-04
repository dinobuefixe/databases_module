CREATE INDEX idx_customer_unreturned ON big_rental (customer_id) WHERE returned_at IS NULL;
CREATE INDEX idx_rented_at ON big_rental (rented_at);
CREATE INDEX idx_customer_rented ON big_rental (customer_id, rented_at);