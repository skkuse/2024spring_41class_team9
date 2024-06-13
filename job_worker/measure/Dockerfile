FROM openjdk:11-jdk

RUN apt-get update && \
    apt-get install -y python3.10 python3-pip && \
    pip3 install --upgrade pip && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY . .

RUN pip3 install --no-cache-dir -r requirements.txt

CMD ["python3", "measure_worker.py"]
