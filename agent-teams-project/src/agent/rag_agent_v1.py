# import logging
# import os
# from typing import List, Dict, Any
# from pathlib import Path

# # Document Processing
# from pypdf import PdfReader
# import pdfplumber
# import pytesseract
# from PIL import Image

# # Embeddings y Vector Store
# from langchain_google_genai import GoogleGenerativeAIEmbeddings
# from langchain.vectorstores import Chroma
# from langchain.text_splitter import RecursiveCharacterTextSplitter
# from langchain.chains import RetrievalQA
# from langchain_google_genai import ChatGoogleGenerativeAI

# # Memory
# from .memory import ConversationMemoryManager

# logger = logging.getLogger(__name__)

# class RAGAgentSystem:
#     """Sistema RAG híbrido con ChromaDB y Google Embeddings"""
    
#     def __init__(self, llm: ChatGoogleGenerativeAI, memory_manager: ConversationMemoryManager):
#         self.llm = llm
#         self.memory_manager = memory_manager
        
#         # Configuración
#         self.documents_path = Path("./data/documents")
#         self.documents_path.mkdir(parents=True, exist_ok=True)
        
#         # Directorio para ChromaDB
#         self.chroma_path = Path("./data/chroma_db")
#         self.chroma_path.mkdir(parents=True, exist_ok=True)
        
#         # Inicializar componentes
#         self.embeddings = GoogleGenerativeAIEmbeddings(
#             model="models/embedding-001",
#             google_api_key=os.getenv("GOOGLE_API_KEY")
#         )
        
#         self.text_splitter = RecursiveCharacterTextSplitter(
#             chunk_size=1000,
#             chunk_overlap=200
#         )
        
#         # Collection name para ChromaDB
#         self.collection_name = "knowledge_base"
        
#         logger.info("✅ RAGAgentSystem con ChromaDB y Google Embeddings inicializado")
    
#     def extract_text_from_pdf(self, pdf_path: str) -> str:
#         """Extraer texto de PDF con OCR para imágenes"""
#         text = ""
        
#         try:
#             # Extraer texto directo
#             with open(pdf_path, 'rb') as file:
#                 reader = PdfReader(file)
#                 for page in reader.pages:
#                     text += page.extract_text() or ""
            
#             # Si hay poco texto, usar OCR
#             if len(text.strip()) < 100:
#                 with pdfplumber.open(pdf_path) as pdf:
#                     for page in pdf.pages:
#                         # Extraer texto
#                         page_text = page.extract_text()
#                         if page_text:
#                             text += page_text
                        
#                         # OCR para imágenes si es necesario
#                         if len(page_text or "") < 50:
#                             try:
#                                 img = page.to_image()
#                                 ocr_text = pytesseract.image_to_string(img.original, lang='spa+eng')
#                                 text += f"\n[OCR]: {ocr_text}"
#                             except:
#                                 pass
            
#             logger.info(f"✅ Extraído {len(text)} caracteres de {pdf_path}")
#             return text
            
#         except Exception as e:
#             logger.error(f"❌ Error extrayendo texto de {pdf_path}: {e}")
#             return ""
    
#     def extract_text_from_document(self, file_path: str) -> str:
#         """Extraer texto según extensión"""
#         file_path = Path(file_path)
#         extension = file_path.suffix.lower()
        
#         if extension == '.pdf':
#             return self.extract_text_from_pdf(str(file_path))
#         elif extension in ['.txt', '.md']:
#             try:
#                 with open(file_path, 'r', encoding='utf-8') as f:
#                     return f.read()
#             except Exception as e:
#                 logger.error(f"❌ Error leyendo {file_path}: {e}")
#                 return ""
#         else:
#             logger.warning(f"⚠️ Tipo no soportado: {extension}")
#             return ""
    
#     def ingest_all_documents(self) -> Dict[str, Any]:
#         """Procesar todos los documentos en data/documents"""
#         try:
#             # Buscar documentos
#             documents = []
#             for ext in ['.pdf', '.txt', '.md']:
#                 documents.extend(self.documents_path.glob(f"*{ext}"))
            
