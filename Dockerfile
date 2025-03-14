# First Stage: Build Dependencies
FROM python:3.9 AS builder

WORKDIR /coffeeCam

# Install required system dependencies
RUN apt-get update && apt-get install -y ffmpeg libsm6 libxext6

# Copy the application source code
COPY . .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade -r requirements.txt

# Second Stage: Production Image (Alpine-based)
FROM python:3.9-alpine AS final

WORKDIR /coffeeCam

# Install only required Alpine system dependencies
RUN apk add --no-cache ffmpeg libxext libsm

# Copy necessary files from the builder stage
COPY --from=builder /coffeeCam /coffeeCam

# Set default command
CMD ["python", "main.py"]
