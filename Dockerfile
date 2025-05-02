# Use Python base image
FROM python:3.11-slim

# Set work directory
WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY main.py .
COPY credentials.json .

# Environment variables (can also be passed at runtime)
ENV GOOGLE_SHEET_ID=your_google_sheet_id
ENV WORKSHEET_NAME="listings to submit"
ENV CREDENTIALS_FILE=credentials.json

# Run the script
CMD ["python", "main.py"]
