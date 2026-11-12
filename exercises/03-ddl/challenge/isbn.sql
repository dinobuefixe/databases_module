-- Challenge 03 - a base de dados recusa ISBNs invalidos
--
-- Executar numa base de dados vazia:
--   ./scripts/create-db.sh ch03
--   docker compose exec -T postgres psql -U postgres -d ch03 < exercises/03-ddl/challenge/isbn.sql
--
-- Este ficheiro deve correr SEM ON_ERROR_STOP: os 4 ultimos INSERT devem
-- falhar com o erro do dominio isbn13.

-- Reexecutavel: apagar primeiro o que depende do resto.
DROP TABLE IF EXISTS book;
DROP DOMAIN IF EXISTS isbn13;
DROP FUNCTION IF EXISTS is_valid_isbn13(text);

-- 1. Funcao que valida o formato e o digito de controlo de um ISBN-13.
--    IMMUTABLE: para as mesmas entradas devolve sempre o mesmo resultado e
--    nao le nem altera nada da base de dados (necessario para a poder usar
--    num CHECK de um dominio).
CREATE FUNCTION is_valid_isbn13(isbn text)
RETURNS boolean
LANGUAGE sql
IMMUTABLE
AS $$
    WITH d AS (
        SELECT replace(isbn, '-', '') AS digits
    )
    SELECT CASE
        -- So digitos, com hifens apenas entre digitos (nunca no inicio,
        -- nunca no fim, nunca dois seguidos) e exatamente 13 digitos.
        WHEN isbn IS NULL
          OR isbn !~ '^[0-9]+(-[0-9]+)*$'
          OR length(d.digits) <> 13
        THEN false
        -- Digito de controlo: os 12 primeiros digitos multiplicados
        -- alternadamente por 1 e 3; o 13.o digito e (10 - soma % 10) % 10.
        ELSE (
            SELECT (10 - sum(
                       (CASE WHEN pos % 2 = 1 THEN 1 ELSE 3 END)
                       * substr(d.digits, pos, 1)::int
                   ) % 10) % 10
                   = substr(d.digits, 13, 1)::int
            FROM generate_series(1, 12) AS pos
        )
    END
    FROM d;
$$;

-- 2. Dominio que reutiliza a funcao.
CREATE DOMAIN isbn13 AS text CHECK (is_valid_isbn13(VALUE));

-- 3. Tabela que usa o dominio.
CREATE TABLE book (
    book_id integer GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    isbn    isbn13 NOT NULL UNIQUE,
    title   text NOT NULL
);

-- 4. Valores VALIDOS (devem ser aceites).
INSERT INTO book (isbn, title) VALUES ('978-0-306-40615-7', 'Com hifens');
INSERT INTO book (isbn, title) VALUES ('9781402894626',     'Sem hifens');
INSERT INTO book (isbn, title) VALUES ('978-3-16-148410-0', 'Outro ISBN valido');

SELECT book_id, isbn, title FROM book ORDER BY book_id;

-- 5. Valores INVALIDOS (devem falhar com o erro do dominio isbn13).
-- Digito de controlo errado (deveria terminar em 7).
INSERT INTO book (isbn, title) VALUES ('978-0-306-40615-8', 'Controlo errado');
-- Demasiado curto (12 digitos).
INSERT INTO book (isbn, title) VALUES ('978-0-306-4061',    'Curto demais');
-- Hifen no inicio.
INSERT INTO book (isbn, title) VALUES ('-9780306406157',    'Hifen no inicio');
-- Dois hifens seguidos.
INSERT INTO book (isbn, title) VALUES ('978--0306406157',   'Hifens duplos');
