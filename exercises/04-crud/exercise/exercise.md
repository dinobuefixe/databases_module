# Exercise

## 1. 
```bash 
SELECT title, length, rating 
FROM FILMS 
WHERE lenght > 120 
AND rating = "PG-13"
ORDER BY title 
```

## 2.
```bash
SELECT first_name, last_name
from actor 
where last_name ilike '%son%';      
```

## 3.
```bash
select customer.first_name, customer.last_name, rental.last_update
from rental
inner join customer on rental.customer_id = customer.customer_id  
where rental.return_date is null;   
```

## 4.
```bash
select max(rental_duration)
from film
group by rental_duration
order by rental_duration  
```

## 5.
```bash
select title,release_year,length
from film
order by title
offset 20 limit 10
```

## 6. 
```bash
select count(rental_id) as rentals
from rental
where rental_date BETWEEN '2026-01-01' AND '2026-01-31'
--where rental_date >= '2026-01-01' AND rental_date < '2026-02-01'
-- o between nunca é usado para timestamp porque "arredonda" a hora para o dia e exclui alguns valores
``` 

## 7.
```bash
INSERT INTO actor (first_name,Last_name)
VALUES ('ADA',  'LOVELACE')
RETURNING actor_id;
```

## 8.
```bash
INSERT INTO actor (first_name,Last_name)
VALUES ('ADA',  'LOVELACE')
RETURNING actor_id;
```