from sqlalchemy import Column, Date, Integer, String, Float, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class Task(Base):
    __tablename__ = 'tasks'

    id = Column(UUID, primary_key=True)
    name = Column(String, nullable=False)
    description = Column(String, nullable=True)
    created_at = Column(Date, nullable=False)
    finished_at = Column(Date, nullable=True)
    outcome = Column(String, nullable=True)
    status = Column(String, nullable=False)

class Participant(Base):
    __tablename__ = 'participants'

    id = Column(UUID, primary_key=True)
    name = Column(String, nullable=False)
    height = Column(Float, nullable=False)
    weight = Column(Float, nullable=False)
    date_of_birth = Column(Date, nullable=False)
    city = Column(String, nullable=False)
    heart_rate = Column(Integer, nullable=False)
    blood_pressure_systolic = Column(Integer, nullable=False)
    blood_pressure_diastolic = Column(Integer, nullable=False)
    task_id = Column(UUID,ForeignKey('tasks.id'), nullable=False)
