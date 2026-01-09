FROM python:3.7-slim
WORKDIR /app

RUN apt-get update && apt-get install -y gcc g++ make libffi-dev python3-dev && rm -rf /var/lib/apt/lists/*

RUN pip install greenlet==0.4.15 && \
    pip install flask gunicorn==19.9.0 gunicorn[gevent]

COPY ./server /app/server

WORKDIR /app/server
#  gevent worker (required for keep-alive)
CMD ["gunicorn", "--keep-alive", "10", "-k", "gevent", "--bind", "0.0.0.0:5001", "-w", "4", "server:app"]