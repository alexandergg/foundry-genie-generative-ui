FROM python:3.12-slim

WORKDIR /app/user_agent

COPY pyproject.toml ./
COPY main.py hosted_main.py ./
COPY src ./src

RUN python -m pip install --no-cache-dir --upgrade pip \
    && python -m pip install --no-cache-dir .

EXPOSE 8088

CMD ["python", "hosted_main.py"]
