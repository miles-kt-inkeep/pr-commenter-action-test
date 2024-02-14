FROM python:3.7.5-slim

RUN pip install PyGithub
RUN pip install requests
COPY entrypoint.py /entrypoint.py

ENTRYPOINT python /entrypoint.py