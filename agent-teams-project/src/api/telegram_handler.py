import aiohttp
import asyncio
from typing import Dict, Any, Optional
from src.config.settings import settings
import logging

logger = logging.getLogger(__name__)

class TelegramHandler:
    def __init__(self):
        self.bot_token = settings.TELEGRAM_BOT_TOKEN
        self.base_url = f"https://api.telegram.org/bot{self.bot_token}"
    
    async def handle_webhook(self, payload: Dict[Any, Any], multi_agent_system) -> Dict[str, Any]:
        """Manejar webhook de Telegram"""
        try:
            # Verificar que es un mensaje
            if "message" not in payload:
                return {"status": "ignored", "reason": "no_message"}
            
            message = payload["message"]
            
            # Extraer información del mensaje
            text = message.get("text", "").strip()
            user_id = str(message["from"]["id"])
            chat_id = message["chat"]["id"]
            username = message["from"].get("username", "Unknown")
            first_name = message["from"].get("first_name", "Usuario")
            
            logger.info(f"Mensaje recibido de {username} ({user_id}): {text[:50]}...")
            
            # Verificar que hay texto
            if not text:
                await self._send_message(chat_id, "❌ Por favor envía un mensaje de texto.")
                return {"status": "processed", "reason": "empty_text"}
            
            # Comandos especiales
            if text.startswith('/'):
                return await self._handle_command(text, chat_id, first_name)
            
            # Procesar con el agente SQL
            await self._send_typing(chat_id)
            
            result = await multi_agent_system.process_message(
                message=text,
                user_id=user_id
            )
            
            # Formatear y enviar respuesta
            response_text = self._format_telegram_response(result, first_name)
            await self._send_message(chat_id, response_text)
            
            return {"status": "processed", "success": result["success"]}
            
        except Exception as e:
            logger.error(f"Error procesando mensaje de Telegram: {e}")
            try:
                chat_id = payload.get("message", {}).get("chat", {}).get("id")
                if chat_id:
                    await self._send_message(
                        chat_id, 
                        "❌ Ocurrió un error procesando tu mensaje. Por favor intenta nuevamente."
                    )
            except:
                pass
            return {"status": "error", "error": str(e)}
    
    async def _handle_command(self, command: str, chat_id: int, first_name: str) -> Dict[str, Any]:
        """Manejar comandos especiales"""
        if command.startswith('/start'):
            welcome_message = f"""
🤖 **¡Hola {first_name}!** Soy tu Asistente de Análisis SQL

📊 **¿Qué puedo hacer por ti?**
• Analizar bases de datos automáticamente
• Generar reportes ejecutivos
• Crear consultas SQL inteligentes
• Proporcionar insights de datos

💡 **Ejemplos de consultas:**
• "Analiza los salarios por ubicación"
• "¿Cuáles son las tendencias salariales por empresa?"
• "Genera un reporte de ML Engineers remotos"
• "Muéstrame estadísticas por nivel de experiencia"

🚀 **¡Simplemente escribe tu pregunta y yo me encargo del resto!**

📝 **Comandos disponibles:**
/help - Mostrar esta ayuda
/tables - Ver tablas disponibles
/examples - Ver más ejemplos
            """
            await self._send_message(chat_id, welcome_message)
            
        elif command.startswith('/help'):
            help_message = """
🆘 **Ayuda - Cómo usar el bot**

📋 **Tipos de consultas que puedo procesar:**
• Análisis de datos por categorías
• Comparaciones y tendencias
• Estadísticas descriptivas
• Reportes personalizados

💬 **Ejemplos prácticos:**
• "¿Cuántos empleados remotos hay?"
• "Compara salarios entre ciudades"
• "Análisis de experiencia vs salario"
• "Tendencias por tipo de trabajo"

⚡ **Tips:**
• Sé específico en tus preguntas
• Puedes usar lenguaje natural
• No necesitas conocer SQL
• El análisis se hace automáticamente

¿Tienes alguna pregunta específica sobre datos?
            """
            await self._send_message(chat_id, help_message)
            
        elif command.startswith('/examples'):
            examples_message = """
📝 **Ejemplos de Consultas Avanzadas**

💰 **Análisis Salariales:**
• "Salario promedio por nivel de experiencia"
• "Top 10 empresas mejor pagadas"
• "Diferencia salarial entre modalidades de trabajo"

🏢 **Análisis por Empresa:**
• "Empresas con más ofertas remotas"
• "Compañías que requieren más experiencia"
• "Análisis de beneficios por empresa"

📍 **Análisis Geográfico:**
• "Ciudades con mejores salarios para developers"
• "Comparación de costos por ubicación"
• "Trabajo remoto vs presencial por región"

🎯 **Análisis por Rol:**
• "Perfiles más demandados en tech"
• "Skills más valoradas por rol"
• "Proyección de crecimiento por posición"

¡Prueba cualquiera de estos o crea tu propia consulta!
            """
            await self._send_message(chat_id, examples_message)
            
        else:
            await self._send_message(
                chat_id, 
                f"❓ Comando no reconocido: {command}\n\nUsa /help para ver comandos disponibles."
            )
        
        return {"status": "command_processed", "command": command}
    
    def _format_telegram_response(self, result: dict, user_name: str) -> str:
        """Formatear respuesta del multi-agente para Telegram"""
        if not result["success"]:
            return f"❌ **Error en el análisis**\n\n{result.get('error', 'Error desconocido')}"
        
        response = f"📊 **Análisis Completado para {user_name}**\n\n"
        response += f"{result['response']}\n\n"
        
        # Información adicional si está disponible
        if result.get("database_result"):
            response += "💾 **Estado:** Datos extraídos exitosamente de la base de datos\n"
        
        if result.get("detailed_analysis"):
            response += "📈 **Análisis detallado:** Disponible en el reporte\n"
        
        # Footer informativo
        response += "\n" + "─" * 30 + "\n"
        response += "🤖 *Análisis generado por sistema multi-agente*\n"
        response += "🔄 *SQL → Procesamiento → Insights → Reporte*"
        
        return response
    
    async def _send_message(self, chat_id: int, text: str, parse_mode: str = "Markdown") -> bool:
        """Enviar mensaje a Telegram"""
        try:
            # Telegram tiene límite de 4096 caracteres
            if len(text) > 4000:
                # Dividir mensaje largo
                chunks = [text[i:i+4000] for i in range(0, len(text), 4000)]
                for chunk in chunks:
                    await self._send_single_message(chat_id, chunk, parse_mode)
                return True
            else:
                return await self._send_single_message(chat_id, text, parse_mode)
                
        except Exception as e:
            logger.error(f"Error enviando mensaje: {e}")
            return False
    
    async def _send_single_message(self, chat_id: int, text: str, parse_mode: str) -> bool:
        """Enviar un mensaje individual"""
        url = f"{self.base_url}/sendMessage"
        data = {
            "chat_id": chat_id,
            "text": text,
            "parse_mode": parse_mode
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=data, timeout=30) as response:
                    if response.status == 200:
                        return True
                    else:
                        logger.error(f"Error HTTP {response.status} enviando mensaje")
                        return False
        except asyncio.TimeoutError:
            logger.error("Timeout enviando mensaje a Telegram")
            return False
        except Exception as e:
            logger.error(f"Error en request a Telegram: {e}")
            return False
    
    async def _send_typing(self, chat_id: int):
        """Enviar indicador de 'escribiendo...'"""
        url = f"{self.base_url}/sendChatAction"
        data = {
            "chat_id": chat_id,
            "action": "typing"
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                await session.post(url, json=data, timeout=5)
        except:
            pass  # No es crítico si falla
    
    async def set_webhook(self, webhook_url: str) -> bool:
        """Configurar webhook de Telegram"""
        url = f"{self.base_url}/setWebhook"
        data = {"url": webhook_url}
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=data) as response:
                    result = await response.json()
                    if result.get("ok"):
                        logger.info(f"Webhook configurado: {webhook_url}")
                        return True
                    else:
                        logger.error(f"Error configurando webhook: {result}")
                        return False
        except Exception as e:
            logger.error(f"Error configurando webhook: {e}")
            return False
    
    async def get_webhook_info(self) -> dict:
        """Obtener información del webhook actual"""
        url = f"{self.base_url}/getWebhookInfo"
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    return await response.json()
        except Exception as e:
            logger.error(f"Error obteniendo info webhook: {e}")
            return {}
        
