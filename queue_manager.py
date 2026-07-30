import os
import threading
import uuid
from converter import VideoConverter

class QueueItem:
    def __init__(self, input_path: str, output_path: str):
        self.id = str(uuid.uuid4())
        self.input_path = input_path
        self.output_path = output_path
        self.status = "Pendente"
        self.progress_msg = "Pendente"

class QueueManager:
    def __init__(self, converter: VideoConverter):
        self.converter = converter
        self.items = []
        self.is_running = False
        self.current_index = -1
        self._lock = threading.Lock()
        
        # Callbacks
        self.on_item_updated = None
        self.on_queue_finished = None
        
    def add_item(self, input_path: str, output_path: str) -> QueueItem:
        with self._lock:
            item = QueueItem(input_path, output_path)
            self.items.append(item)
            return item
            
    def clear_queue(self):
        with self._lock:
            if self.is_running:
                return
            self.items.clear()
            self.current_index = -1
            
    def start_conversion(self):
        with self._lock:
            if self.is_running:
                return
            self.is_running = True
            
        thread = threading.Thread(target=self._process_queue)
        thread.daemon = True
        thread.start()
        
    def _process_queue(self):
        while True:
            item = None
            with self._lock:
                next_item = None
                for i, it in enumerate(self.items):
                    if it.status == "Pendente":
                        self.current_index = i
                        next_item = it
                        break
                
                if next_item is None or not self.is_running:
                    self.is_running = False
                    if self.on_queue_finished:
                        self.on_queue_finished()
                    break
                
                item = next_item
                item.status = "Convertendo"
                item.progress_msg = "Inicializando..."
                
            if self.on_item_updated:
                self.on_item_updated(item)
                
            event = threading.Event()
            
            def on_complete():
                item.status = "Concluído"
                item.progress_msg = "Concluído"
                event.set()
                
            def on_error(err_msg):
                item.status = "Erro"
                item.progress_msg = f"Erro: {err_msg}"
                event.set()
                
            def on_encoder(msg):
                item.progress_msg = msg
                if self.on_item_updated:
                    self.on_item_updated(item)
                    
            self.converter.convert(
                input_path=item.input_path,
                output_path=item.output_path,
                completion_callback=on_complete,
                error_callback=on_error,
                encoder_callback=on_encoder
            )
            
            event.wait()
            
            if self.on_item_updated:
                self.on_item_updated(item)
