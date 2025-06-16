#!/usr/bin/env python3
import uvicorn
import os
import sys

# Agregar src al path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

if __name__ == "__main__":
    uvicorn.run(
        "src.api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )

# # Instalar dependencias
# pip install -r requirements.txt

# # Configurar variables de entorno
# cp .env.example .env
# # Editar .env con tus credenciales

# # Ejecutar servidor
# python run.py

# # O con uvicorn directamente
# uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000