#             if not documents:
#                 return {
#                     "success": False,
#                     "error": f"No hay documentos en {self.documents_path}"
#                 }
            
#             # Extraer texto de todos los documentos
#             all_texts = []
#             metadatas = []
            
#             for doc_path in documents:
#                 text = self.extract_text_from_document(str(doc_path))
#                 if text:
#                     # Dividir en chunks
#                     chunks = self.text_splitter.split_text(text)
#                     all_texts.extend(chunks)
                    
#                     # Metadata para cada chunk
#                     for i, chunk in enumerate(chunks):
#                         metadatas.append({
#                             "source": str(doc_path),
#                             "filename": doc_path.name,
#                             "chunk": i,
#                             "total_chunks": len(chunks)
#                         })
            
#             if not all_texts:
#                 return {"success": False, "error": "No se extrajo texto válido"}
            
#             # Crear vector store con ChromaDB
#             self.vectorstore = Chroma.from_texts(
#                 texts=all_texts,
#                 embedding=self.embeddings,
#                 metadatas=metadatas,
#                 collection_name=self.collection_name,
#                 persist_directory=str(self.chroma_path)
#             )
            
#             # Persistir la base de datos
#             self.vectorstore.persist()
            
#             # Crear chain QA
#             self.qa_chain = RetrievalQA.from_chain_type(
#                 llm=self.llm,
#                 chain_type="stuff",
#                 retriever=self.vectorstore.as_retriever(search_kwargs={"k": 3})
#             )
            
#             logger.info(f"✅ Ingesta completada: {len(all_texts)} chunks de {len(documents)} documentos")
#             return {
#                 "success": True,
#                 "documents_processed": len(documents),
#                 "chunks_created": len(all_texts),
#                 "filenames": [doc.name for doc in documents],
#                 "chroma_path": str(self.chroma_path)
#             }
            
#         except Exception as e:
#             logger.error(f"❌ Error en ingesta: {e}")
#             return {"success": False, "error": str(e)}
    
#     def _ensure_vectorstore(self):
#         """Asegurar que vectorstore existe"""
#         if not hasattr(self, 'vectorstore') or self.vectorstore is None:
#             try:
#                 # Intentar cargar vectorstore existente desde ChromaDB
#                 self.vectorstore = Chroma(
#                     embedding_function=self.embeddings,
#                     collection_name=self.collection_name,
#                     persist_directory=str(self.chroma_path)
#                 )
                
#                 self.qa_chain = RetrievalQA.from_chain_type(
#                     llm=self.llm,
#                     chain_type="stuff",
#                     retriever=self.vectorstore.as_retriever(search_kwargs={"k": 3})
#                 )
                
#                 logger.info("✅ ChromaDB vectorstore cargado desde disco")
#                 return True
                
#             except Exception as e:
#                 logger.warning(f"⚠️ No hay vectorstore existente en ChromaDB: {e}")
#                 return False
#         return True
    
#     def process_rag_query(self, query: str, user_id: str) -> Dict[str, Any]:
#         """Procesar consulta RAG completa"""
#         try:
#             # Asegurar vectorstore
#             if not self._ensure_vectorstore():
#                 return {
#                     "success": False,
#                     "response": "La base de conocimiento no está disponible. Ejecuta la ingesta de documentos primero.",
#                     "query_type": "rag"
#                 }
            
#             # Ejecutar consulta
#             result = self.qa_chain.run(query)
            
#             # Obtener documentos relevantes para metadata
#             docs = self.vectorstore.similarity_search(query, k=3)
#             sources = [doc.metadata.get("filename", "unknown") for doc in docs]
            
#             # Guardar en memoria
#             self.memory_manager.save_interaction(user_id, query, result)
            
#             return {
#                 "success": True,
#                 "response": result,
#                 "sources": list(set(sources)),
#                 "query_type": "rag"
#             }
            
