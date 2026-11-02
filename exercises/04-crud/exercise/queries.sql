--1--

SELECT title, length, rating 
FROM FILM
WHERE length > 120 
AND rating = 'PG-13'
ORDER BY title 

--2--

SELECT first_name, last_name
from actor 
where last_name ilike '%son%';  

--3--

select customer.first_name, customer.last_name, rental.last_update
from rental
inner join customer on rental.customer_id = customer.customer_id  
where rental.return_date is null;  

--4--

select max(rental_duration)
from film
group by rental_duration
order by rental_duration  

--5--

select title,release_year,length
from film
order by title
offset 20 limit 10

--6--

select count(rental_id) as rentals
from rental
where rental_date BETWEEN '2026-01-01' AND '2026-01-31'
--where rental_date >= '2026-01-01' AND rental_date < '2026-02-01'
-- o between nunca é usado para timestamp porque "arredonda" a hora para o dia e exclui alguns valores

--7--

INSERT INTO actor (first_name,Last_name)
VALUES ('ADA',  'LOVELACE')
RETURNING actor_id;

--8--

BEGIN;

SELECT count(*)
FROM film
WHERE rating = 'NC-17'
  AND length < 60;

UPDATE film
SET rental_rate = rental_rate + 0.50
WHERE rating = 'NC-17'
  AND length < 60
RETURNING film_id, title, rental_rate;

commit;

--9--

INSERT INTO actor_award (actor_id, awards)
VALUES (1, 1)
ON CONFLICT (actor_id)
DO UPDATE SET awards = actor_award.awards + 1;

--10--

INSERT INTO actor_award (actor_id, awards)
VALUES (2, 5)
ON CONFLICT (actor_id) DO NOTHING;

--11--

INSERT INTO payment (customer_id, staff_id, rental_id, amount, payment_date)
VALUES
    (1, 2, 76, 0.01, '2026-07-30 12:00+00'),
    (1, 2, 76, 0.01, '2026-07-30 12:00+00'),
    (1, 2, 76, 0.01, '2026-07-30 12:00+00')
RETURNING payment_id;

--12--

BEGIN;

SELECT count(*)
FROM payment
WHERE customer_id = 1
  AND staff_id = 2
  AND rental_id = 76
  AND amount = 0.01
  AND payment_date = '2026-07-30 12:00+00';

DELETE FROM payment
WHERE customer_id = 1
  AND staff_id = 2
  AND rental_id = 76
  AND amount = 0.01
  AND payment_date = '2026-07-30 12:00+00'
RETURNING payment_id, customer_id, staff_id, rental_id, amount, payment_date;

COMMIT;