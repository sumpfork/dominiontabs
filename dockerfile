FROM python:3.9-slim AS compile-image

# Add git for hooks
RUN apt-get update && apt-get install -y --no-install-recommends python3-icu git

# Set the working directory in the container (creating it in the process)
WORKDIR /app

# Copy the local directory contents into the container at /app
COPY . .

# install the application
RUN pip install . && rm -rf ~/.cache/pip

ENTRYPOINT ["/usr/local/bin/dominion_dividers"]