#         except Exception as e:
#             logger.error(f"❌ Error en consulta RAG: {e}")
#             return {
#                 "success": False,
#                 "error": str(e),
#                 "response": "Error procesando consulta de conocimiento.",
#                 "query_type": "rag"
#             }
    
#     def get_knowledge_stats(self) -> Dict[str, Any]:
#         """Estadísticas de la base de conocimiento"""
#         try:
#             docs_count = len(list(self.documents_path.glob("*.pdf"))) + \
#                         len(list(self.documents_path.glob("*.txt"))) + \
#                         len(list(self.documents_path.glob("*.md")))
            
#             vectorstore_ready = hasattr(self, 'vectorstore') and self.vectorstore is not None
#             chroma_exists = self.chroma_path.exists() and any(self.chroma_path.iterdir())
            
#             return {
#                 "documents_folder": str(self.documents_path),
#                 "total_documents": docs_count,
#                 "vectorstore_ready": vectorstore_ready,
#                 "chroma_db_exists": chroma_exists,
#                 "chroma_path": str(self.chroma_path),
#                 "embedding_model": "Google models/embedding-001",
#                 "supported_formats": [".pdf", ".txt", ".md"]
#             }
            
#         except Exception as e:
#             logger.error(f"❌ Error obteniendo estadísticas: {e}")
#             return {"error": str(e)}

#######################################################

import logging
import os
from typing import List, Dict, Any
from pathlib import Path

# Document Processing
from pypdf import PdfReader
import pdfplumber
import pytesseract
from PIL import Image

# Embeddings y Vector Store
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain.vectorstores import Chroma
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI

# Memory
from .memory import ConversationMemoryManager

logger = logging.getLogger(__name__)

