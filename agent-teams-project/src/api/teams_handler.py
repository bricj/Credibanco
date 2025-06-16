import aiohttp
from typing import Dict, Any
from src.config.settings import settings
import logging

logger = logging.getLogger(__name__)

class TeamsHandler:
    def __init__(self):
        self.bot_id = settings.TEAMS_BOT_ID
        self.bot_password = settings.TEAMS_BOT_PASSWORD
    
    async def handle_webhook(self, payload: Dict[Any, Any], multi_agent_system):
        """Manejar webhook de Teams"""
        activity_type = payload.get("type")
        
        if activity_type == "message":
            return await self._handle_message(payload, multi_agent_system)
        elif activity_type == "conversationUpdate":
            return await self._handle_conversation_update(payload)
        
        return {"status": "ignored"}
    
    async def _handle_message(self, payload: Dict[Any, Any], multi_agent_system):
        """Procesar mensaje de Teams con análisis SQL"""
        try:
            text = payload.get("text", "").strip()
            user_id = payload["from"]["id"]
            conversation_id = payload["conversation"]["id"]
            service_url = payload["serviceUrl"]
            
            # Detectar consultas SQL/datos
            sql_keywords = ["sql", "database", "table", "query", "análisis", "datos", "reporte", "salarios"]
            is_sql_query = any(keyword in text.lower() for keyword in sql_keywords)
            
            if is_sql_query:
                result = await multi_agent_system.process_message(text, user_id)
                response_text = self._format_teams_response(result) if result["success"] else f"❌ Error: {result.get('error')}"
            else:
                response_text = """
                👋 ¡Hola! Soy tu asistente de análisis de datos SQL.
                
                Puedo ayudarte con:
                📊 Análisis de bases de datos
                📈 Generación de reportes ejecutivos
                🔍 Consultas SQL automáticas
                💡 Insights de datos
                
                **Ejemplos de consultas:**
                - "Analiza los salarios por ubicación y experiencia"
                - "Genera un reporte de ML Engineers remotos"
                - "¿Cuáles son las tendencias salariales por compañía?"
                
                ¡Pregúntame lo que necesites! 🚀
                """
            
            await self._send_response(service_url, conversation_id, response_text)
            return {"status": "processed"}
            
        except Exception as e:
            logger.error(f"Error procesando mensaje de Teams: {e}")
            return {"status": "error", "error": str(e)}
    
    def _format_teams_response(self, result: dict) -> str:
        """Formatear respuesta del multi-agente para Teams"""
        response = f"📊 **Análisis SQL Completado**\n\n"
        response += f"{result['response']}\n\n"
        
        if result.get("database_result"):
            response += f"💾 **Datos extraídos**: Consulta SQL ejecutada exitosamente\n"
        
        if result.get("detailed_analysis"):
            response += f"📈 **Análisis detallado disponible**\n"
            
        response += f"\n✅ Análisis generado por sistema multi-agente (SQL → Análisis → Reporte)"
        
        return response
    
    async def _send_response(self, service_url: str, conversation_id: str, response_text: str):
        """Enviar respuesta a Teams"""
        access_token = await self._get_access_token()
        
        message = {
            "type": "message",
            "text": response_text,
            "textFormat": "markdown"
        }
        
        url = f"{service_url}v3/conversations/{conversation_id}/activities"
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=message, headers=headers) as response:
                if response.status != 201:
                    logger.error(f"Error enviando mensaje a Teams: {response.status}")
    
    async def _get_access_token(self) -> str:
        """Obtener token de acceso de Microsoft"""
        url = "https://login.microsoftonline.com/botframework.com/oauth2/v2.0/token"
        
        data = {
            "grant_type": "client_credentials",
            "client_id": self.bot_id,
            "client_secret": self.bot_password,
            "scope": "https://api.botframework.com/.default"
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, data=data) as response:
                result = await response.json()
                return result["access_token"]
    
    async def _handle_conversation_update(self, payload: Dict[Any, Any]):
        """Manejar actualizaciones de conversación"""
        members_added = payload.get("membersAdded", [])
        
        if members_added:
            # Aquí podrías enviar un mensaje de bienvenida
            pass
            
        return {"status": "welcomed"}