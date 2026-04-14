FROM python:3.10-slim AS compile-image

# Add git for hooks
RUN apt-get update && apt-get install -y --no-install-recommends python3-icu git

COPY --from=ghcr.io/astral-sh/uv:0.7.2 /uv /uvx /bin/

# Set the working directory in the container (creating it in the process)
WORKDIR /app

# Copy the local directory contents into the container at /app
COPY . .

# install the application
RUN uv pip install --system .

ENTRYPOINT ["/usr/local/bin/dominion_dividers"]
