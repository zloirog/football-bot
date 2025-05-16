FROM python:3.10.5-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    sqlite3 \
    && rm -rf /var/lib/apt/lists/*

# Copy Pipfile and Pipfile.lock
COPY Pipfile Pipfile.lock ./

# Install pipenv and dependencies
RUN pip install pipenv && \
    pipenv install --system --deploy

# Copy the rest of the application
COPY . .

# Create necessary directories
RUN mkdir -p /app/data

# Create the database and run migrations
ENV DATABASE_PATH=/app/data/football.db
RUN sqlite3 $DATABASE_PATH < migrations/create_db.sql && \
    sqlite3 $DATABASE_PATH < migrations/change_chat_ids.sql && \
    sqlite3 $DATABASE_PATH < migrations/alter_users.sql && \
    sqlite3 $DATABASE_PATH < migrations/add_pidor.sql

# Expose port (if needed for health checks)
EXPOSE 8080

# Run the bot
CMD ["python", "main.py"]