### Mejoras planteadas con el agente modularizado

# import aiohttp
# import asyncio
# from typing import Dict, Any, Optional
# from src.config.settings import settings
# import logging

# logger = logging.getLogger(__name__)

# class TelegramHandler:
#     def __init__(self):
#         self.bot_token = settings.TELEGRAM_BOT_TOKEN
#         self.base_url = f"https://api.telegram.org/bot{self.bot_token}"
    
#     async def handle_webhook(self, payload: Dict[Any, Any], multi_agent_system) -> Dict[str, Any]:
#         """Manejar webhook de Telegram"""
#         try:
#             # Verificar que es un mensaje
#             if "message" not in payload:
#                 return {"status": "ignored", "reason": "no_message"}
            
#             message = payload["message"]
            
#             # Extraer información del mensaje
#             text = message.get("text", "").strip()
#             user_id = str(message["from"]["id"])
#             chat_id = message["chat"]["id"]
#             username = message["from"].get("username", "Unknown")
#             first_name = message["from"].get("first_name", "Usuario")
            
#             logger.info(f"Mensaje recibido de {username} ({user_id}): {text[:50]}...")
            
#             # Verificar que hay texto
#             if not text:
#                 await self._send_message(chat_id, "❌ Por favor envía un mensaje de texto.")
#                 return {"status": "processed", "reason": "empty_text"}
            
