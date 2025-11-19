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

### Cambios mejorados de la actualizacion

# #!/usr/bin/env python3
# """
# Telegram Bot - Conexión mejorada con FastAPI
# Archivo: telegram_bot.py
# Versión mejorada para OrchestratorSystem v2.0
# """

# import requests
# import time
# import os
# from dotenv import load_dotenv

# # Cargar variables de entorno
# load_dotenv()

# # Configuración
# BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
# FASTAPI_URL = "http://localhost:8000"

# class TelegramBot:
#     def __init__(self, token):
#         self.token = token
#         self.api_url = f"https://api.telegram.org/bot{token}"
#         self.offset = 0
        
#     def get_updates(self):
#         """Obtener mensajes nuevos de Telegram"""
#         url = f"{self.api_url}/getUpdates"
#         params = {
#             "offset": self.offset,
#             "timeout": 30  # Esperar hasta 30 segundos por nuevos mensajes
#         }
        
#         try:
#             response = requests.get(url, params=params, timeout=35)
#             if response.status_code == 200:
#                 return response.json().get("result", [])
#             else:
#                 print(f"❌ Error obteniendo updates: {response.status_code}")
#                 return []
#         except requests.exceptions.Timeout:
#             return []  # Normal en polling, solo continuar
#         except Exception as e:
#             print(f"❌ Error en get_updates: {e}")
#             return []
    
#     def send_message(self, chat_id, text):
#         """Enviar mensaje a Telegram"""
#         url = f"{self.api_url}/sendMessage"
        
#         # Dividir mensajes largos si es necesario
#         if len(text) > 4000:
#             chunks = [text[i:i+4000] for i in range(0, len(text), 4000)]
#             for chunk in chunks:
#                 self._send_single_message(chat_id, chunk)
#             return True
#         else:
#             return self._send_single_message(chat_id, text)
    
#     def _send_single_message(self, chat_id, text):
#         """Enviar un mensaje individual"""
#         url = f"{self.api_url}/sendMessage"
#         data = {
#             "chat_id": chat_id,
#             "text": text,
#             "parse_mode": "Markdown"
#         }
        
#         try:
#             response = requests.post(url, json=data, timeout=10)
#             return response.status_code == 200
#         except Exception as e:
#             print(f"❌ Error enviando mensaje: {e}")
#             return False
    
#     def send_typing(self, chat_id):
#         """Enviar indicador de 'escribiendo...'"""
#         url = f"{self.api_url}/sendChatAction"
#         data = {
#             "chat_id": chat_id,
#             "action": "typing"
#         }
        
#         try:
#             requests.post(url, json=data, timeout=5)
#         except:
#             pass  # No es crítico si falla
    
#     def call_sql_agent(self, message, user_id, chat_id):
#         """Llamar al agente SQL via FastAPI con mejoras del orchestrator"""
#         # Enviar mensaje de procesando con info del sistema
#         self.send_message(chat_id, "🔄 **Analizando con Sistema Multi-Agente v2.0...**\n\n🧠 Router clasificando consulta → Agente especializado\n\nEsto puede tomar 1-2 minutos. Por favor espera.")
        
#         # Mostrar que está escribiendo
#         self.send_typing(chat_id)
        
#         url = f"{FASTAPI_URL}/api/sql-analysis"
#         data = {
#             "message": message,
#             "user_id": str(user_id)
#         }
        
#         try:
#             response = requests.post(url, json=data, timeout=60)
            
#             if response.status_code == 200:
#                 result = response.json()
#                 if result.get("success"):
#                     return self._format_enhanced_response(result, message)
#                 else:
#                     return f"❌ **Error en análisis**\n\n{result.get('error', 'Error desconocido')}"
#             else:
#                 return f"❌ **Error del servidor ({response.status_code})**\n\nIntenta nuevamente en unos momentos."
                
#         except requests.exceptions.Timeout:
#             return """⏱️ **Timeout - Análisis complejo**

