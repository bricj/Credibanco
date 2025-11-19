# FROM python:3.11-slim

# WORKDIR /app

# # Instalar dependencias del sistema necesarias
# RUN apt-get update && apt-get install -y \
#     gcc \
#     curl \
#     && rm -rf /var/lib/apt/lists/*

# # Crear usuario no-root para seguridad
# RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app

# # Copiar requirements y instalar dependencias Python
# COPY requirements.txt .
# RUN pip install --no-cache-dir -r requirements.txt

# # Copiar código fuente y scripts
# COPY src/ ./src/
# COPY scripts/ ./scripts/
# COPY .env .

# # Crear directorio para datos y asignar permisos
# RUN mkdir -p /app/data && chown -R appuser:appuser /app

# # Cambiar a usuario no-root
# USER appuser

# # Health check
# #HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
# #    CMD curl -f http://localhost:8000/health || exit 1

# # Exponer puerto
# #EXPOSE 8000
# EXPOSE 8080

# # Comando por defecto (será sobrescrito por docker-compose)
# #CMD ["uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
# CMD ["uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8080"]

##############################################################################################################

# # Versión Agente SQL
# FROM python:3.11-slim

# WORKDIR /app

# # Instalar dependencias del sistema necesarias
# RUN apt-get update && apt-get install -y \
#     gcc \
#     curl \
#     && rm -rf /var/lib/apt/lists/*

# # Crear usuario no-root para seguridad
# RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app

# # Copiar requirements y instalar dependencias Python
# COPY requirements.txt .
# RUN pip install --no-cache-dir -r requirements.txt

# # Copiar código fuente y scripts
# COPY src/ ./src/
# COPY scripts/ ./scripts/
# COPY .env .

# # 🆕 AGREGAR: Copiar datos directamente en la imagen
# COPY data/ ./data/

# # Crear directorio para datos y asignar permisos
# RUN chown -R appuser:appuser /app

# # Cambiar a usuario no-root
# USER appuser

# # Exponer puerto
# EXPOSE 8080

# # Comando por defecto
# CMD ["uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8080"]

##################################################################################################

# Version Agente SQL + RAG

FROM python:3.11-slim

WORKDIR /app

# Instalar dependencias del sistema necesarias
RUN apt-get update && apt-get install -y \
    gcc \
    curl \
    tesseract-ocr \
    tesseract-ocr-spa \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Crear usuario no-root para seguridad
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app

# Copiar requirements y instalar dependencias Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código fuente y scripts
COPY src/ ./src/
COPY scripts/ ./scripts/
COPY .env .

# 🆕 AGREGAR: Copiar datos directamente en la imagen
COPY data/ ./data/

# Crear directorio para datos y asignar permisos
RUN chown -R appuser:appuser /app

# Cambiar a usuario no-root
USER appuser

# Exponer puerto
EXPOSE 8080

# Comando por defecto
CMD ["uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8080"]
