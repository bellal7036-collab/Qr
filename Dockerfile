FROM python:3.11

RUN apt update && apt install -y libzbar0

WORKDIR /app
COPY . .

RUN pip install -r requirements.txt

CMD ["python", "q.py"]