# El análisis está tomando más tiempo del esperado.

# 💡 **Sugerencias:**
# • Intenta una consulta más específica
# • Usa menos datos en el análisis  
# • Reformula la pregunta de manera más simple

# 🔄 **Ejemplos específicos:**
# • "Total transacciones por periodo"
# • "Análisis por franquicia"
# • "Comparar plataformas de pago" """

#         except requests.exceptions.ConnectionError:
#             return "❌ **Error de conexión**\n\nNo se puede conectar con el servidor. Verifica que FastAPI esté ejecutándose."
            
#         except Exception as e:
#             return f"❌ **Error inesperado**\n\n{str(e)}"
    
#     def _format_enhanced_response(self, result, original_query):
#         """Formatear respuesta con información del orchestrator"""
#         # Información del orchestrator
#         query_type = result.get('query_type', 'unknown')
#         confidence = result.get('confidence', 0.0)
#         intent = result.get('intent', 'unknown')
        
#         # Emojis y títulos según tipo
#         type_info = {
#             'sql': {'emoji': '📊', 'title': 'Análisis SQL', 'agent': 'SQL Agent'},
#             'rag': {'emoji': '📚', 'title': 'Consulta de Conocimiento', 'agent': 'RAG Agent'}, 
#             'hybrid': {'emoji': '🔄', 'title': 'Análisis Híbrido', 'agent': 'Multi-Agent'},
#             'error': {'emoji': '❌', 'title': 'Error', 'agent': 'Sistema'}
#         }
        
#         info = type_info.get(query_type, {'emoji': '🤖', 'title': 'Análisis', 'agent': 'Agente'})
        
#         # Construir respuesta
#         response_text = f"{info['emoji']} **{info['title']} Completado**\n\n"
#         response_text += f"{result['response']}\n\n"
        
#         # Información adicional del sistema
#         if result.get("database_result"):
#             response_text += "💾 **Estado:** Datos extraídos exitosamente de la base de datos\n"
        
#         if result.get("detailed_analysis"):
#             response_text += "📈 **Análisis detallado:** Disponible en el reporte\n"
        
#         # Información del orchestrator
#         response_text += f"🎯 **Tipo:** {query_type.upper()}\n"
#         response_text += f"🤖 **Procesado por:** {info['agent']}\n"
        
#         # Información de confianza con emojis
#         if confidence > 0.8:
#             response_text += f"✨ **Confianza:** Alta ({confidence:.1%})\n"
#         elif confidence > 0.6:
#             response_text += f"⚡ **Confianza:** Buena ({confidence:.1%})\n"
#         elif confidence > 0.4:
#             response_text += f"🔶 **Confianza:** Media ({confidence:.1%})\n"
#         elif confidence > 0.0:
#             response_text += f"🔸 **Confianza:** Baja ({confidence:.1%}) - Clasificación por defecto\n"
        
#         # Footer técnico
#         response_text += "\n" + "─" * 30 + "\n"
#         response_text += f"🧠 *Sistema Multi-Agente v2.0*\n"
        
#         # Footer específico por tipo
#         if query_type == 'sql':
#             response_text += "🔄 *Router → SQL Agent → Análisis → Reporte*"
#         elif query_type == 'rag':
#             response_text += "🔄 *Router → RAG Agent → Conocimiento → Respuesta*"
#         elif query_type == 'hybrid':
#             response_text += "🔄 *Router → Multi-Agent → Synthesis → Reporte*"
#         else:
#             response_text += "🔄 *Sistema de orquestación inteligente*"
        
#         return response_text
    
#     def handle_command(self, command, first_name):
#         """Manejar comandos especiales mejorados para v2.0"""
#         if command.startswith('/start'):
#             return f"""🤖 **¡Hola {first_name}!** Soy tu Asistente SQL Inteligente v2.0

