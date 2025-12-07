FROM python:3.12-slim

WORKDIR /app

# Install uv (fast Python package manager used by project)
RUN pip install uv

# Copy project files
COPY pyproject.toml uv.lock README.md ./
COPY src/ ./src/

# Install the project
RUN uv sync --frozen

# Expose the server port
EXPOSE 8000

# Run the server (use 0.0.0.0 to be accessible outside container)
CMD ["uv", "run", "micromouse", "server", "start", "--host", "0.0.0.0", "--ctf", "tempflag", "--size", "32"]
