FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy MCP server code
COPY . .

# Set environment variables
ENV PYTHONPATH=/app
ENV DB_HOST=dev-postgres-db
ENV DB_PORT=5432
ENV DB_NAME=postgres
ENV DB_USER=postgres
ENV DB_PASSWORD=postgres

# Run MCP server
CMD ["python", "-m", "mcp_server.server"]