# 🧠 **Sistema de Orquestación Multi-Agente:**
# • **Router Agent**: Clasifica tu consulta automáticamente
# • **SQL Agent**: Especialista en análisis de datos transaccionales
# • **RAG Agent**: Sistema de conocimiento (próximamente)
# • **Orchestrator**: Coordina todo el proceso inteligentemente

# 📊 **¿Qué puedo hacer?**
# • Analizar transacciones automáticamente
# • Generar reportes por periodo/franquicia/plataforma
# • Consultas SQL inteligentes en lenguaje natural
# • Insights de datos transaccionales especializados

# 💡 **Ejemplos específicos para datos transaccionales:**
# • "¿Cuál es el total de transacciones por periodo?"
# • "Análisis de transacciones por franquicia de tarjetas"
# • "Comparar rendimiento por plataforma de pago"
# • "Estadísticas por establecimiento y entidad emisora"
# • "Tendencias de transacciones por pasarela"

# 🚀 **¡El sistema clasifica tu consulta automáticamente y la dirige al agente especializado!**

# 📝 **Comandos disponibles:**
# /help - Ayuda detallada del sistema
# /system - Información de la arquitectura v2.0
# /examples - Ejemplos específicos de consultas
# /tables - Ver tablas y datos disponibles
# /status - Estado completo del sistema"""

#         elif command.startswith('/help'):
#             return """🆘 **Ayuda - Sistema Multi-Agente v2.0**

# 🧠 **Cómo funciona la clasificación inteligente:**
# 1. **Tu consulta** → Router Agent (análisis automático)
# 2. **Clasificación** → SQL/RAG/Híbrido (con nivel de confianza)
# 3. **Routing** → Agente especializado correspondiente
# 4. **Procesamiento** → Análisis específico del dominio
# 5. **Respuesta** → Resultado formateado y contextualizado

# 📋 **Tipos de consultas que proceso:**

# 🔢 **Consultas SQL (Datos Transaccionales):**
# • Total de transacciones por periodo/franquicia/plataforma
# • Análisis comparativos entre entidades
# • Estadísticas por establecimiento
# • Tendencias temporales y reportes ejecutivos

# 📚 **Consultas RAG (Conocimiento - Próximamente):**
# • Explicaciones de conceptos financieros
# • Documentación de procesos de pago
# • Definiciones técnicas del sector

# 💬 **Ejemplos prácticos específicos:**
# • "Total transacciones Visa vs Mastercard en diciembre"
# • "Establecimientos con mayor volumen por plataforma"
# • "Análisis temporal de transacciones por entidad emisora"
# • "Comparación de pasarelas de pago por rendimiento"

# ⚡ **Tips para mejores resultados:**
# • Usa lenguaje natural y específico
# • Menciona periodos, franquicias o plataformas
# • El sistema detecta automáticamente el tipo de consulta
# • No necesitas conocer SQL - habla como si fuera una conversación

# 🎯 **El router clasificará tu consulta y la dirigirá automáticamente al agente especializado más apropiado**"""

#         elif command.startswith('/system'):
#             return """🔧 **Sistema Multi-Agente v2.0 - Arquitectura**

# 🧠 **Componentes Principales:**

# **🎯 Router Agent:**
# • Clasifica consultas automáticamente
# • Análisis de keywords + confianza semántica
# • Threshold: 0.5 para decisiones
# • Fallback: SQL Agent para datos transaccionales

# **📊 SQL Agent:**
# • Especialista en datos transaccionales
# • Base de datos SQLite optimizada
# • Herramientas: list_tables, schema_analysis, execute_sql
# • Contexto: Conoce estructura completa de datos

# **📚 RAG Agent (En desarrollo):**
# • Sistema de conocimiento externo
# • Documentación y procedimientos
# • Base vectorial con Pinecone
# • Respuestas contextualizadas

# **🤖 Orchestrator:**
# • Coordinador principal del sistema
# • Pipeline LangGraph con estados
# • Memoria conversacional por usuario
# • Logging completo para debugging

