FROM python:3.7-alpine
LABEL athor=hm.hassanmehmood@gmail.com
WORKDIR /app
COPY . .
RUN pwd
RUN /bin/sh -c python3 -m venv venv3
RUN . venv3/bin/activate
RUN pip install -r requirements.txt
RUN . set_env.env
RUN flask db_create
RUN flask db_seed
CMD flask run --reload --host=0.0.0.0 --port=5000