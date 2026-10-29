CREATE TABLE publisher (
    publisher_id SERIAL PRIMARY KEY,
    name         VARCHAR(255) NOT NULL
);

CREATE TABLE book (
    book_id          SERIAL PRIMARY KEY,
    title            VARCHAR(255) NOT NULL,
    isbn             VARCHAR(20) UNIQUE,
    publication_year INT CHECK (publication_year > 0),
    publisher_id     INT NOT NULL,
    FOREIGN KEY (publisher_id) REFERENCES publisher(publisher_id)
);

CREATE TABLE reader (
    reader_id SERIAL PRIMARY KEY,
    name      VARCHAR(255) NOT NULL,
    email     VARCHAR(255) NOT NULL UNIQUE,
    phone     VARCHAR(20)
);

CREATE TABLE author (
    author_id SERIAL PRIMARY KEY,
    name      VARCHAR(255) NOT NULL
);

CREATE TABLE book_author (
    book_id   INT NOT NULL,
    author_id INT NOT NULL,
    PRIMARY KEY (book_id, author_id),
    FOREIGN KEY (book_id)   REFERENCES book(book_id) ON DELETE CASCADE,
    FOREIGN KEY (author_id) REFERENCES author(author_id) ON DELETE CASCADE
);

CREATE TABLE book_copy (
    copy_id        SERIAL PRIMARY KEY,
    book_id        INT NOT NULL,
    barcode        VARCHAR(255) UNIQUE,
    shelf_location VARCHAR(255),
    copy_condition VARCHAR(50),
    FOREIGN KEY (book_id) REFERENCES book(book_id)
);

CREATE TABLE reservation (
    reservation_id SERIAL PRIMARY KEY,
    reader_id      INT NULL,
    book_id        INT NOT NULL,
    reserved_at    TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    status         VARCHAR(50) NOT NULL,
    FOREIGN KEY (reader_id) REFERENCES reader(reader_id) ON DELETE SET NULL,
    FOREIGN KEY (book_id)   REFERENCES book(book_id)
);

CREATE TABLE loan (
    loan_id       SERIAL PRIMARY KEY,
    reader_id     INT NOT NULL,
    copy_id       INT NOT NULL,
    loan_date     DATE NOT NULL,
    due_date      DATE NOT NULL,
    returned_date DATE,
    CHECK (due_date >= loan_date),
    FOREIGN KEY (reader_id) REFERENCES reader(reader_id),
    FOREIGN KEY (copy_id)   REFERENCES book_copy(copy_id)
);

CREATE TABLE fine (
    fine_id     SERIAL PRIMARY KEY,
    loan_id     INT NOT NULL,
    amount      NUMERIC(10,2) NOT NULL CHECK (amount >= 0),
    issued_date DATE NOT NULL,
    paid_date   DATE,
    FOREIGN KEY (loan_id) REFERENCES loan(loan_id)
);