# bot/Dockerfile
FROM python:3.10-slim
WORKDIR /app

# Kopiujemy TYLKO plik z zależnościami z folderu bot
COPY bot/requirements.txt .
RUN pip install -r requirements.txt

# Kopiujemy zawartość folderu 'bot' do '/app'
COPY ./bot/. .

# ZMIANA: Wracamy do prostszego polecenia startowego, które działa z importami bezwzględnymi
CMD ["python", "main.py"]