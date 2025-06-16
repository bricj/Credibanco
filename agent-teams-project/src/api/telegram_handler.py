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