import customtkinter as ctk
from tkinter import filedialog
from converter import VideoConverter
from queue_manager import QueueManager, QueueItem
import os
import sys

class ConverterGUI(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        self.title("Conversor de Vídeo para MP4 (Lote)")
        self.geometry("700x550")
        self.resizable(False, False)
        
        # Load Window Icon
        if getattr(sys, 'frozen', False):
            base_dir = os.path.dirname(sys.executable)
        else:
            base_dir = os.path.dirname(os.path.abspath(__file__))
        icon_path = os.path.join(base_dir, "icon.ico")
        if os.path.exists(icon_path):
            try:
                self.iconbitmap(icon_path)
            except Exception:
                pass
        
        ctk.set_appearance_mode("System")
        ctk.set_default_color_theme("blue")
        
        self.converter = VideoConverter()
        self.queue_manager = QueueManager(self.converter)
        
        # Set up callbacks
        self.queue_manager.on_item_updated = self._on_item_updated
        self.queue_manager.on_queue_finished = self._on_queue_finished
        
        self.row_widgets = {}
        self.dest_folder = ctk.StringVar()
        self.same_folder_var = ctk.BooleanVar(value=True)
        
        self._build_ui()
        
    def _build_ui(self):
        main_frame = ctk.CTkFrame(self)
        main_frame.pack(pady=15, padx=15, fill="both", expand=True)
        
        # Top Frame: Output configuration
        out_frame = ctk.CTkFrame(main_frame)
        out_frame.pack(fill="x", padx=10, pady=(10, 5))
        
        self.chk_same_folder = ctk.CTkCheckBox(
            out_frame, 
            text="Salvar vídeos na mesma pasta dos arquivos originais", 
            variable=self.same_folder_var,
            command=self._toggle_dest_folder,
            font=("Arial", 11, "bold")
        )
        self.chk_same_folder.grid(row=0, column=0, columnspan=3, padx=10, pady=10, sticky="w")
        
        lbl_dest = ctk.CTkLabel(out_frame, text="Pasta de Destino:", font=("Arial", 11))
        lbl_dest.grid(row=1, column=0, padx=(10, 5), pady=(0, 10), sticky="e")
        
        self.entry_dest = ctk.CTkEntry(out_frame, textvariable=self.dest_folder, width=420, state="disabled")
        self.entry_dest.grid(row=1, column=1, padx=5, pady=(0, 10))
        
        self.btn_dest = ctk.CTkButton(out_frame, text="Selecionar", width=80, state="disabled", command=self._select_dest_folder)
        self.btn_dest.grid(row=1, column=2, padx=(5, 10), pady=(0, 10))
        
        # Middle Frame: Scrollable queue list
        self.scroll_frame = ctk.CTkScrollableFrame(main_frame, height=270, label_text="Fila de Conversão")
        self.scroll_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        # Bottom Frame: Status and Controls
        bottom_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        bottom_frame.pack(fill="x", padx=10, pady=(5, 10))
        
        self.lbl_status = ctk.CTkLabel(bottom_frame, text="Adicione arquivos para começar.", text_color="gray", font=("Arial", 11))
        self.lbl_status.pack(pady=5)
        
        btn_control_frame = ctk.CTkFrame(bottom_frame, fg_color="transparent")
        btn_control_frame.pack()
        
        self.btn_add = ctk.CTkButton(btn_control_frame, text="Adicionar Arquivos", command=self._add_files_to_queue)
        self.btn_add.grid(row=0, column=0, padx=10)
        
        self.btn_clear = ctk.CTkButton(btn_control_frame, text="Limpar Fila", fg_color="#7f8c8d", hover_color="#95a5a6", command=self._clear_all_queue)
        self.btn_clear.grid(row=0, column=1, padx=10)
        
        self.btn_convert = ctk.CTkButton(btn_control_frame, text="Converter", fg_color="#27ae60", hover_color="#2ecc71", command=self._start_queue_conversion)
        self.btn_convert.grid(row=0, column=2, padx=10)
        
        self.btn_download = ctk.CTkButton(main_frame, text="Baixar FFmpeg Automático (Necessário)", command=self._start_download, fg_color="#c0392b", hover_color="#e74c3c")
        self.btn_download.pack(pady=(5, 0))
        
        if self.converter.has_ffmpeg:
            self.btn_download.pack_forget()
        else:
            self.btn_convert.configure(state="disabled")
            self._show_error("Conversor indisponível (FFmpeg não encontrado).")
            
    def _toggle_dest_folder(self):
        if self.same_folder_var.get():
            self.entry_dest.configure(state="disabled")
            self.btn_dest.configure(state="disabled")
            self.dest_folder.set("")
        else:
            self.entry_dest.configure(state="normal")
            self.btn_dest.configure(state="normal")
            
    def _select_dest_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            self.dest_folder.set(folder)
            
    def _add_files_to_queue(self):
        files = filedialog.askopenfilenames(filetypes=[("Arquivos de Vídeo Suportados", "*.avi;*.dva;*.dav"), ("Todos os Arquivos", "*.*")])
        if not files:
            return
            
        added_count = 0
        for file_path in files:
            ext = os.path.splitext(file_path)[1].lower()
            if ext not in [".avi", ".dva", ".dav"]:
                continue
                
            # Avoid duplicate pending items
            is_dup = False
            for item in self.queue_manager.items:
                if item.input_path == file_path and item.status in ["Pendente", "Convertendo"]:
                    is_dup = True
                    break
            if is_dup:
                continue
                
            if self.same_folder_var.get():
                out_path = os.path.splitext(file_path)[0] + ".mp4"
            else:
                dest = self.dest_folder.get()
                if not dest:
                    dest = os.path.dirname(file_path)
                out_path = os.path.join(dest, os.path.basename(os.path.splitext(file_path)[0] + ".mp4"))
                
            item = self.queue_manager.add_item(file_path, out_path)
            self._create_queue_row(item)
            added_count += 1
            
        if added_count > 0:
            self.lbl_status.configure(text=f"{added_count} arquivo(s) adicionado(s) à fila.", text_color="gray")
            
    def _create_queue_row(self, item):
        row_frame = ctk.CTkFrame(self.scroll_frame, fg_color="transparent")
        row_frame.pack(fill="x", padx=5, pady=2)
        
        base_name = os.path.basename(item.input_path)
        lbl_name = ctk.CTkLabel(row_frame, text=base_name, font=("Arial", 11), anchor="w", width=250)
        lbl_name.pack(side="left", padx=5)
        
        lbl_prog = ctk.CTkLabel(row_frame, text="Pendente", font=("Arial", 10), text_color="gray", anchor="w")
        lbl_prog.pack(side="left", fill="x", expand=True, padx=5)
        
        lbl_status = ctk.CTkLabel(row_frame, text="Pendente", font=("Arial", 11, "bold"), text_color="gray", width=90, anchor="e")
        lbl_status.pack(side="right", padx=5)
        
        self.row_widgets[item.id] = {
            "frame": row_frame,
            "name_lbl": lbl_name,
            "prog_lbl": lbl_prog,
            "status_lbl": lbl_status
        }
        
    def _on_item_updated(self, item):
        self.after(0, lambda: self._update_row_ui(item))
        
    def _update_row_ui(self, item):
        widgets = self.row_widgets.get(item.id)
        if not widgets:
            return
            
        widgets["prog_lbl"].configure(text=item.progress_msg)
        widgets["status_lbl"].configure(text=item.status)
        
        if item.status == "Pendente":
            widgets["status_lbl"].configure(text_color="gray")
            widgets["prog_lbl"].configure(text_color="gray")
        elif item.status == "Convertendo":
            widgets["status_lbl"].configure(text_color="#d35400")
            widgets["prog_lbl"].configure(text_color="#d35400")
        elif item.status == "Concluído":
            widgets["status_lbl"].configure(text_color="#27ae60")
            widgets["prog_lbl"].configure(text_color="#27ae60")
        elif item.status == "Erro":
            widgets["status_lbl"].configure(text_color="#c0392b")
            widgets["prog_lbl"].configure(text_color="#c0392b")
            
    def _start_queue_conversion(self):
        if not self.converter.has_ffmpeg:
            self._show_error("FFmpeg não encontrado.")
            return
            
        # If currently running, acts as Cancel button
        if self.queue_manager.is_running:
            self._cancel_conversion()
            return
            
        has_pending = any(item.status == "Pendente" for item in self.queue_manager.items)
        if not has_pending:
            self._show_error("Não há arquivos pendentes na fila.")
            return
            
        self.btn_convert.configure(text="Parar", fg_color="#c0392b", hover_color="#e74c3c")
        self.btn_add.configure(state="disabled")
        self.btn_clear.configure(state="disabled")
        self.chk_same_folder.configure(state="disabled")
        self.btn_dest.configure(state="disabled")
        self.lbl_status.configure(text="Processando fila de conversão...", text_color="#d35400")
        
        # Apply output directory choices to pending items
        for item in self.queue_manager.items:
            if item.status == "Pendente":
                if self.same_folder_var.get():
                    item.output_path = os.path.splitext(item.input_path)[0] + ".mp4"
                else:
                    dest = self.dest_folder.get()
                    if dest:
                        item.output_path = os.path.join(dest, os.path.basename(os.path.splitext(item.input_path)[0] + ".mp4"))
                        
        self.queue_manager.start_conversion()
        
    def _cancel_conversion(self):
        self.queue_manager.is_running = False
        self.converter.cancel()
        
        for item in self.queue_manager.items:
            if item.status in ["Convertendo", "Pendente"]:
                item.status = "Erro"
                item.progress_msg = "Cancelado"
                self._update_row_ui(item)
                
        self._on_queue_finished()
        
    def _on_queue_finished(self):
        self.after(0, self._handle_queue_finished)
        
    def _handle_queue_finished(self):
        self.btn_convert.configure(text="Converter", fg_color="#27ae60", hover_color="#2ecc71")
        self.btn_add.configure(state="normal")
        self.btn_clear.configure(state="normal")
        self.chk_same_folder.configure(state="normal")
        self._toggle_dest_folder()
        
        has_errors = any(item.status == "Erro" for item in self.queue_manager.items)
        if has_errors:
            self.lbl_status.configure(text="Conversão finalizada com erros.", text_color="#c0392b")
        else:
            self.lbl_status.configure(text="Fila finalizada com sucesso!", text_color="#27ae60")
            
    def _clear_all_queue(self):
        if self.queue_manager.is_running:
            return
            
        self.queue_manager.clear_queue()
        for widgets in self.row_widgets.values():
            widgets["frame"].destroy()
        self.row_widgets.clear()
        self.lbl_status.configure(text="Fila limpa.", text_color="gray")
        
    def _show_error(self, msg):
        self.lbl_status.configure(text=msg[:120] + "..." if len(msg) > 120 else msg, text_color="#c0392b")
        
    def _start_download(self):
        self.btn_download.configure(state="disabled", text="Iniciando...")
        self.lbl_status.configure(text="Conectando...", text_color="#d35400")
        
        self.converter.download_ffmpeg(
            progress_callback=self._on_download_progress,
            completion_callback=self._on_download_complete,
            error_callback=self._on_download_error
        )
        
    def _on_download_progress(self, msg):
        self.after(0, lambda: self.lbl_status.configure(text=msg, text_color="#d35400"))
        
    def _on_download_complete(self):
        def _handle():
            self.converter._check_ffmpeg()
            if self.converter.has_ffmpeg:
                self.btn_download.pack_forget()
                self.btn_convert.configure(state="normal")
                self.lbl_status.configure(text="FFmpeg instalado com sucesso!", text_color="#27ae60")
            else:
                self._show_error("Falha ao configurar o FFmpeg após o download.")
                self.btn_download.configure(state="normal", text="Baixar FFmpeg Automático")
        self.after(0, _handle)
        
    def _on_download_error(self, err_msg):
        def _handle():
            self._show_error(f"Erro no download: {err_msg}")
            self.btn_download.configure(state="normal", text="Tentar Novamente")
        self.after(0, _handle)
