FROM python:3.14

WORKDIR /app
COPY . /app

RUN pip install uv

RUN uv sync

CMD ["uv", "run", "app.py"]