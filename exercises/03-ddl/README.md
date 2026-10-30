```
insert into reader (reader_id ,name, email, phone)
values
(1, 'Roberto', 'email@email.com', 955955955),
(1, 'Afonso', 'email1@gmail.com', 931912934);
-- vai falhar porque o id é unico
```
```
SQL Error [23505]: ERROR: duplicate key value violates unique constraint "reader_pkey"
  Detail: Key (reader_id)=(1) already exists.
```
```
delete fine;
-- vai falhar porque está mal estruturado
```
```
SQL Error [42601]: ERROR: syntax error at or near "fine"
  Position: 8 
```
```
INSERT INTO book (title, publisher_id)
VALUES ('Os Lusíadas', 999999);
-- vai falhar porque o publisher com esse id nao existe
```
```
SQL Error [23503]: ERROR: insert or update on table "book" violates foreign key constraint "book_publisher_id_fkey"
  Detail: Key (publisher_id)=(999999) is not present in table "publisher".
```
```
INSERT INTO book (title, publication_year, publisher_id)
VALUES ('Livro Antigo', -500, 999999);
-- vai falhar porque o check vai negar o ano do livro
```
```
SQL Error [23514]: ERROR: new row for relation "book" violates check constraint "book_publication_year_check"
  Detail: Failing row contains (2, Livro Antigo, null, -500, 999999).
```
```
INSERT INTO loan (reader_id, copy_id, loan_date, due_date)
VALUES (999999, 999999, '2026-10-29', '2026-10-01');
-- data de devolução inferior à de emprestimo
```
```
SQL Error [23514]: ERROR: new row for relation "loan" violates check constraint "loan_check"
  Detail: Failing row contains (1, 999999, 999999, 2026-10-29, 2026-10-01, null).
```