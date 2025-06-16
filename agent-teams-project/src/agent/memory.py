from langchain.memory import ConversationBufferWindowMemory
from typing import Dict, List
import logging

logger = logging.getLogger(__name__)

class ConversationMemoryManager:
    def __init__(self, k: int = 10):
        self.memories: Dict[str, ConversationBufferWindowMemory] = {}
        self.k = k
    
    def get_memory(self, user_id: str) -> List:
        """Obtiene la memoria conversacional para un usuario específico"""
        if user_id not in self.memories:
            self.memories[user_id] = ConversationBufferWindowMemory(
                k=self.k,
                return_messages=True,
                memory_key="chat_history"
            )
        
        return self.memories[user_id].chat_memory.messages
    
    def save_interaction(self, user_id: str, user_input: str, ai_response: str):
        """Guarda una interacción en la memoria del usuario"""
        try:
            if user_id not in self.memories:
                self.memories[user_id] = ConversationBufferWindowMemory(
                    k=self.k,
                    return_messages=True,
                    memory_key="chat_history"
                )
            
            memory = self.memories[user_id]
            memory.chat_memory.add_user_message(user_input)
            memory.chat_memory.add_ai_message(ai_response)
            
        except Exception as e:
            logger.error(f"Error saving interaction for user {user_id}: {e}")
    
    def clear_memory(self, user_id: str):
        """Limpia la memoria de un usuario específico"""
        if user_id in self.memories:
            self.memories[user_id].clear()
    
    def get_conversation_summary(self, user_id: str) -> str:
        """Obtiene un resumen de la conversación del usuario"""
        if user_id not in self.memories:
            return "No hay conversaciones previas."
        
        messages = self.memories[user_id].chat_memory.messages
        if not messages:
            return "No hay conversaciones previas."
        
        return f"Conversación con {len(messages)} mensajes intercambiados."