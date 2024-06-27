FROM containers.cisco.com/cway/hardened-python:3.11-alpine

LABEL quay.expires-after=12w

WORKDIR /app

COPY . .

RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 5000

ENTRYPOINT [ "uvicorn", "src.main:app", "--host=0.0.0.0", "--port=5000" ]
