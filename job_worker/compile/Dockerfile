# Start from a Java 11 base image that includes the JDK
FROM openjdk:11-jdk

# Install Python 3.10
RUN apt-get update && \
    apt-get install -y python3.10 python3-pip && \
    wget https://services.gradle.org/distributions/gradle-8.8-bin.zip -P /tmp && \
    unzip -d /opt/gradle /tmp/gradle-8.8-bin.zip && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/* && \
    pip3 install --upgrade pip

ENV PATH $PATH:/opt/gradle/gradle-8.8/bin

# Set the working directory for the application
WORKDIR /app

# Copy the local code to the container
COPY . .

# Install any needed packages specified in requirements.txt
RUN pip3 install --no-cache-dir -r requirements.txt

# Run the Python application
CMD ["python3", "compile_worker.py"]
