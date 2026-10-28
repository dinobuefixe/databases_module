from sqlalchemy import Column, Date
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy import ForeignKey
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class InsightReport(Base):
    __tablename__ = 'insight_reports'

    id = Column(UUID, primary_key=True)
    task_id = Column(UUID, nullable=False)
    participant_id = Column(UUID, nullable=False)
    created_at = Column(Date, nullable=False)


class InsightReportContent(Base):
    __tablename__ = 'insight_report_contents'

    id = Column(UUID, primary_key=True)
    insight_report_id = Column(UUID,ForeignKey('insight_reports.id'), nullable=False)
    content = Column(JSONB, nullable=False)