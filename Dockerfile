FROM python:3.9-slim-buster

WORKDIR /rag_app

COPY . /rag_app

RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 8501

CMD ["streamlit", "run", "rag_app.py", "--server.port=8501", "--server.address=0.0.0.0"]
