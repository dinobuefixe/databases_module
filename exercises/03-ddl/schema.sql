create database library if not exists;

create table publisher(
    publisher_id int primary key,
    name varchar(255)
);

create table book (
    book_id int primary key,
    title varchar(255),
    isbn varchar(255) unique,
    publication_year int,
    publisher_id foreign key references publisher(publisher_id)
);

create table reader (
    reader_id int primary key,
    name varchar(255),
    email varchar(255) unique,
    phone int check ()
);

create table author (
    author_id int primary key,
    name varchar(255) 
);

create table book_author (
    book_id int primary key foreign key references book(book_id),
    author_id int primary key foreign key references author(author_id) 
);

create table copy(
    copy_id int primary key,
    book_id int foreign key references book(book_id),
    barcode varchar(255) unique,
    shelf_location varchar(255),
    condition varchar(255)
);

create table reservation(
    reservation_id int primary key,
    reader_id int foreign key references reader(reader_id) on delete set null, -- i think it makes more sense to set null instead of delete every data about this user 
    book_id int foreign key references book(book_id),
    reserved_at datetime,
    status varchar(255)
);


create table loan(
    load_id int primary key,
    reader_id int foreign key references reader(reader_id),
    copy_id int foreign key references copy(copy_id),
    loan_date date,
    due_date date,
    returned_date date
);

create table fine(
    fine_id int primary key,
    loan_id int foreign key references loan(loan_id),
    amount float,
    issued_date date,
    paid_date date
);