FROM alpine AS fonts-download
# get the pre-converted fonts
RUN wget "https://drive.usercontent.google.com/download?id=1_BmJ1afnSt1rR_YAWhUCFDch8Bat78ti&export=download&authuser=0" -O fonts.zip
RUN unzip -d /fonts -j fonts.zip

FROM python:3.9-slim AS compile-image

# get fonts from the specified platform image
COPY --from=fonts-download /fonts /fonts

# Add git for hooks
RUN apt-get update && apt-get install -y --no-install-recommends python3-icu git

# get pip tools for computing requirements, and compile them
RUN python -m pip install pip-tools

# Set the working directory in the container (creating it in the process)
WORKDIR /app

# compile our requirements and then install them
COPY requirements.in .
RUN pip-compile --no-emit-index-url requirements.in && \
    pip install -r requirements.txt

# Copy the local directory contents into the container at /app
COPY . .

# install the application
RUN python setup.py develop

ENTRYPOINT ["/usr/local/bin/dominion_dividers"]
CMD ["--help"]
