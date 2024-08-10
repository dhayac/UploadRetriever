FROM ubuntu:22.04
COPY . /opt
WORKDIR /opt
RUN apt-get update && apt-get install -y python3-pip python3-venv -y --no-install-recommends
RUN python3 -m venv /opt/venv
RUN --mount=type=cache,target=/root/.cache pip install -r requirements.txt
RUN pip install "uvicorn[standard]" gunicorn
ENV PATH="/opt/venv/bin:$PATH"
ENV MONGO_URI=mongodb://localhost:27017/
RUN pip install --upgrade pip
RUN pip install status


