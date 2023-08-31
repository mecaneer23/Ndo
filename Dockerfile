FROM python:slim-bookworm

WORKDIR /app

ADD todo.py /app/todo.py
ADD README.md /app/README.md

CMD ["python", "todo.py"]