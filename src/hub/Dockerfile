FROM registry.fedoraproject.org/fedora-minimal

RUN microdnf update -y && \
    microdnf install -y \
        python3-pip \
        python3.11 \
        python3.11-devel

COPY requirements.txt /tmp/requirements.txt 
# RUN pip install -r /tmp/requirements.txt
RUN python3.11 -m venv /venv
RUN /venv/bin/pip install -r /tmp/requirements.txt

WORKDIR /app
COPY entrypoint.sh /app/entrypoint.sh
#COPY app.py /app/app.py
#COPY settings.py /app/settings.py
#COPY pulp_client.py /app/pulp_client.py
#COPY collection_utils.py /app/collection_utils.py
#COPY tasks.py /app/tasks.py
COPY *.py /app/.

EXPOSE 80

CMD ["./entrypoint.sh"]
