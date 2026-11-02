import functools
import json
import uuid
import datetime

from sqlalchemy import Engine
from sqlalchemy.orm import Session

from session8.connection import get_engine, get_inputs_connstr, get_insights_connstr
from session8.models.inputs import Task
from session8.models.insights import InsightReport, InsightReportContent


def with_engine(conn_func, param_name="engine"):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            engine = get_engine(conn_func())
            try:
                return func(*args, **{param_name: engine, **kwargs})
            finally:
                engine.dispose()
        return wrapper
    return decorator

@with_engine(get_inputs_connstr, param_name="engine")
async def get_task_by_id(task_uuid: str, *, engine: Engine) -> bool:

    with Session(engine) as session:
        task = session.get(Task, task_uuid)
        return task is not None

@with_engine(get_inputs_connstr, param_name="inputs_engine")
@with_engine(get_insights_connstr, param_name="insights_engine")
async def generate_reports_for_task(
    task_id: str,
    *,
    inputs_engine: Engine,
    insights_engine: Engine,
):
    with Session(inputs_engine) as session:
        participants = list(session.query(Task).filter(Task.id == task_id).first().participants)

    if not participants:
        raise ValueError(f"No participants found for task ID {task_id}.")

    with Session(insights_engine) as session:
        # Example: generate reports for each participant
        for participant in participants:
            new_report = InsightReport(
                id = uuid.uuid4(),
                participant_id=participant.id, task_id=task_id,
                created_at = datetime.datetime.now(),
                )
            session.add(new_report)
            session.commit()
            session.refresh(new_report)

            report_content = InsightReportContent(
                id = uuid.uuid4(),
                insight_report_id=new_report.id,
                content = str(json.dumps(
                    {
                        "participant_id": str(participant.id),
                        "task_id": str(task_id)
                    }
                ))
            )
            session.add(report_content)

        session.commit()

