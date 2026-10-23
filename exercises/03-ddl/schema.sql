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
    publisher_id foreign key publisher(publisher_id)
);

create table reader (
    reader_id int primary key,
    name varchar(255),
    email varchar(255) unique,
    phone int
);

create table author (
    author_id int primary key,
    name varchar(255) 
);

create table book_author (
    book_id int primary key foreign key,
    author_id int primary key foreign key 
);

create table copy(
    copy_id int primary key,
    book_id int foreign key,
    barcode varchar(255) unique,
    shelf_location varchar(255),
    condition varchar(255)
);

create table reservation(
    reservation_id int primary key,
    reader_id int foreign key,
    book_id int foreign key,
    reserved_at datetime,
    status varchar(255)
);
