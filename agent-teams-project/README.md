
# Desarrollo Agente Credibanco

A continuación se presenta el desarrollo del agente en bootcamp: ciencia de datos para la entidad Credibanco.

## 📁 Estructura del Proyecto

```
agent-teams-project/
├── data/                           # Datos y bases de datos
│   ├── company_data.db            # Base de datos SQLite con información de la empresa
│   └── creditcard.csv             # Datos de tarjetas de crédito
│
├── scripts/                       # Scripts de inicialización y utilidades
│   └── init_database.py          # Script para inicializar la base de datos
│
├── src/                           # Código fuente principal
│   ├── agent/                     # Módulos del agente principal
│   │   ├── __pycache__/          # Cache de Python
│   │   ├── __init__.py           # Inicialización del módulo
│   │   ├── core_extended.py      # Funcionalidades extendidas del core
│   │   ├── core.py               # Lógica central del agente
│   │   ├── memory.py             # Sistema de memoria del agente
│   │   └── tools.py              # Herramientas y utilidades del agente
│   │
│   ├── api/                       # API REST y handlers
│   │   ├── __pycache__/          # Cache de Python
│   │   ├── __init__.py           # Inicialización del módulo API
│   │   ├── main.py               # Aplicación principal FastAPI
│   │   ├── teams_handler.py      # Manejador de equipos
│   │   └── telegram_handler.py   # Integración con Telegram
│   │
│   └── config/                    # Configuraciones del sistema
│       ├── __pycache__/          # Cache de Python
│       ├── __init__.py           # Inicialización de configuración
│       └── settings.py           # Configuraciones y variables de entorno
│
├── .env                          # Variables de entorno (NO incluir en Git)
├── cloudbuild.yaml              # Configuración para Google Cloud Build
├── deploy_simple.sh             # Script de despliegue simple
├── docker-compose.yml           # Configuración Docker Compose
├── Dockerfile                   # Imagen Docker del proyecto
├── README.md                    # Documentación del proyecto
├── requirements.txt             # Dependencias de Python
├── run.py                       # Script principal de ejecución
└── telegram_bot.py              # Bot de Telegram independiente
```

## 🚀 Características Principales

Agentes Inteligentes: Sistema de agentes basado en LangChain/LangGraph

API REST: Interfaz HTTP para interactuar disponibilizar la información consumida por el agente

Integración Telegram: Bot de Telegram para interacciones

Base de Datos: Almacenamiento persistente con SQL

Sistema de Memoria: Memoria persistente para los agentes

Dockerización: Contenedores Docker para fácil despliegue

### Descripción de módulos

agent (src/agent/)

core.py: Lógica principal del agente

core_extended.py: Funcionalidades avanzadas

memory.py: Sistema de memoria persistente

tools.py: Herramientas disponibles para el agente

api (src/api/)

main.py: Aplicación FastAPI principal

teams_handler.py: Lógica de manejo de equipos

telegram_handler.py: Integración con Telegram

Configuración (src/config/)

settings.py: Configuraciones centralizadas del sistema


## 📋 Prerrequisitos

Python 3.8+
Docker y Docker Compose
Cuenta de Telegram (para el bot)
Variables de entorno configuradas

## ⚙️ Instalación y Configuración

1. Clonar el Repositorio

bash 

git clone <repository-url>

cd agent-teams-project

2. Configurar Variables de Entorno

bash

touch .env
#### Editar .env con tus configuraciones

DATABASE_URL=sqlite:///./data/company_data.db

#### Credenciales Google
GOOGLE_API_KEY="GOOGLE API KEY"
LLM_MODEL=gemini-1.5-flash
GCP_PROJECT_ID=NOMBRE PROYECTO GCP
GCP_REGION=us-central1 

1. Se debe crear un nuevo proyecto en GCP, allí se puede obtener el id del proyecto

2. EL API Key de Google se obtiene en AI Studio


#### Telegram Bot - REEMPLAZAR CON TU TOKEN REAL
TELEGRAM_BOT_TOKEN=TOKEN TELEGRAM

Para generar el token de Telegram se deben seguir los siguientes pasos:

1. Entrar a Telegram

2. Abrir @botfather

3. Iniciar conversación

4. /newbot

5. Indicar nombre del asistente: EJ -> Analysis Assistant

6. Escribir el nombre del bot: EJ -> analysis_assistant_bot

7. Ejemplo token: 7309587597:AAF3bdnAWLPVmQ6mr0gYFdn5LQZJE40S6Hs(111)


3. 🐳 Despliegue con Docker

### Desarrollo Local

bash# Construir y ejecutar con Docker Compose

docker-compose up --build

bash# En otra terminal ejecutar

python telegram_bot.py

### Despliegue Simple

#### Instalar gcloud

##### Instalador

Descargar desde: https://cloud.google.com/sdk/docs/install

Ejecutar el archivo .msi

Seguir el asistente de instalación

Reiniciar Command Prompt o PowerShell

##### Inicializar configuración
gcloud init

##### Autenticarse
gcloud auth login

##### Verificar instalación
gcloud version

##### Ver configuración actual
gcloud config list

##### Establecer proyecto por defecto
gcloud config set project TU_PROJECT_ID

##### Establecer región por defecto
gcloud config set compute/region us-central1
gcloud config set compute/zone us-central1-a


#### Establecer Proyecto

* Verificar proyectos disponibles:

gcloud projects list

* Cambiar al proyecto correcto:

gcloud config set project credibancoagent (Indicar nombre del proyecto en vez de "credibancoagent")

* Verificar que cambió:

gcloud config get-value project

##### Debería mostrar: credibancoagent

#### Habilitar Permisos

* Habilitar APIs en el proyecto correcto:

gcloud services enable cloudbuild.googleapis.com

gcloud services enable run.googleapis.com

gcloud services enable aiplatform.googleapis.com


#### Verificación autenticación

*  Verificar autenticación si falla:

# Ver cuenta actual
gcloud auth list

# Re-autenticarse si es necesario
gcloud auth login

# Verificar permisos en el proyecto
gcloud projects get-iam-policy credibancoagent

* Importante, por ahora, no se ha definido el CI/CD, por ello, se requiere desplegar la imagen cada cambio.


#### Despliegue

Se debe garantizar que las credenciales están actualizadas en el archivo cloud_build.yaml

bash# Usar el script de despliegue

./deploy_simple.sh

Construcción Manual

bash# Construir imagen

docker build -t agent-teams .


#### Base de Datos
DATABASE_URL=sqlite:///data/company_data.db


## 🚀 Despliegue en Google Cloud
El proyecto incluye cloudbuild.yaml para despliegue automático en Google Cloud Platform.

📝 Logs y Debugging

Los logs se pueden revisar usando:

bash# Docker Compose

docker-compose logs -f

#### Contenedor específico
docker logs <container_name>

📄 Licencia
Este proyecto está bajo la Licencia [MIT/Apache/etc] - ver el archivo LICENSE para detalles.