#             # Comandos especiales
#             if text.startswith('/'):
#                 return await self._handle_command(text, chat_id, first_name)
            
#             # Procesar con el agente SQL
#             await self._send_typing(chat_id)
            
#             result = await multi_agent_system.process_message(
#                 message=text,
#                 user_id=user_id
#             )
            
#             # Formatear y enviar respuesta
#             response_text = self._format_telegram_response(result, first_name)
#             await self._send_message(chat_id, response_text)
            
#             # Log mejorado con información del orchestrator
#             query_type = result.get('query_type', 'unknown')
#             confidence = result.get('confidence', 0.0)
#             intent = result.get('intent', 'unknown')
            
#             logger.info(f"Respuesta enviada - Tipo: {query_type}, Intent: {intent}, Confianza: {confidence:.2f}")
            
#             return {
#                 "status": "processed", 
#                 "success": result["success"],
#                 "query_type": query_type,
#                 "confidence": confidence
#             }
            
#         except Exception as e:
#             logger.error(f"Error procesando mensaje de Telegram: {e}")
#             try:
#                 chat_id = payload.get("message", {}).get("chat", {}).get("id")
#                 if chat_id:
#                     await self._send_message(
#                         chat_id, 
#                         "❌ Ocurrió un error procesando tu mensaje. Por favor intenta nuevamente."
#                     )
#             except:
#                 pass
#             return {"status": "error", "error": str(e)}
    
#     async def _handle_command(self, command: str, chat_id: int, first_name: str) -> Dict[str, Any]:
#         """Manejar comandos especiales"""
#         if command.startswith('/start'):
#             welcome_message = f"""
# 🤖 **¡Hola {first_name}!** Soy tu Asistente de Análisis SQL Inteligente

# 🧠 **Sistema de Orquestación Avanzada:**
# • Router inteligente que clasifica tus consultas
# • Agente SQL especializado en análisis de datos
# • Sistema RAG para conocimiento (próximamente)

# 📊 **¿Qué puedo hacer por ti?**
# • Analizar bases de datos automáticamente
# • Generar reportes ejecutivos
# • Crear consultas SQL inteligentes
# • Proporcionar insights de datos

