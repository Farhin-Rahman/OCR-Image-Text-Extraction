# ---- Stage 1: Build Stage ----
# Use a specific slim Python image for reproducibility
FROM python:3.9-slim-bullseye as builder

# Set the working directory
WORKDIR /usr/src/app

# Copy requirements and install packages into a "wheels" directory
# This layer is cached as long as requirements.txt doesn't change, speeding up future builds
COPY requirements.txt ./
RUN pip wheel --no-cache-dir --wheel-dir /usr/src/app/wheels -r requirements.txt


# ---- Stage 2: Final Stage ----
# Use the same base image for the final, lean container
FROM python:3.9-slim-bullseye

# Set a new working directory
WORKDIR /app

# Install Tesseract OCR and remove the package manager cache to keep the image small
# --no-install-recommends avoids installing extra, unnecessary packages
RUN apt-get update && \
    apt-get install -y tesseract-ocr --no-install-recommends && \
    rm -rf /var/lib/apt/lists/*

# Copy the pre-built Python packages from the builder stage
COPY --from=builder /usr/src/app/wheels /wheels
# Install the packages from the local wheels, which is fast and requires no network
RUN pip install --no-cache /wheels/*

# Copy only the application code into the final image
COPY ./app ./app

# Create a non-root user for security best practices
RUN useradd --create-home appuser
USER appuser

# Expose the port that Cloud Run will listen on
EXPOSE 8080

# The command to run the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]