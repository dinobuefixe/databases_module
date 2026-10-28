-- EXCLUDE builds a GiST index on (room, during). GiST has no operator class for plain int
-- equality until btree_gist adds one.
CREATE EXTENSION IF NOT EXISTS btree_gist;

-- No two bookings of the same room may overlap. Ranges are [start, end): a booking may start
-- exactly when the previous one ends.
CREATE TABLE IF NOT EXISTS room_booking (
    id     int GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    room   int NOT NULL,
    during tstzrange NOT NULL,
    EXCLUDE USING gist (room WITH =, during WITH &&)
);
