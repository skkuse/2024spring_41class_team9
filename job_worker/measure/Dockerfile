# Start from a Java 11 base image that includes the JDK
FROM openjdk:11-jdk

# Install Python 3.10
RUN apt-get update && apt-get install -y python3.10 python3-pip

# Clean up APT when done.
RUN apt-get clean && rm -rf /var/lib/apt/lists/*

# Set JAVA_HOME environment variable
ENV JAVA_HOME /usr/lib/jvm/java-11-openjdk-amd64

# Set the working directory for the application
WORKDIR /app

# Copy the local code to the container
COPY . .

# Install any needed packages specified in requirements.txt
RUN pip3 install --no-cache-dir -r requirements.txt

# Run the Python application
CMD ["python3", "measure_worker.py"]
