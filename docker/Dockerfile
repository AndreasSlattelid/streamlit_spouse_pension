#FROM python:3.11.0rc2-windowsservercore-ltsc2022
#FROM python:3.10-windowsservercore-1809 
FROM python:3.10-slim

EXPOSE 8501 

WORKDIR /spouse_app

RUN apt-get update && apt-get install -y \
    build-essential \
    software-properties-common \
    git \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./requirements.txt
COPY Spouse_app.py ./Spouse_app.py
RUN pip install -r requirements.txt

ENTRYPOINT ["streamlit", "run", "Spouse_app.py", "--server.port=8501", "--server.address=0.0.0.0"]