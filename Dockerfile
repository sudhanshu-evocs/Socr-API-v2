# Use the official Python image from the Docker Hub
FROM python:3.12-slim

# Set the working directory in the container
WORKDIR /app

# Copy the source code to the container
COPY src /app/src

# Copy the test suite to the container
COPY test_suite /app/test_suite

# Copy the test documents to the container
COPY test_documents /app/test_documents

# Set environment variables (if needed)
ENV PYTHONPATH="/app/src"

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r src/requirements.txt

# Make port 5000 available to the world outside this container
EXPOSE 5000

# Run app.py when the container launches
CMD ["python", "src/docuverus/app.py"]
