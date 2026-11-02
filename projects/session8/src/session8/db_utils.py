from faker import Faker
from sqlalchemy import UUID, Engine
from sqlalchemy.orm import Session

from session8.models import inputs

faker = Faker()

def create_new_task(engine: Engine, task_id:UUID):
    # Implement the logic to create a new task in the database
    with Session(engine) as session:
        new_task = inputs.Task(
            id=task_id,
            name=faker.word(),
            description=faker.sentence(),
            created_at=faker.date_time(),
            finished_at=faker.date_time(),
            outcome=faker.word(),
            status=faker.word(),
            )
        session.add(new_task)
        session.commit()

def create_new_participant(engine: Engine, task_id:UUID, participant_id:UUID):
    # Implement the logic to create a new participant in the database
    with Session(engine) as session:
        new_participant = inputs.Participant(
            id=participant_id,
            task_id=task_id,
            name=faker.name(),
            height=faker.random_int(min=100, max=200),
            weight=faker.random_int(min=30, max=150),
            date_of_birth=faker.date_of_birth(),
            city=faker.city(),
            heart_rate=faker.random_int(min=60, max=100),
            blood_pressure_systolic=faker.random_int(min=90, max=140),
            blood_pressure_diastolic=faker.random_int(min=60, max=90),
        )
        session.add(new_participant)
        session.commit()