class RAGAgentSystem:
    """Sistema RAG híbrido con ChromaDB y Google Embeddings"""
    
    def __init__(self, llm: ChatGoogleGenerativeAI, memory_manager: ConversationMemoryManager):
        self.llm = llm
        self.memory_manager = memory_manager
        
        # Configuración
        self.documents_path = Path("./data/documents")
        self.documents_path.mkdir(parents=True, exist_ok=True)
        
        # Directorio para ChromaDB
        self.chroma_path = Path("./data/chroma_db")
        self.chroma_path.mkdir(parents=True, exist_ok=True)
        
        # Inicializar componentes
        self.embeddings = GoogleGenerativeAIEmbeddings(
            model="models/embedding-001",
            google_api_key=os.getenv("GOOGLE_API_KEY")
        )
        
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200
        )
        
        # Collection name para ChromaDB
        self.collection_name = "knowledge_base"
        
        # Variables para debugging
        self.vectorstore = None
        self.qa_chain = None
        
        # Prompt personalizado para RAG
        self.custom_prompt = self._create_custom_prompt()
        
        logger.info("✅ RAGAgentSystem con ChromaDB y Google Embeddings inicializado")
    
    def _create_custom_prompt(self) -> PromptTemplate:
        """Crear prompt personalizado con few-shot examples"""
        template = """Eres un analista financiero experto especializado en estados financieros de instituciones bancarias colombianas.

CONTEXTO:
{context}

INSTRUCCIONES:
1. Analiza cuidadosamente los documentos financieros proporcionados
2. Proporciona respuestas precisas basadas únicamente en la información disponible
3. Si encuentras cifras específicas, inclúyelas con sus unidades (miles de pesos, millones, etc.)
4. Si la información no está disponible, indícalo claramente pero de manera útil
5. Mantén un tono profesional y técnico
6. Siempre contextualiza las cifras con períodos de comparación cuando estén disponibles

EJEMPLOS DE RESPUESTAS ESPERADAS:

Ejemplo 1:
Pregunta: "¿Cuál es el total de activos?"
Respuesta: "Según los estados financieros de Credibanco S.A., el total de activos al 31 de diciembre de 2023 es de $436,274,863 miles de pesos colombianos, comparado con $425,521,684 miles de pesos en 2022, representando un incremento del 2.5%."

Ejemplo 2:
Pregunta: "¿Cuáles son los ingresos por actividades ordinarias?"
Respuesta: "Los ingresos por actividades ordinarias de Credibanco para el período terminado el 31 de diciembre de 2023 ascendieron a $356,295,648 miles de pesos, comparado con $292,636,325 miles de pesos en 2022, evidenciando un crecimiento del 21.8%."

Ejemplo 3:
Pregunta: "¿Qué información hay sobre efectivo?"
Respuesta: "El efectivo y equivalentes al efectivo de Credibanco al 31 de diciembre de 2023 fue de $19,700,390 miles de pesos colombianos, comparado con $32,980,791 miles de pesos en 2022, mostrando una disminución del 40.3%."

Ejemplo 4:
Pregunta: "¿Cuáles son las inversiones en subsidiarias?"
Respuesta: "Las inversiones en subsidiarias y negocios conjuntos de Credibanco al 31 de diciembre de 2023 totalizaron $4,494,817 miles de pesos colombianos, mientras que en 2022 fueron de $6,991,278 miles de pesos."

PREGUNTA: {question}

RESPUESTA DETALLADA:"""
        
        return PromptTemplate(
            template=template,
            input_variables=["context", "question"]
        )
    
    def extract_text_from_pdf(self, pdf_path: str) -> str:
        """Extraer texto de PDF con OCR para imágenes"""
        text = ""
        
        try:
            # Extraer texto directo
            with open(pdf_path, 'rb') as file:
                reader = PdfReader(file)
                for page in reader.pages:
                    text += page.extract_text() or ""
            
            # Si hay poco texto, usar OCR
            if len(text.strip()) < 100:
                with pdfplumber.open(pdf_path) as pdf:
                    for page in pdf.pages:
                        # Extraer texto
                        page_text = page.extract_text()
                        if page_text:
                            text += page_text
                        
                        # OCR para imágenes si es necesario
                        if len(page_text or "") < 50:
                            try:
                                img = page.to_image()
                                ocr_text = pytesseract.image_to_string(img.original, lang='spa+eng')
                                text += f"\n[OCR]: {ocr_text}"
                            except:
                                pass
            
            logger.info(f"✅ Extraído {len(text)} caracteres de {pdf_path}")
            return text
            
        except Exception as e:
            logger.error(f"❌ Error extrayendo texto de {pdf_path}: {e}")
            return ""
    
    def extract_text_from_document(self, file_path: str) -> str:
        """Extraer texto según extensión"""
        file_path = Path(file_path)
        extension = file_path.suffix.lower()
        
        if extension == '.pdf':
            return self.extract_text_from_pdf(str(file_path))
        elif extension in ['.txt', '.md']:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    return f.read()
            except Exception as e:
                logger.error(f"❌ Error leyendo {file_path}: {e}")
                return ""
        else:
            logger.warning(f"⚠️ Tipo no soportado: {extension}")
            return ""
    
    def ingest_all_documents(self) -> Dict[str, Any]:
        """Procesar todos los documentos en data/documents"""
        try:
            # Buscar documentos
            documents = []
            for ext in ['.pdf', '.txt', '.md']:
                documents.extend(self.documents_path.glob(f"*{ext}"))
            
            if not documents:
                return {
                    "success": False,
                    "error": f"No hay documentos en {self.documents_path}"
                }
            
            logger.info(f"📁 Documentos encontrados: {[doc.name for doc in documents]}")
            
            # Extraer texto de todos los documentos
            all_texts = []
            metadatas = []
            
            for doc_path in documents:
                logger.info(f"📄 Procesando: {doc_path.name}")
                text = self.extract_text_from_document(str(doc_path))
                if text:
                    # Dividir en chunks
                    chunks = self.text_splitter.split_text(text)
                    all_texts.extend(chunks)
                    
                    logger.info(f"✂️ {doc_path.name}: {len(chunks)} chunks creados")
                    
                    # Metadata para cada chunk
                    for i, chunk in enumerate(chunks):
                        metadatas.append({
                            "source": str(doc_path),
                            "filename": doc_path.name,
                            "chunk": i,
                            "total_chunks": len(chunks)
                        })
                else:
                    logger.warning(f"⚠️ No se extrajo texto de {doc_path.name}")
            
            if not all_texts:
                return {"success": False, "error": "No se extrajo texto válido"}
            
            logger.info(f"📊 Total chunks a indexar: {len(all_texts)}")
            
            # Crear vector store con ChromaDB
            self.vectorstore = Chroma.from_texts(
                texts=all_texts,
                embedding=self.embeddings,
                metadatas=metadatas,
                collection_name=self.collection_name,
                persist_directory=str(self.chroma_path)
            )
            
            # Persistir la base de datos
            self.vectorstore.persist()
            logger.info(f"💾 ChromaDB persistido en: {self.chroma_path}")
            
            # Crear chain QA con prompt personalizado
            self.qa_chain = RetrievalQA.from_chain_type(
                llm=self.llm,
                chain_type="stuff",
                retriever=self.vectorstore.as_retriever(search_kwargs={"k": 15}),
                chain_type_kwargs={"prompt": self.custom_prompt}
            )
            
            # Validar que funciona
            validation_result = self._validate_vectorstore()
            
            logger.info(f"✅ Ingesta completada: {len(all_texts)} chunks de {len(documents)} documentos")
            return {
                "success": True,
                "documents_processed": len(documents),
                "chunks_created": len(all_texts),
                "filenames": [doc.name for doc in documents],
                "chroma_path": str(self.chroma_path),
                "validation": validation_result
            }
            
        except Exception as e:
            logger.error(f"❌ Error en ingesta: {e}")
            return {"success": False, "error": str(e)}
    
    def _ensure_vectorstore(self):
        """Asegurar que vectorstore existe"""
        if not hasattr(self, 'vectorstore') or self.vectorstore is None:
            try:
                # Intentar cargar vectorstore existente desde ChromaDB
                self.vectorstore = Chroma(
                    embedding_function=self.embeddings,
                    collection_name=self.collection_name,
                    persist_directory=str(self.chroma_path)
                )
                
                # Validar que tiene contenido
                try:
                    collection_count = self.vectorstore._collection.count()
                    logger.info(f"📊 ChromaDB cargado: {collection_count} documentos")
                    
                    if collection_count == 0:
                        logger.warning("⚠️ ChromaDB existe pero está vacío")
                        return False
                        
                except Exception as e:
                    logger.error(f"❌ Error verificando contenido de ChromaDB: {e}")
                    return False
                
                # Crear chain QA con prompt personalizado
                self.qa_chain = RetrievalQA.from_chain_type(
                    llm=self.llm,
                    chain_type="stuff",
                    retriever=self.vectorstore.as_retriever(search_kwargs={"k": 15}),
                    chain_type_kwargs={"prompt": self.custom_prompt}
                )
                
                logger.info("✅ ChromaDB vectorstore cargado desde disco")
                return True
                
            except Exception as e:
                logger.warning(f"⚠️ No hay vectorstore existente en ChromaDB: {e}")
                return False
        return True
    
    def _validate_vectorstore(self) -> Dict[str, Any]:
        """Validar que el vectorstore funciona correctamente"""
        if not self.vectorstore:
            return {"status": "error", "message": "Vectorstore no disponible"}
        
        try:
            # Test 1: Contar documentos
            count = self.vectorstore._collection.count()
            
            # Test 2: Búsqueda simple
            test_queries = ["activos", "credibanco", "estados financieros", "total"]
            test_results = {}
            
            for query in test_queries:
                try:
                    docs = self.vectorstore.similarity_search(query, k=3)
                    scores = self.vectorstore.similarity_search_with_score(query, k=3)
                    
                    test_results[query] = {
                        "docs_found": len(docs),
                        "best_score": scores[0][1] if scores else None,
                        "preview": docs[0].page_content[:100] if docs else "No content"
                    }
                    
                    logger.info(f"🔍 Test '{query}': {len(docs)} docs, score: {scores[0][1] if scores else 'N/A'}")
                    
                except Exception as e:
                    test_results[query] = {"error": str(e)}
                    logger.error(f"❌ Error en test '{query}': {e}")
            
            return {
                "status": "success",
                "total_documents": count,
                "test_results": test_results
            }
            
        except Exception as e:
            logger.error(f"❌ Error validando vectorstore: {e}")
            return {"status": "error", "message": str(e)}
    
    def debug_search(self, query: str, k: int = 5) -> Dict[str, Any]:
        """Debug de búsqueda para diagnóstico"""
        try:
            if not self._ensure_vectorstore():
                return {"error": "Vectorstore no disponible"}
            
            logger.info(f"🔍 DEBUG: Buscando '{query}'")
            
            # Búsqueda con scores
            docs_with_scores = self.vectorstore.similarity_search_with_score(query, k=k)
            
            results = []
            for i, (doc, score) in enumerate(docs_with_scores):
                result = {
                    "index": i,
                    "score": float(score),
                    "content_preview": doc.page_content[:200],
                    "metadata": doc.metadata,
                    "content_length": len(doc.page_content)
                }
                results.append(result)
                
                logger.info(f"📄 Doc {i}: score={score:.4f}, source={doc.metadata.get('filename', 'unknown')}")
                logger.info(f"📝 Preview: {doc.page_content[:100]}...")
            
            return {
                "query": query,
                "total_results": len(results),
                "results": results,
                "vectorstore_count": self.vectorstore._collection.count()
            }
            
        except Exception as e:
            logger.error(f"❌ Error en debug_search: {e}")
            return {"error": str(e)}
    
    def process_rag_query(self, query: str, user_id: str) -> Dict[str, Any]:
        """Procesar consulta RAG completa con debugging mejorado"""
        try:
            logger.info(f"🔍 RAG Query: '{query}' de user: {user_id}")
            
            # Asegurar vectorstore
            if not self._ensure_vectorstore():
                logger.error("❌ Vectorstore no disponible")
                return {
                    "success": False,
                    "response": "La base de conocimiento no está disponible. Ejecuta la ingesta de documentos primero.",
                    "query_type": "rag"
                }
            
            # Log información del vectorstore
            doc_count = self.vectorstore._collection.count()
            logger.info(f"📊 ChromaDB tiene {doc_count} documentos")
            
            # Buscar documentos relevantes primero
            docs_with_scores = self.vectorstore.similarity_search_with_score(query, k=5)
            logger.info(f"📄 Documentos encontrados: {len(docs_with_scores)}")
            
            for i, (doc, score) in enumerate(docs_with_scores):
                logger.info(f"  Doc {i}: score={score:.4f}, source={doc.metadata.get('filename', 'unknown')}")
                logger.info(f"  Preview: {doc.page_content[:100]}...")
            
            # Si no hay documentos relevantes
            if not docs_with_scores:
                logger.warning("⚠️ No se encontraron documentos relevantes")
                return {
                    "success": True,
                    "response": f"No encontré información específica sobre '{query}' en los documentos financieros disponibles. Los documentos contienen información sobre estados financieros de Credibanco, pero no incluyen datos específicos relacionados con su consulta.",
                    "query_type": "rag",
                    "debug_info": {
                        "total_docs_in_db": doc_count,
                        "docs_found": 0
                    }
                }
            
            # Ejecutar consulta con el QA chain
            logger.info("🤖 Ejecutando QA chain...")
            result = self.qa_chain.run(query)
            
            # DEBUG Y FIX del resultado
            logger.info(f"🔍 DEBUG - result type: {type(result)}")
            logger.info(f"🔍 DEBUG - result content: {repr(result)[:300]}...")
            logger.info(f"🔍 DEBUG - result length: {len(str(result))}")
            
            # Asegurar que result es string limpio
            if hasattr(result, 'content'):
                final_result = result.content
            elif hasattr(result, 'text'):
                final_result = result.text
            else:
                final_result = str(result).strip()
            
            # Validar que tenemos una respuesta útil
            if not final_result or len(final_result.strip()) < 10:
                final_result = f"Encontré información relacionada con '{query}' en los documentos financieros, pero no pude generar una respuesta específica. Por favor, reformule su consulta con términos más específicos."
            
            logger.info(f"✅ Respuesta final: {len(final_result)} caracteres")
            logger.info(f"📝 Preview respuesta: {final_result[:200]}...")
            
            # Obtener fuentes
            sources = list(set([doc.metadata.get("filename", "unknown") for doc, _ in docs_with_scores]))
            
            # Guardar en memoria
            try:
                self.memory_manager.save_interaction(user_id, query, final_result)
            except Exception as e:
                logger.warning(f"⚠️ Error guardando en memoria: {e}")
            
            return {
                "success": True,
                "response": final_result,
                "sources": sources,
                "query_type": "rag",
                "debug_info": {
                    "total_docs_in_db": doc_count,
                    "docs_found": len(docs_with_scores),
                    "best_score": float(docs_with_scores[0][1]) if docs_with_scores else None,
                    "raw_result_length": len(str(result)),
                    "final_result_length": len(final_result)
                }
            }
            
        except Exception as e:
            logger.error(f"❌ Error en consulta RAG: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "response": "Error procesando consulta de conocimiento. Por favor, intente nuevamente.",
                "query_type": "rag"
            }
    
    def get_knowledge_stats(self) -> Dict[str, Any]:
        """Estadísticas detalladas de la base de conocimiento"""
        try:
            # Contar archivos en directorio
            docs_count = len(list(self.documents_path.glob("*.pdf"))) + \
                        len(list(self.documents_path.glob("*.txt"))) + \
                        len(list(self.documents_path.glob("*.md")))
            
            # Estado del vectorstore
            vectorstore_ready = hasattr(self, 'vectorstore') and self.vectorstore is not None
            chroma_exists = self.chroma_path.exists() and any(self.chroma_path.iterdir())
            
            # Información adicional si vectorstore está disponible
            vectorstore_info = {}
            if vectorstore_ready:
                try:
                    vectorstore_info = {
                        "documents_in_vectorstore": self.vectorstore._collection.count(),
                        "collection_name": self.collection_name
                    }
                except Exception as e:
                    vectorstore_info = {"error": str(e)}
            
            # Listar archivos disponibles
            available_files = []
            for ext in ['.pdf', '.txt', '.md']:
                files = list(self.documents_path.glob(f"*{ext}"))
                for file in files:
                    available_files.append({
                        "name": file.name,
                        "size": file.stat().st_size,
                        "type": ext
                    })
            
            return {
                "documents_folder": str(self.documents_path),
                "total_documents": docs_count,
                "available_files": available_files,
                "vectorstore_ready": vectorstore_ready,
                "chroma_db_exists": chroma_exists,
                "chroma_path": str(self.chroma_path),
                "embedding_model": "Google models/embedding-001",
                "supported_formats": [".pdf", ".txt", ".md"],
                "vectorstore_info": vectorstore_info,
                "prompt_template": "Custom Financial Analysis Prompt with Few-Shot Examples"
            }
            
        except Exception as e:
            logger.error(f"❌ Error obteniendo estadísticas: {e}")
            return {"error": str(e)}
    
    def reset_knowledge_base(self) -> Dict[str, Any]:
        """Resetear completamente la base de conocimiento"""
        try:
            import shutil
            
            # Eliminar ChromaDB
            if self.chroma_path.exists():
                shutil.rmtree(self.chroma_path)
                logger.info(f"🗑️ ChromaDB eliminado: {self.chroma_path}")
            
            # Limpiar variables
            self.vectorstore = None
            self.qa_chain = None
            
            # Recrear directorio
            self.chroma_path.mkdir(parents=True, exist_ok=True)
            
            return {
                "success": True,
                "message": "Base de conocimiento reseteada correctamente. Ejecuta /api/rag/ingest para cargar documentos nuevamente."
            }
            
        except Exception as e:
            logger.error(f"❌ Error reseteando base de conocimiento: {e}")
            return {"success": False, "error": str(e)}