from dotenv import load_dotenv
from fastapi import FastAPI, Response, status

from session8.reports import generate_reports_for_task_id

load_dotenv()

api = FastAPI(title="Generator service")


@api.get("/healthcheck")
async def healthcheck():
    """
    Healthcheck endpoint to verify if the API is running.
    Returns a JSON object with the status of the service.
    """
    return {"status": "ok"}


@api.post("/generate", status_code=status.HTTP_201_CREATED)
async def generate(task_id: str):
    """
    Generate endpoint to initiate a task based on the provided task ID.
    Returns a JSON object with the status of the task initiation.
    """
    await generate_reports_for_task_id(task_id)

    return Response(content="Task Terminated", status_code=status.HTTP_201_CREATED)
