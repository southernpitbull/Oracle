"""
Knowledge Graph module for managing conversation context and relationships
"""

import os
from core.config import (NETWORKX_AVAILABLE, SENTENCE_TRANSFORMERS_AVAILABLE, 
                        nx, logger)

class KnowledgeGraph:
    def __init__(self, model_name='all-MiniLM-L6-v2'):
        if not NETWORKX_AVAILABLE or not SENTENCE_TRANSFORMERS_AVAILABLE:
            logger.warning("Dependencies not available for KnowledgeGraph, using simplified version")
            self.graph = {}  # Simple dict as fallback
            self.model = None
            self.node_counter = 0
            return
            
        try:
            from sentence_transformers import SentenceTransformer
            
            self.graph = nx.DiGraph()
            # Lazy load the model to prevent freezes during initialization
            self._model_name = model_name
            self.model = None
            self.node_counter = 0
        except Exception as e:
            logger.warning(f"Failed to initialize KnowledgeGraph with full features: {e}")
            self.graph = {}
            self.model = None
            self.node_counter = 0

    def _load_model(self):
        """Lazy load the sentence transformer model."""
        if self.model is None and SENTENCE_TRANSFORMERS_AVAILABLE:
            try:
                from sentence_transformers import SentenceTransformer
                self.model = SentenceTransformer(self._model_name)
            except Exception as e:
                logger.warning(f"Failed to load sentence transformer model: {e}")
                self.model = None

    def add_message(self, role, content, conversation_id):
        if not NETWORKX_AVAILABLE:
            # Simplified storage without graph
            node_id = self.node_counter
            self.node_counter += 1
            return node_id
            
        try:
            self._load_model()
            vector = self.model.encode(content) if self.model else None
            node_id = self.node_counter
            self.graph.add_node(node_id, role=role, content=content, vector=vector, conversation_id=conversation_id)
            
            # Find previous node in the same conversation and add an edge
            prev_nodes = [n for n, data in self.graph.nodes(data=True) if data.get('conversation_id') == conversation_id and n < node_id]
            if prev_nodes:
                prev_node = max(prev_nodes)
                self.graph.add_edge(prev_node, node_id)
                
            self.node_counter += 1
            return node_id
        except Exception as e:
            logger.warning(f"Failed to add message to knowledge graph: {e}")
            node_id = self.node_counter
            self.node_counter += 1
            return node_id

    def get_conversation_summary(self, conversation_id, num_messages=3):
        if not NETWORKX_AVAILABLE:
            return f"Conversation {conversation_id}"
            
        try:
            conv_nodes = [data['content'] for n, data in self.graph.nodes(data=True) 
                            if data.get('conversation_id') == conversation_id]
            # Simple summary: first 5 words of the first user message
            if conv_nodes:
                first_user_message = next((data['content'] for n, data in self.graph.nodes(data=True) 
                                         if data.get('conversation_id') == conversation_id and data.get('role') == 'user'), None)
                if first_user_message:
                    return " ".join(first_user_message.split()[:5])
            return f"Conversation {conversation_id}"
        except Exception as e:
            logger.warning(f"Failed to get conversation summary: {e}")
            return f"Conversation {conversation_id}"

    def save_graph(self, path="knowledge_graph.gml"):
        if not NETWORKX_AVAILABLE:
            logger.warning("Cannot save graph - networkx not available")
            return
            
        try:
            # Cannot save numpy arrays in gml, so convert to list with native Python types
            for n, data in self.graph.nodes(data=True):
                if 'vector' in data and data['vector'] is not None:
                    # Convert numpy array to list of native Python floats
                    data['vector'] = [float(x) for x in data['vector']]
            nx.write_gml(self.graph, path)
        except Exception as e:
            logger.warning(f"Failed to save graph: {e}")

    def load_graph(self, path="knowledge_graph.gml"):
        if not NETWORKX_AVAILABLE:
            logger.warning("Cannot load graph - networkx not available")
            return
            
        try:
            
            if os.path.exists(path):
                self.graph = nx.read_gml(path)
                # Convert vector lists back to numpy arrays
                for n, data in self.graph.nodes(data=True):
                    if 'vector' in data and data['vector'] is not None:
                        data['vector'] = np.array(data['vector'])
                self.node_counter = len(self.graph.nodes)
        except Exception as e:
            logger.warning(f"Failed to load graph: {e}")
