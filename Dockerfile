# Use a lightweight version of Python
FROM python:3.12-slim

# Set the folder inside the container
WORKDIR /app

# Copy the requirements file first
COPY requirements.txt .

# Install dependencies (no cache to save space)
RUN pip install --no-cache-dir -r requirements.txt

# Copy all your code into the container
COPY . .

# Run the bot
CMD ["python", "main.py"]