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
    apt-get install -y --no-install-recommends python3-icu git && \
    apt-get clean  && \
    rm -rf /var/lib/apt/lists/*

# pip-tools installation
RUN python -m pip install pip-tools

WORKDIR /app

# Copy the requirements file first, to cache the requirements layer as well.
COPY requirements.in .

# Now compile and install dependencies in a single layer
RUN pip-compile --no-emit-index-url requirements.in \
    && pip install -r requirements.txt \
    && rm -rf ~/.cache/pip

# Copy the rest of your application code. This step is done later as this part changes more often.
COPY . .

# installation using setup.py
RUN python setup.py develop

ENTRYPOINT ["/usr/local/bin/dominion_dividers"]
CMD ["--help"]
