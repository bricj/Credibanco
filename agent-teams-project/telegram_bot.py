#!/usr/bin/env python3
"""
Telegram Bot - Conexión simple con FastAPI
Archivo: telegram_bot.py
Versión corregida
"""

import requests
import time
import os
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Configuración
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
FASTAPI_URL = "http://localhost:8000"

class TelegramBot:
    def __init__(self, token):
        self.token = token
        self.api_url = f"https://api.telegram.org/bot{token}"
        self.offset = 0
        
    def get_updates(self):
        """Obtener mensajes nuevos de Telegram"""
        url = f"{self.api_url}/getUpdates"
        params = {
            "offset": self.offset,
            "timeout": 30  # Esperar hasta 30 segundos por nuevos mensajes
        }
        
        try:
            response = requests.get(url, params=params, timeout=35)
            if response.status_code == 200:
                return response.json().get("result", [])
            else:
                print(f"❌ Error obteniendo updates: {response.status_code}")
                return []
        except requests.exceptions.Timeout:
            return []  # Normal en polling, solo continuar
        except Exception as e:
            print(f"❌ Error en get_updates: {e}")
            return []
    
    def send_message(self, chat_id, text):
        """Enviar mensaje a Telegram"""
        url = f"{self.api_url}/sendMessage"
        
        # Dividir mensajes largos si es necesario
        if len(text) > 4000:
            chunks = [text[i:i+4000] for i in range(0, len(text), 4000)]
            for chunk in chunks:
                self._send_single_message(chat_id, chunk)
            return True
        else:
            return self._send_single_message(chat_id, text)
    
    def _send_single_message(self, chat_id, text):
        """Enviar un mensaje individual"""
        url = f"{self.api_url}/sendMessage"
        data = {
            "chat_id": chat_id,
            "text": text,
            "parse_mode": "Markdown"
        }
        
        try:
            response = requests.post(url, json=data, timeout=10)
            return response.status_code == 200
        except Exception as e:
            print(f"❌ Error enviando mensaje: {e}")
            return False
    
    def send_typing(self, chat_id):
        """Enviar indicador de 'escribiendo...'"""
        url = f"{self.api_url}/sendChatAction"
        data = {
            "chat_id": chat_id,
            "action": "typing"
        }
        
        try:
            requests.post(url, json=data, timeout=5)
        except:
            pass  # No es crítico si falla
    
    def call_sql_agent(self, message, user_id, chat_id):
        """Llamar al agente SQL via FastAPI"""
        # Enviar mensaje de procesando
        self.send_message(chat_id, "🔄 **Analizando datos...**\n\nEsto puede tomar 1-2 minutos. Por favor espera.")
        
        # Mostrar que está escribiendo
        self.send_typing(chat_id)
        
        url = f"{FASTAPI_URL}/api/sql-analysis"
        data = {
            "message": message,
            "user_id": str(user_id)
        }
        
        try:
            response = requests.post(url, json=data, timeout=60)  # 3 minutos
            
            if response.status_code == 200:
                result = response.json()
                if result.get("success"):
                    # Formatear respuesta exitosa
                    response_text = f"📊 **Análisis Completado**\n\n{result['response']}"
                    
                    # Agregar información adicional si está disponible
                    if result.get("database_result"):
                        response_text += f"\n\n💾 **Datos procesados exitosamente**"
                    
                    return response_text
                else:
                    return f"❌ **Error en análisis**\n\n{result.get('error', 'Error desconocido')}"
            else:
                return f"❌ **Error del servidor ({response.status_code})**\n\nIntenta nuevamente en unos momentos."
                
        except requests.exceptions.Timeout:
            return """⏱️ **Timeout - Análisis complejo**

El análisis está tomando más tiempo del esperado.

💡 **Sugerencias:**
• Intenta una consulta más específica
• Usa menos datos en el análisis
• Reformula la pregunta de manera más simple

🔄 **Ejemplo:** En lugar de "analizar todo", prueba "promedio de salarios por empresa" """

        except requests.exceptions.ConnectionError:
            return "❌ **Error de conexión**\n\nNo se puede conectar con el servidor. Verifica que FastAPI esté ejecutándose."
            
        except Exception as e:
            return f"❌ **Error inesperado**\n\n{str(e)}"
    
    def handle_command(self, command, first_name):
        """Manejar comandos especiales"""
        if command.startswith('/start'):
            return f"""🤖 **¡Hola {first_name}!** Soy tu Asistente de Análisis SQL

📊 **¿Qué puedo hacer?**
• Analizar bases de datos automáticamente
• Generar reportes ejecutivos  
• Crear consultas SQL inteligentes
• Proporcionar insights de datos

💡 **Ejemplos de consultas:**
• "Analiza los salarios por ubicación"
• "¿Cuáles son las tendencias por empresa?"
• "Genera un reporte de desarrolladores remotos"
• "Muéstrame estadísticas por experiencia"
• "Promedio de salarios por año de experiencia"

🚀 **¡Simplemente escribe tu pregunta!**

📝 **Comandos disponibles:**
/help - Mostrar ayuda detallada
/examples - Ver más ejemplos
/tables - Ver tablas disponibles
/status - Estado del sistema"""

        elif command.startswith('/help'):
            return """🆘 **Ayuda - Cómo usar el bot**

✨ **Usa lenguaje natural:**
• "¿Cuántos empleados remotos hay?"
• "Compara salarios entre ciudades"
• "Análisis de experiencia vs salario"
• "Top 10 empresas mejor pagadas"

🔍 **El sistema:**
1. Analiza tu pregunta en lenguaje natural
2. Genera consultas SQL automáticamente
3. Procesa los datos de la base de datos
4. Te proporciona insights detallados y recomendaciones

💡 **Tips para mejores resultados:**
• Sé específico en tus preguntas
• No necesitas conocer SQL
• Puedes pedir comparaciones y estadísticas
• Menciona columnas específicas si las conoces

⚡ **Comandos útiles:**
/tables - Ver qué datos están disponibles
/examples - Inspiración para consultas
/status - Verificar estado del sistema"""

        elif command.startswith('/examples'):
            return """📝 **Ejemplos de Consultas Avanzadas**

💰 **Análisis Salariales:**
• "Salario promedio por nivel de experiencia"
• "Top 10 empresas mejor pagadas"
• "Diferencia salarial trabajo remoto vs presencial"
• "Distribución de salarios por rango"

🏢 **Análisis por Empresa:**
• "Empresas con más ofertas remotas"
• "Compañías que requieren más experiencia"
• "Análisis de beneficios por empresa"

📍 **Análisis Geográfico:**
• "Mejores ciudades para developers"
• "Comparación de salarios por región"
• "Costo de vida vs salario por ubicación"

🎯 **Análisis por Rol:**
• "Perfiles más demandados en tech"
• "Skills más valoradas por posición"
• "Tendencias de crecimiento por rol"

📊 **Análisis Estadístico:**
• "Correlación entre experiencia y salario"
• "Mediana de salarios por sector"
• "Percentiles de compensación"

¡Prueba cualquiera de estos o crea tu propia consulta!"""

        elif command.startswith('/tables'):
            return """📋 **Consultando tablas disponibles...**

🔄 Un momento mientras obtengo la información de la base de datos."""

        elif command.startswith('/status'):
            return """🔍 **Estado del Sistema**

🔄 Verificando conexiones..."""

        else:
            return f"""❓ **Comando no reconocido:** `{command}`

📝 **Comandos disponibles:**
/help - Ayuda detallada
/examples - Ejemplos de consultas
/tables - Ver tablas disponibles
/status - Estado del sistema

💡 **Tip:** Para hacer consultas, simplemente escribe tu pregunta sin usar comandos."""
    
    def get_database_tables(self):
        """Obtener lista de tablas disponibles"""
        try:
            response = requests.get(f"{FASTAPI_URL}/api/database/tables", timeout=10)
            if response.status_code == 200:
                result = response.json()
                return f"📋 **Tablas disponibles:**\n\n{result.get('tables', 'No se encontraron tablas')}"
            else:
                return "❌ Error obteniendo lista de tablas"
        except Exception as e:
            return f"❌ Error: {str(e)}"
    
    def get_system_status(self):
        """Obtener estado del sistema"""
        try:
            response = requests.get(f"{FASTAPI_URL}/health", timeout=10)
            if response.status_code == 200:
                result = response.json()
                status_text = "✅ **Sistema funcionando correctamente**\n\n"
                
                if 'components' in result:
                    status_text += "**Componentes:**\n"
                    for component, status in result['components'].items():
                        status_emoji = "✅" if status == "active" or status == "ready" else "❌"
                        status_text += f"{status_emoji} {component}: {status}\n"
                
                if 'settings' in result:
                    status_text += "\n**Configuración:**\n"
                    for setting, configured in result['settings'].items():
                        config_emoji = "✅" if configured else "❌"
                        status_text += f"{config_emoji} {setting}\n"
                
                return status_text
            else:
                return f"⚠️ **Sistema con problemas**\n\nCódigo de respuesta: {response.status_code}"
        except Exception as e:
            return f"❌ **Sistema no disponible**\n\nError: {str(e)}"
    
    def start_polling(self):
        """Iniciar el bot"""
        print("🤖 Iniciando Telegram Bot...")
        print(f"📡 FastAPI: {FASTAPI_URL}")
        print("💬 Listo para recibir mensajes")
        print("🛑 Presiona Ctrl+C para detener\n")
        
        # Verificar FastAPI
        try:
            response = requests.get(f"{FASTAPI_URL}/health", timeout=5)
            if response.status_code == 200:
                print("✅ FastAPI conectado correctamente")
            else:
                print(f"⚠️ FastAPI responde con código: {response.status_code}")
        except:
            print("❌ No se puede conectar con FastAPI")
            print("   Ejecuta: docker-compose up")
            return
        
        # Ciclo principal
        while True:
            try:
                updates = self.get_updates()
                
                for update in updates:
                    self.offset = update["update_id"] + 1
                    
                    if "message" in update:
                        message = update["message"]
                        chat_id = message["chat"]["id"]
                        user_id = message["from"]["id"]
                        username = message["from"].get("username", "unknown")
                        first_name = message["from"].get("first_name", "Usuario")
                        text = message.get("text", "")
                        
                        if text:
                            print(f"\n📩 @{username}: {text}")
                            
                            # Procesar mensaje
                            if text.startswith('/'):
                                if text.startswith('/tables'):
                                    response = self.get_database_tables()
                                elif text.startswith('/status'):
                                    response = self.get_system_status()
                                else:
                                    response = self.handle_command(text, first_name)
                            else:
                                print("🔄 Procesando con agente SQL...")
                                response = self.call_sql_agent(text, user_id, chat_id)
                            
                            # Enviar respuesta
                            print("📤 Enviando respuesta...")
                            if self.send_message(chat_id, response):
                                print("✅ Mensaje enviado")
                            else:
                                print("❌ Error enviando mensaje")
                
                # Pequeña pausa para no sobrecargar
                time.sleep(0.1)
                
            except KeyboardInterrupt:
                print("\n🛑 Deteniendo bot...")
                break
            except Exception as e:
                print(f"❌ Error: {e}")
                time.sleep(5)

def main():
    # Verificar configuración
    if not BOT_TOKEN or BOT_TOKEN == "temp":
        print("❌ Error: TELEGRAM_BOT_TOKEN no configurado")
        print("\n📝 Pasos para configurar:")
        print("1. Busca @BotFather en Telegram")
        print("2. Envía /newbot")
        print("3. Sigue las instrucciones")
        print("4. Copia el token al archivo .env")
        print("5. Reinicia este script")
        return
    
    print(f"🔑 Token configurado: {BOT_TOKEN[:10]}...")
    
    # Iniciar bot
    bot = TelegramBot(BOT_TOKEN)
    bot.start_polling()

if __name__ == "__main__":
    main()