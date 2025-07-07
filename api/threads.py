"""
Threading module for handling API responses
"""

from core.config import QThread, pyqtSignal


class ModelResponseThread(QThread):
    response_chunk = pyqtSignal(str)
    response_finished = pyqtSignal(str)
    error_occurred = pyqtSignal(str)

    def __init__(self, ollama_client, model, prompt):
        super().__init__()
        self.ollama_client = ollama_client
        self.model = model
        self.prompt = prompt

    def run(self):
        try:
            response = self.ollama_client.generate(model=self.model, prompt=self.prompt, stream=True)
            full_response = ""
            for chunk in response:
                token = chunk.get('response') or chunk.get('message') or chunk.get('content') or ''
                if token:
                    full_response += token
                    self.response_chunk.emit(token)
            self.response_finished.emit(full_response)
        except Exception as e:
            self.error_occurred.emit(str(e))


class MultiProviderResponseThread(QThread):
    """Thread for handling multi-provider responses"""
    response_chunk = pyqtSignal(str)
    response_finished = pyqtSignal(str)
    error_occurred = pyqtSignal(str)

    def __init__(self, client, prompt, system_message=None):
        super().__init__()
        self.client = client
        self.prompt = prompt
        self.system_message = system_message

    def run(self):
        try:
            full_response = ""
            for chunk in self.client.generate_response(self.prompt, system_message=self.system_message, stream=True):
                full_response += chunk
                self.response_chunk.emit(chunk)
            self.response_finished.emit(full_response)
        except Exception as e:
            self.error_occurred.emit(str(e))