# 💡 **Ejemplos de consultas SQL:**
# • "¿Cuál es el total de transacciones por periodo?"
# • "Mostrar análisis por franquicia"
# • "Comparar plataformas de pago"
# • "Reporte de transacciones por establecimiento"

# 🚀 **¡Simplemente escribe tu pregunta y yo me encargo del resto!**

# 📝 **Comandos disponibles:**
# /help - Mostrar ayuda detallada
# /system - Info del sistema de orquestación
# /examples - Ver ejemplos específicos
# /debug - Información técnica del sistema
#             """
#             await self._send_message(chat_id, welcome_message)
            
#         elif command.startswith('/help'):
#             help_message = """
# 🆘 **Ayuda - Sistema Multi-Agente**

# 🎯 **Cómo funciona la clasificación inteligente:**
# • El router analiza tu consulta automáticamente
# • Determina si necesitas análisis SQL o conocimiento
# • Dirige tu consulta al agente especializado

# 📋 **Tipos de consultas que proceso:**

# 🔢 **Consultas SQL (Datos):**
# • Total de transacciones
# • Análisis por periodo, franquicia, plataforma
# • Comparaciones y tendencias
# • Reportes ejecutivos

# 📚 **Consultas RAG (Conocimiento - Próximamente):**
# • Explicaciones de conceptos
# • Documentación y procedimientos
# • Definiciones técnicas

# 💬 **Ejemplos prácticos:**
# • "Total transacciones en diciembre"
# • "Análisis por tipo de tarjeta"
# • "Comparar rendimiento por plataforma"
# • "Estadísticas de establecimientos"

# ⚡ **Tips:**
# • Usa lenguaje natural
# • Sé específico en fechas y categorías
# • El sistema clasificará automáticamente tu consulta

# ¿Tienes alguna pregunta específica sobre datos?
#             """
#             await self._send_message(chat_id, help_message)

#         elif command.startswith('/system'):
#             system_message = """
# 🔧 **Sistema de Orquestación Multi-Agente v2.0**

# 🧠 **Arquitectura Actual:**
# • **Router Agent**: Clasificador de intenciones inteligente
# • **SQL Agent**: Especialista en análisis de datos transaccionales
# • **RAG Agent**: Sistema de conocimiento (en desarrollo)
# • **Orchestrator**: Coordinador principal del sistema

# 🎯 **Proceso de Análisis:**
# 1. **Recepción**: Tu mensaje llega al router
# 2. **Clasificación**: Se determina el tipo de consulta
# 3. **Routing**: Se dirige al agente especializado
# 4. **Procesamiento**: El agente genera la respuesta
# 5. **Synthesis**: Se formatea la respuesta final

# 📊 **Métricas de Confianza:**
# • **Alta (>80%)**: Clasificación muy segura
# • **Media (50-80%)**: Clasificación confiable
# • **Baja (<50%)**: Se usa agente SQL por defecto

# 🔄 **Estado Actual:**
# • ✅ Router Agent: Activo
# • ✅ SQL Agent: Activo  
# • ⏳ RAG Agent: En desarrollo
# • ✅ Orchestrator: Operativo

# ¡El sistema está optimizado para darte las mejores respuestas!
#             """
#             await self._send_message(chat_id, system_message)
            
#         elif command.startswith('/examples'):
#             examples_message = """
# 📝 **Ejemplos de Consultas por Tipo**

# 📊 **Consultas SQL - Análisis de Datos:**

# 💰 **Por Montos y Valores:**
# • "¿Cuál es el total de transacciones del último periodo?"
# • "Valor promedio de transacciones por franquicia"
# • "Top 5 establecimientos por volumen de transacciones"

# 📅 **Por Periodo y Tiempo:**
# • "Transacciones por mes en 2024"
# • "Comparar este periodo vs periodo anterior"
# • "Tendencia de transacciones por trimestre"

# 🏪 **Por Establecimiento y Plataforma:**
# • "Análisis de transacciones por plataforma de pago"
# • "Establecimientos con más transacciones"
# • "Comparación entre diferentes entidades emisoras"

