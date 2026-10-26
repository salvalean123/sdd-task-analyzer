# Imagem do TaskAnalyzer (Fase 3): ambiente isolado e imutável para o Test Harness.
FROM python:3.11-slim

# Sem arquivos .pyc e com saída do Python sem buffer (logs aparecem na hora).
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Dependências primeiro, para aproveitar o cache de camadas do Docker.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Código, testes e artefatos de governança.
COPY . .

# Usuário sem privilégios de root.
RUN useradd --create-home appuser && chown -R appuser /app
USER appuser

# Comando de entrada principal: executa a suíte de testes.
CMD ["pytest", "tests/test_harness.py", "-v"]
