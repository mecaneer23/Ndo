FROM python:slim-bookworm

WORKDIR /app

COPY todo.py /app/todo.py
COPY README.md /app/README.md

CMD ["python", "todo.py"]