# 💳 **Por Franquicia y Tipo:**
# • "Distribución de transacciones Visa vs Mastercard"
# • "Análisis por tipo de entidad autorizadora"
# • "Estadísticas por pasarela de pago"

# 📚 **Consultas RAG - Conocimiento (Próximamente):**
# • "¿Qué es una entidad adquiriente?"
# • "Explica el proceso de autorización de transacciones"
# • "Documentación sobre franquicias de tarjetas"

# ¡Prueba cualquiera de estos o crea tu propia consulta!
#             """
#             await self._send_message(chat_id, examples_message)

#         elif command.startswith('/debug'):
#             debug_message = """
# 🔧 **Modo Debug - Información Técnica**

# 🧠 **Router Agent - Clasificador:**
# • **Método**: Análisis de keywords + confianza
# • **Threshold**: 0.5 para decisiones
# • **Fallback**: SQL Agent por defecto
# • **Keywords SQL**: total, suma, transacciones, periodo, franquicia
# • **Keywords RAG**: explicar, documentación, procedimiento

# 📊 **SQL Agent - Especialista en Datos:**
# • **Base de Datos**: SQLite con datos transaccionales
# • **Herramientas**: list_tables, tables_schema, execute_sql
# • **Contexto**: Conoce estructura de tablas y columnas
# • **Fallback**: Ejecución directa si herramientas fallan

# 🔄 **Orchestrator - Coordinador:**
# • **Pipeline**: LangGraph StateGraph
# • **Estados**: Router → Procesamiento → Respuesta
# • **Memoria**: Conversacional por usuario
# • **Logging**: Completo para debugging

# 📈 **Próxima Consulta - Proceso:**
# 1. Tu mensaje → Router (análisis de intent)
# 2. Clasificación → Confianza calculada
# 3. Routing → Agente especializado
# 4. Procesamiento → Análisis y respuesta
# 5. Formateo → Mensaje final para ti

# **¡Envía una consulta para ver el proceso en acción!**
#             """
#             await self._send_message(chat_id, debug_message)
            
#         else:
#             await self._send_message(
#                 chat_id, 
#                 f"❓ Comando no reconocido: {command}\n\nUsa /help para ver comandos disponibles."
#             )
        
#         return {"status": "command_processed", "command": command}
    
#     def _format_telegram_response(self, result: dict, user_name: str) -> str:
#         """Formatear respuesta del multi-agente para Telegram con mejoras del orchestrator"""
#         if not result["success"]:
#             return f"❌ **Error en el análisis**\n\n{result.get('error', 'Error desconocido')}"
        
#         # Información del tipo de consulta y confianza
#         query_type = result.get('query_type', 'unknown')
#         confidence = result.get('confidence', 0.0)
#         intent = result.get('intent', 'unknown')
        
#         # Emoji y título según tipo de consulta
#         query_info = {
#             'sql': {'emoji': '📊', 'title': 'Análisis SQL'},
#             'rag': {'emoji': '📚', 'title': 'Consulta de Conocimiento'}, 
#             'hybrid': {'emoji': '🔄', 'title': 'Análisis Híbrido'},
#             'error': {'emoji': '❌', 'title': 'Error'}
#         }
        
#         info = query_info.get(query_type, {'emoji': '🤖', 'title': 'Análisis'})
        
#         response = f"{info['emoji']} **{info['title']} - {user_name}**\n\n"
#         response += f"{result['response']}\n\n"
        
#         # Información adicional existente
#         if result.get("database_result"):
#             response += "💾 **Estado:** Datos extraídos exitosamente de la base de datos\n"
        
#         if result.get("detailed_analysis"):
#             response += "📈 **Análisis detallado:** Disponible en el reporte\n"
        
#         # Nueva información del orchestrator
#         response += f"🎯 **Tipo de consulta:** {query_type.upper()}\n"
        