# 🎯 **Proceso de tu próxima consulta:**
# 1. **Análisis** → Router examina tu mensaje
# 2. **Clasificación** → Determina tipo (SQL/RAG/Híbrido)
# 3. **Confianza** → Calcula nivel de certeza
# 4. **Routing** → Dirige al agente especializado
# 5. **Procesamiento** → Análisis específico
# 6. **Synthesis** → Respuesta final formateada

# 📊 **Métricas de Confianza:**
# • **Alta (>80%)**: Clasificación muy segura
# • **Buena (60-80%)**: Clasificación confiable  
# • **Media (40-60%)**: Clasificación probable
# • **Baja (<40%)**: Usa SQL Agent por defecto

# 🔄 **Estado Actual:**
# • ✅ Router Agent: Operativo
# • ✅ SQL Agent: Completamente funcional
# • ⏳ RAG Agent: En desarrollo
# • ✅ Orchestrator: Sistema v2.0 activo

# ¡Tu consulta será procesada inteligentemente!"""
            
#         elif command.startswith('/examples'):
#             return """📝 **Ejemplos de Consultas - Datos Transaccionales**

# 💰 **Análisis por Montos y Valores:**
# • "¿Cuál es el total de transacciones por periodo?"
# • "Valor promedio de transacciones por franquicia"
# • "Top 5 establecimientos por volumen de transacciones"
# • "Comparar montos entre Visa y Mastercard"

# 📅 **Análisis Temporal y Periodos:**
# • "Transacciones del último trimestre"
# • "Comparar este periodo vs periodo anterior"
# • "Tendencia mensual de transacciones por plataforma"
# • "Análisis anual por entidad emisora"

# 💳 **Análisis por Franquicia y Tipo de Tarjeta:**
# • "Distribución de transacciones Visa vs Mastercard"
# • "Análisis por entidad emisora y autorizadora"
# • "Estadísticas por tipo de franquicia"
# • "Comparación entre diferentes entidades adquirientes"

# 🏪 **Análisis por Establecimiento y Plataforma:**
# • "Establecimientos con más transacciones por plataforma"
# • "Análisis de rendimiento por pasarela de pago"
# • "Comparar diferentes plataformas por volumen"
# • "Estadísticas por subnivel de plataforma"

# 🔄 **Consultas Combinadas y Complejas:**
# • "Análisis cruzado: periodo + franquicia + plataforma"
# • "Evolución temporal por establecimiento y entidad"
# • "Comparación multi-dimensional de rendimientos"
# • "Reporte ejecutivo completo por todos los factores"

# 📊 **El Router clasificará automáticamente cada consulta como SQL y la procesará con el agente especializado en datos transaccionales**

# 🎯 **Tip**: Sé específico con fechas, franquicias, plataformas o establecimientos para obtener análisis más precisos

# ¡Prueba cualquiera de estos ejemplos específicos del dominio!"""

#         elif command.startswith('/tables'):
#             return """📋 **Consultando estructura de datos disponibles...**

# 🔄 Obteniendo información de la base de datos con el SQL Agent..."""

#         elif command.startswith('/status'):
#             return """🔍 **Estado del Sistema Multi-Agente v2.0**

# 🔄 Verificando todos los componentes de la arquitectura..."""

#         else:
#             return f"""❓ **Comando no reconocido:** `{command}`

# 📝 **Comandos disponibles en v2.0:**
# /help - Ayuda detallada del sistema multi-agente
# /system - Información completa de la arquitectura
# /examples - Ejemplos específicos de consultas transaccionales
# /tables - Ver estructura de datos disponibles
# /status - Estado completo del sistema

# 💡 **Tip**: Para hacer consultas de datos, simplemente escribe tu pregunta sin usar comandos. El Router la clasificará automáticamente."""
    
