FROM alpine AS fonts-download
# get the fonts from Google Drive
RUN wget "https://drive.usercontent.google.com/download?id=1_BmJ1afnSt1rR_YAWhUCFDch8Bat78ti&export=download&authuser=0" -O fonts.zip
RUN unzip -d /fonts -j fonts.zip

# Switch to using python:3.9-slim as the base image for the application.
FROM python:3.9-slim AS compile-image

# Copying fonts first as this is less likely to change than source code,
# optimizing use of Docker's cache when rebuilding images.
COPY --from=fonts-download /fonts /fonts

# Combine apt-get update, software installation, and cleanup into a single RUN to reduce layers.
# Additionally, we remove the cache files to keep the image size down.
RUN apt-get update && \
    apt-get install -y --no-install-recommends git && \
    apt-get clean  && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy the rest of application code.
COPY . .

# Compile and install dependencies
# then install the local package
RUN pip install -r requirements.txt \
    && pip install . \
    && rm -rf ~/.cache/pip

ENTRYPOINT ["/usr/local/bin/dominion_dividers"]
CMD ["--help"]
