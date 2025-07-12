# Use Python base image
FROM python:3.10

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set working directory
WORKDIR /app

# Copy files
COPY . /app

# System dependencies (optional but good for numpy performance)
RUN apt-get update && apt-get install -y build-essential

# Upgrade pip and install numpy first
RUN pip install --upgrade pip


# Now install rest of dependencies
RUN pip install -r requirements.txt

# Force model download & cache
RUN python -c "from transformers import pipeline; pipeline('sentiment-analysis', model='distilbert-base-uncased-finetuned-sst-2-english', framework='pt')"

# Expose port (Railway uses $PORT)
EXPOSE 8080

# Start with gunicorn
CMD ["gunicorn", "app:app", "-b", "0.0.0.0:8080", "--workers", "4", "--threads", "2", "--timeout", "600"]