#     def get_database_tables(self):
#         """Obtener lista de tablas disponibles con info mejorada"""
#         try:
#             response = requests.get(f"{FASTAPI_URL}/api/database/tables", timeout=10)
#             if response.status_code == 200:
#                 result = response.json()
#                 tables_info = result.get('tables', 'No se encontraron tablas')
                
#                 enhanced_response = f"""📋 **Estructura de Datos Disponibles**

# 🗄️ **Tablas en la base de datos:**
# {tables_info}

# 📊 **Tipo de datos transaccionales disponibles:**
# • **Identificadores**: establecimiento, entidades
# • **Transaccionales**: cantidad, valor, periodo
# • **Clasificación**: franquicia, plataforma, pasarela
# • **Temporales**: periodo (para análisis temporal)

# 💡 **Ejemplos de consultas con estos datos:**
# • "Total por periodo usando la columna de fechas"
# • "Análisis por franquicia (Visa, Mastercard, etc.)"
# • "Comparación entre plataformas de pago"

# 🤖 **El SQL Agent conoce automáticamente esta estructura y optimiza las consultas**"""
                
#                 return enhanced_response
#             else:
#                 return "❌ Error obteniendo lista de tablas del SQL Agent"
#         except Exception as e:
#             return f"❌ Error conectando con el sistema: {str(e)}"
    
#     def get_system_status(self):
#         """Obtener estado del sistema con info del orchestrator"""
#         try:
#             response = requests.get(f"{FASTAPI_URL}/health", timeout=10)
#             if response.status_code == 200:
#                 result = response.json()
                
#                 status_text = "✅ **Sistema Multi-Agente v2.0 Operativo**\n\n"
                
#                 # Información de componentes
#                 if 'components' in result:
#                     status_text += "🧠 **Componentes de la Arquitectura:**\n"
#                     for component, status in result['components'].items():
#                         status_emoji = "✅" if status in ["active", "ready"] else "❌"
#                         status_text += f"{status_emoji} {component}: {status}\n"
                
#                 # Información de configuración
#                 if 'settings' in result:
#                     status_text += "\n⚙️ **Configuración del Sistema:**\n"
#                     for setting, configured in result['settings'].items():
#                         config_emoji = "✅" if configured else "❌"
#                         status_text += f"{config_emoji} {setting}\n"
                
#                 # Información específica de arquitectura
#                 if 'architecture' in result:
#                     arch = result['architecture']
#                     status_text += f"\n🏗️ **Arquitectura v{arch.get('version', '2.0')}:**\n"
#                     status_text += f"✅ Orchestrator: {'Activo' if arch.get('orchestrator_enabled') else 'Inactivo'}\n"
#                     status_text += f"✅ Router Agent: {'Activo' if arch.get('router_agent_enabled') else 'Inactivo'}\n"
#                     status_text += f"✅ SQL Agent: {'Activo' if arch.get('sql_agent_enabled') else 'Inactivo'}\n"
#                     status_text += f"⏳ RAG Agent: {'Activo' if arch.get('rag_agent_enabled') else 'En desarrollo'}\n"
                
#                 status_text += "\n🚀 **Sistema listo para procesar consultas inteligentemente**"
                
#                 return status_text
#             else:
#                 return f"⚠️ **Sistema con problemas**\n\nCódigo de respuesta: {response.status_code}\n\nAlgunos componentes pueden no estar funcionando correctamente."
#         except Exception as e:
#             return f"❌ **Sistema no disponible**\n\nError de conexión: {str(e)}\n\nVerifica que FastAPI esté ejecutándose con:\n`docker-compose up`"
    
#     def start_polling(self):
#         """Iniciar el bot con información mejorada"""
#         print("🤖 Iniciando Telegram Bot Multi-Agente v2.0...")
#         print(f"📡 FastAPI: {FASTAPI_URL}")
#         print("🧠 Arquitectura: Router + SQL Agent + Orchestrator")
#         print("💬 Listo para recibir mensajes inteligentes")
#         print("🛑 Presiona Ctrl+C para detener\n")
        
