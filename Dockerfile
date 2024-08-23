# Use python as the base image
FROM python:3.11

# Set the working directory
WORKDIR /app

# Copy the application code into the container
COPY . /app

# ensure poetry is installed
RUN pip install poetry

# Install any dependencies
RUN poetry lock
RUN poetry install

# Start the Temporal worker
CMD ["poetry", "run", "bitbot"]