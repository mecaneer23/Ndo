#!/usr/bin/bash
docker run -v "$1":/app/todo.txt -it todo || echo "Make sure to include a relative path to open"