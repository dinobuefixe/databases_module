-- How many rentals has each staff member handled, per store?
SELECT s.store_id, st.first_name, st.last_name, count(*) AS rentals
FROM rental r
JOIN staff st ON st.staff_id = r.staff_id
JOIN store s  ON s.store_id  = st.store_id
GROUP BY s.store_id, st.staff_id
ORDER BY s.store_id, rentals DESC;