#         # Verificar FastAPI y arquitectura
#         try:
#             response = requests.get(f"{FASTAPI_URL}/health", timeout=5)
#             if response.status_code == 200:
#                 result = response.json()
#                 print("✅ FastAPI conectado correctamente")
                
#                 # Verificar componentes de la arquitectura
#                 if 'architecture' in result:
#                     arch = result['architecture']
#                     print(f"🧠 Orchestrator v{arch.get('version', '2.0')}: {'✅' if arch.get('orchestrator_enabled') else '❌'}")
#                     print(f"🎯 Router Agent: {'✅' if arch.get('router_agent_enabled') else '❌'}")
#                     print(f"📊 SQL Agent: {'✅' if arch.get('sql_agent_enabled') else '❌'}")
#                     print(f"📚 RAG Agent: {'⏳ En desarrollo' if not arch.get('rag_agent_enabled') else '✅'}")
#                 else:
#                     print("⚠️ Arquitectura legacy detectada")
#             else:
#                 print(f"⚠️ FastAPI responde con código: {response.status_code}")
#         except:
#             print("❌ No se puede conectar con FastAPI")
#             print("   Ejecuta: docker-compose up")
#             return
        
#         print("\n" + "="*50)
#         print("🚀 Bot iniciado - Procesamiento inteligente activo")
#         print("="*50 + "\n")
        
#         # Ciclo principal
#         while True:
#             try:
#                 updates = self.get_updates()
                
#                 for update in updates:
#                     self.offset = update["update_id"] + 1
                    
#                     if "message" in update:
#                         message = update["message"]
#                         chat_id = message["chat"]["id"]
#                         user_id = message["from"]["id"]
#                         username = message["from"].get("username", "unknown")
#                         first_name = message["from"].get("first_name", "Usuario")
#                         text = message.get("text", "")
                        
#                         if text:
#                             print(f"\n📩 @{username}: {text}")
                            
#                             # Procesar mensaje
#                             if text.startswith('/'):
#                                 if text.startswith('/tables'):
#                                     print("📋 Consultando estructura de datos...")
#                                     response = self.get_database_tables()
#                                 elif text.startswith('/status'):
#                                     print("🔍 Verificando estado del sistema...")
#                                     response = self.get_system_status()
#                                 else:
#                                     response = self.handle_command(text, first_name)
#                             else:
#                                 print("🧠 Procesando con sistema multi-agente...")
#                                 print("   → Router clasificando consulta...")
#                                 response = self.call_sql_agent(text, user_id, chat_id)
                            
#                             # Enviar respuesta
#                             print("📤 Enviando respuesta...")
#                             if self.send_message(chat_id, response):
#                                 print("✅ Mensaje enviado correctamente")
#                             else:
#                                 print("❌ Error enviando mensaje")
                
#                 # Pequeña pausa para no sobrecargar
#                 time.sleep(0.1)
                
#             except KeyboardInterrupt:
#                 print("\n🛑 Deteniendo bot multi-agente...")
#                 break
#             except Exception as e:
#                 print(f"❌ Error: {e}")
#                 time.sleep(5)

# def main():
#     # Verificar configuración
#     if not BOT_TOKEN or BOT_TOKEN == "temp":
#         print("❌ Error: TELEGRAM_BOT_TOKEN no configurado")
#         print("\n📝 Pasos para configurar:")
#         print("1. Busca @BotFather en Telegram")
#         print("2. Envía /newbot")
#         print("3. Sigue las instrucciones")
#         print("4. Copia el token al archivo .env")
#         print("5. Reinicia este script")
#         return
    
#     print(f"🔑 Token configurado: {BOT_TOKEN[:10]}...")
    
#     # Iniciar bot
#     bot = TelegramBot(BOT_TOKEN)
#     bot.start_polling()

# if __name__ == "__main__":
#     main()