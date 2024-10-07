# Step 1: Use the official Python 3.12.4 image
FROM python:3.12.4-slim

# Set the working directory inside the container
WORKDIR /app

# Install required dependencies and libraries
RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxrender1 \
    libxext6 \
    libzbar0 \
    poppler-utils \
    && rm -rf /var/lib/apt/lists/*

# Step 3: Copy the necessary files into the container
# Copy individual files into the /app/ directory
COPY main.py requirements.txt artifact.py contract.py deploy_config.py /app/

# Copy the entire /templates directory into /app/
COPY templates /app/templates

# Copy the Poppler folder into the container at /app/Poppler
COPY Poppler /app/Poppler

# Step 4: Create a virtual environment named .venv
RUN python -m venv .venv

# Step 5: Install dependencies from requirements.txt into the .venv environment
RUN ./.venv/bin/pip install --upgrade pip
RUN ./.venv/bin/pip install -r requirements.txt

# Step 6: Set environment variables (for virtual environment and Poppler PATH)
ENV VIRTUAL_ENV=/app/.venv
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

# Add Poppler/Library/bin to the PATH environment variable
ENV PATH="/app/Poppler/Library/bin:$PATH"

# Expose the Flask app port
EXPOSE 4444

# Step 7: Run the main.py file with the virtual environment activated
CMD ["/app/.venv/bin/python", "main.py"]
