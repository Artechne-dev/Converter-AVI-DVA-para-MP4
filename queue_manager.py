import os
import threading
import uuid
import time
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
        self.queue_start_time = 0.0
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
            self.queue_start_time = time.time()
            
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
            
            encoder_cache = ["Detectando..."]
            
            def on_complete():
                item.status = "Concluído"
                item.progress_msg = "Concluído"
                event.set()
                
            def on_error(err_msg):
                item.status = "Erro"
                item.progress_msg = f"Erro: {err_msg}"
                event.set()
                
            def on_encoder(msg):
                encoder_cache[0] = msg
                item.progress_msg = msg
                if self.on_item_updated:
                    self.on_item_updated(item)
                    
            def on_progress(msg):
                item.progress_msg = f"{encoder_cache[0]} | {msg}"
                if self.on_item_updated:
                    self.on_item_updated(item)
                    
            self.converter.convert(
                input_path=item.input_path,
                output_path=item.output_path,
                completion_callback=on_complete,
                error_callback=on_error,
                encoder_callback=on_encoder,
                progress_callback=on_progress
            )
            
            event.wait()
            
            if self.on_item_updated:
                self.on_item_updated(item)

    def get_overall_progress(self):
        with self._lock:
            total = len(self.items)
            if total == 0:
                return 0, 0, 0.0, 0.0, 0
                
            completed = sum(1 for it in self.items if it.status == "Concluído")
            failed = sum(1 for it in self.items if it.status == "Erro")
            
            active_fraction = 0.0
            active_item = next((it for it in self.items if it.status == "Convertendo"), None)
            if active_item and active_item.progress_msg:
                import re
                match = re.search(r"(\d+\.\d+)%", active_item.progress_msg)
                if match:
                    active_fraction = float(match.group(1)) / 100.0
            
            processed = completed + failed + active_fraction
            overall_percent = (processed / total) * 100.0
            
            eta = 0
            if processed > 0.01 and self.is_running:
                elapsed = time.time() - self.queue_start_time
                eta = (elapsed / processed) * (total - processed)
                
            return completed + failed, total, processed, overall_percent, int(eta)