#         # Información de confianza con emojis
#         if confidence > 0.8:
#             response += f"✨ **Confianza:** Alta ({confidence:.1%})\n"
#         elif confidence > 0.6:
#             response += f"⚡ **Confianza:** Buena ({confidence:.1%})\n"
#         elif confidence > 0.4:
#             response += f"🔶 **Confianza:** Media ({confidence:.1%})\n"
#         else:
#             response += f"🔸 **Confianza:** Baja ({confidence:.1%}) - Clasificación por defecto\n"
        
#         # Footer informativo actualizado
#         response += "\n" + "─" * 30 + "\n"
#         response += f"🤖 *Análisis {query_type.upper()} generado por orquestador v2.0*\n"
        
#         # Footer específico por tipo
#         if query_type == 'sql':
#             response += "🔄 *Router → SQL Agent → Análisis → Reporte*"
#         elif query_type == 'rag':
#             response += "🔄 *Router → RAG Agent → Conocimiento → Respuesta*"
#         elif query_type == 'hybrid':
#             response += "🔄 *Router → Multi-Agent → Synthesis → Reporte*"
#         else:
#             response += "🔄 *Sistema de orquestación inteligente*"
        
#         return response
    
#     async def _send_message(self, chat_id: int, text: str, parse_mode: str = "Markdown") -> bool:
#         """Enviar mensaje a Telegram"""
#         try:
#             # Telegram tiene límite de 4096 caracteres
#             if len(text) > 4000:
#                 # Dividir mensaje largo
#                 chunks = [text[i:i+4000] for i in range(0, len(text), 4000)]
#                 for chunk in chunks:
#                     await self._send_single_message(chat_id, chunk, parse_mode)
#                 return True
#             else:
#                 return await self._send_single_message(chat_id, text, parse_mode)
                
#         except Exception as e:
#             logger.error(f"Error enviando mensaje: {e}")
#             return False
    
#     async def _send_single_message(self, chat_id: int, text: str, parse_mode: str) -> bool:
#         """Enviar un mensaje individual"""
#         url = f"{self.base_url}/sendMessage"
#         data = {
#             "chat_id": chat_id,
#             "text": text,
#             "parse_mode": parse_mode
#         }
        
#         try:
#             async with aiohttp.ClientSession() as session:
#                 async with session.post(url, json=data, timeout=30) as response:
#                     if response.status == 200:
#                         return True
#                     else:
#                         logger.error(f"Error HTTP {response.status} enviando mensaje")
#                         return False
#         except asyncio.TimeoutError:
#             logger.error("Timeout enviando mensaje a Telegram")
#             return False
#         except Exception as e:
#             logger.error(f"Error en request a Telegram: {e}")
#             return False
    
#     async def _send_typing(self, chat_id: int):
#         """Enviar indicador de 'escribiendo...'"""
#         url = f"{self.base_url}/sendChatAction"
#         data = {
#             "chat_id": chat_id,
#             "action": "typing"
#         }
        
#         try:
#             async with aiohttp.ClientSession() as session:
#                 await session.post(url, json=data, timeout=5)
#         except:
#             pass  # No es crítico si falla
    
#     async def set_webhook(self, webhook_url: str) -> bool:
#         """Configurar webhook de Telegram"""
#         url = f"{self.base_url}/setWebhook"
#         data = {"url": webhook_url}
        
#         try:
#             async with aiohttp.ClientSession() as session:
#                 async with session.post(url, json=data) as response:
#                     result = await response.json()
#                     if result.get("ok"):
#                         logger.info(f"Webhook configurado: {webhook_url}")
#                         return True
#                     else:
#                         logger.error(f"Error configurando webhook: {result}")
#                         return False
#         except Exception as e:
#             logger.error(f"Error configurando webhook: {e}")
#             return False
    
#     async def get_webhook_info(self) -> dict:
#         """Obtener información del webhook actual"""
#         url = f"{self.base_url}/getWebhookInfo"
        
#         try:
#             async with aiohttp.ClientSession() as session:
#                 async with session.get(url) as response:
#                     return await response.json()
#         except Exception as e:
#             logger.error(f"Error obteniendo info webhook: {e}")
#             return {}