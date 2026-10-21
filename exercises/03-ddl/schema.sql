create database library if not exists;

create table publisher(
    publisher_id int primary key,
    name varchar(255)
)

create table book (
    book_id int primary key,
    title varchar(255),
    isbn varchar(255) unique,
    
)
