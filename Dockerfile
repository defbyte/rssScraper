FROM python:3.10-slim

ENV PYTHONUNBUFFERED 1

# Put project files in to place
COPY . /app
WORKDIR /app

# folder to serve media files by nginx
RUN mkdir -p /vol/web/media
# folder to serve static files by nginx
RUN mkdir -p /vol/web/static

# Create virtualenv and install requirements
RUN python3 -m venv /opt/venv
RUN . /opt/venv/bin/activate
RUN /opt/venv/bin/pip install -r requirements.txt

RUN chmod +x entrypoint.sh

CMD [ "/app/entrypoint.sh" ]