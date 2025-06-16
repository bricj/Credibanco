#!/bin/bash

# ========================================
# Configuración - CAMBIAR ESTE VALOR
# ========================================
PROJECT_ID="credibancoagent"        # 🔧 CAMBIAR por tu Project ID
SERVICE_NAME="agent-teams"
REGION="us-central1"

echo "🚀 Deployment simple (datos incluidos en imagen)"
echo "📍 Project: $PROJECT_ID"
echo ""

# Verificar que tienes datos locales
if [ ! -d "data" ]; then
    echo "❌ Error: No existe carpeta 'data/'"
    echo "💡 Asegúrate de estar en la raíz del proyecto"
    exit 1
fi

if [ -z "$(ls -A data/)" ]; then
    echo "❌ Error: La carpeta 'data/' está vacía"
    exit 1
fi

echo "📁 Datos que se incluirán en la imagen:"
ls -la data/

# Configurar proyecto
echo "🔧 Configurando proyecto..."
gcloud config set project $PROJECT_ID

# Habilitar APIs necesarias
echo "🔧 Habilitando APIs..."
gcloud services enable cloudbuild.googleapis.com >/dev/null 2>&1
gcloud services enable run.googleapis.com >/dev/null 2>&1

# Build de imagen (incluye datos automáticamente por el COPY)
echo ""
echo "🏗️  Construyendo imagen con datos incluidos..."
echo "⏳ Esto puede tomar unos minutos..."

gcloud builds submit --tag "gcr.io/$PROJECT_ID/$SERVICE_NAME"

if [ $? -ne 0 ]; then
    echo "❌ Error en build de imagen"
    exit 1
fi

echo "✅ Imagen construida exitosamente"

# Deploy a Cloud Run
echo ""
echo "☁️  Desplegando en Cloud Run..."

gcloud run deploy $SERVICE_NAME \
    --image "gcr.io/$PROJECT_ID/$SERVICE_NAME" \
    --platform managed \
    --region $REGION \
    --allow-unauthenticated \
    --memory=2Gi \
    --cpu=1 \
    --port=8080 \
    --timeout=300 \
    --quiet

if [ $? -eq 0 ]; then
    echo ""
    echo "🎉 ¡Deployment completado exitosamente!"
    echo ""
    echo "📊 Resumen:"
    echo "   🐳 Imagen: gcr.io/$PROJECT_ID/$SERVICE_NAME"
    echo "   📁 Datos: Incluidos en la imagen"
    echo "   ☁️  Servicio: $SERVICE_NAME"
    echo ""
    echo "🌐 Tu aplicación está disponible en:"
    gcloud run services describe $SERVICE_NAME --region=$REGION --format='value(status.url)'
    echo ""
    echo "📋 Para ver logs en tiempo real:"
    echo "   gcloud logs tail --service=$SERVICE_NAME"
    echo ""
    echo "🔄 Para actualizar datos:"
    echo "   1. Modifica archivos en ./data/"
    echo "   2. Ejecuta de nuevo: ./deploy_simple.sh"
else
    echo "❌ Error en deployment a Cloud Run"
    exit 1
fi