"""
Threading module for handling API responses
"""

from core.config import QThread, pyqtSignal


class ModelResponseThread(QThread):
    response_chunk = pyqtSignal(str)
    response_finished = pyqtSignal(str)
    error_occurred = pyqtSignal(str)

    def __init__(self, ollama_client, model, prompt, model_params=None, system_message=None):
        super().__init__()
        self.ollama_client = ollama_client
        self.model = model
        self.prompt = prompt
        self.model_params = model_params or {}
        self.system_message = system_message

    def run(self):
        try:
            # Use the OllamaClient's generate_response method
            full_response = ""
            for chunk in self.ollama_client.generate_response(
                self.prompt,
                self.model,
                stream=True,
                system_message=self.system_message,
                model_params=self.model_params
            ):
                full_response += chunk
                self.response_chunk.emit(chunk)
            self.response_finished.emit(full_response)
        except Exception as e:
            self.error_occurred.emit(str(e))


class MultiProviderResponseThread(QThread):
    """Thread for handling multi-provider responses"""
    response_chunk = pyqtSignal(str)
    response_finished = pyqtSignal(str)
    error_occurred = pyqtSignal(str)

    def __init__(self, client, prompt, provider=None, model=None, system_message=None, model_params=None):
        super().__init__()
        self.client = client
        self.prompt = prompt
        self.provider = provider
        self.model = model
        self.system_message = system_message
        self.model_params = model_params or {}

    def run(self):
        try:
            full_response = ""
            for chunk in self.client.generate_response(
                self.prompt,
                provider_name=self.provider,
                model_name=self.model,
                system_message=self.system_message, 
                stream=True,
                model_params=self.model_params
            ):
                full_response += chunk
                self.response_chunk.emit(chunk)
            self.response_finished.emit(full_response)
        except Exception as e:
            self.error_occurred.emit(str(e))
