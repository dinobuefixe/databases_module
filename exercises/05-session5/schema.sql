create database session05;

create table staff(
    staffId int primary key,
    firstName varchar(255),
    lastName varchar(255),
    dateOfBirth date,
    salary float,
    specification varchar(255),
    contact int,
    NIF int
);

create table case(
    caseId int primary key,
    chargedStaff int foreign key,
    description varchar(255),
    budget int,
    staff int
    CONSTRAINT fk_staff_case 
    FOREIGN KEY (staff) 
    REFERENCES staff(staffId)
    patient int
    CONSTRAINT fk_patient_case 
    FOREIGN KEY (patient) 
    REFERENCES patient(patientId)
);

create table exams(
    examId int primary key,
    results varchar(255),
    examFor varchar(255),
    receiptGiven varchar(255),
    case int
    CONSTRAINT fk_case_exams
    FOREIGN KEY (case)
    REFERENCES case(caseId)
);

create table rooms(
    roomId int primary key,
    specification varchar(255),
    number int,
    staff INT
    CONSTRAINT fk_staff_rooms  
    FOREIGN KEY (staff) 
    REFERENCES staff(staffId)
);

create table shifts(
    shiftsId int primary key,
    whenStarts date,
    whenEnds date,
    staff int
    CONSTRAINT fk_staff_shift  
    FOREIGN KEY (staff) 
    REFERENCES staff(staffId)
)

create table insurance(
    insuranceId int primary key,
    name varchar(30),
    priceMonthly int
) 

create table finance(
    financeId int primary key,
    insurance int
    CONSTRAINT fk_insirance_finance
    foreign key insurance
    references insurance(insuranceId)
);

create table patient(
    patientId int primary key,
    firstName varchar(255),
    lastName varchar(255),
    dateOfBirth date,
    contact int,
    NIF int,
    insurance int
    CONSTRAINT fk_patient_insurance
    foreign key (insurance)
    references insurance(insuranceId)
);