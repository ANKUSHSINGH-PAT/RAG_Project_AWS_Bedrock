FROM python:3.10-slim

WORKDIR /app

# Copy entire project
COPY . /app/

RUN pip install -r requirements.txt

RUN python -m nltk.downloader stopwords wordnet

EXPOSE 8501

CMD ["streamlit", "run", "rag_app.py", "--server.port=8501", "--server.address=0.0.0.0"]