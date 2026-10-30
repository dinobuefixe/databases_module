insert into reader (reader_id ,name, email, phone)
values
(1, 'Roberto', 'email@email.com', 955955955),
(1, 'Afonso', 'email1@gmail.com', 931912934);
-- vai falhar porque o id é unico

delete fine;
-- vai falhar porque está mal estruturado

INSERT INTO book (title, publisher_id)
VALUES ('Os Lusíadas', 999999);
-- vai falhar porque o publisher com esse id nao existe

INSERT INTO book (title, publication_year, publisher_id)
VALUES ('Livro Antigo', -500, 999999);
-- vai falhar porque o check vai negar o ano do livro

INSERT INTO loan (reader_id, copy_id, loan_date, due_date)
VALUES (999999, 999999, '2026-10-29', '2026-10-01');
-- data de devolução inferior à de emprestimo