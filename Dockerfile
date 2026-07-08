FROM python:3.12-slim

RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-por \
    pandoc \
    poppler-utils \
    texlive-xetex \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY . .

RUN pip install uv && uv sync --no-dev

EXPOSE 8501

CMD ["uv", "run", "streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]