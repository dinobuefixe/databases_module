from sqlalchemy import UUID

from session8.db_actions import generate_reports_for_task, get_task_by_id


async def generate_reports_for_task_id(task_id: str):
    # Implement the logic to generate reports for the given task ID

    task_exists: bool = await get_task_by_id(task_id)

    if not task_exists:
        raise ValueError(f"Task with ID {task_id} does not exist.")

    # Implement the report generation logic here
    await generate_reports_for_task(task_id)