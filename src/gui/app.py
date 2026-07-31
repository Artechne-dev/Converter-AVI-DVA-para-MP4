import customtkinter as ctk
from tkinter import filedialog, messagebox
from src.core.converter import VideoConverter
from src.core.queue_manager import QueueManager, QueueItem
from src.core.config import get_path
import os
import sys
import winsound

class ConverterGUI(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        self.title("Conversor de Vídeo para MP4 (Lote) - v1.3")
        self.geometry("750x600")
        self.resizable(False, False)
        
        # Load Window Icon
        icon_path = get_path("icon.ico", use_meipass=False)
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
        self.ultra_fast_var = ctk.BooleanVar(value=True)
        
        import queue
        self.gui_queue = queue.Queue()
        self._poll_gui_queue()
        
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
        
        self.chk_ultra_fast = ctk.CTkCheckBox(
            out_frame,
            text="Ativar Cópia Direta Ultra Rápida (Copia streams sem reprocessar quando possível)",
            variable=self.ultra_fast_var,
            font=("Arial", 11, "bold")
        )
        self.chk_ultra_fast.grid(row=2, column=0, columnspan=3, padx=10, pady=(0, 10), sticky="w")
        
        # Middle Frame: Scrollable queue list
        self.scroll_frame = ctk.CTkScrollableFrame(main_frame, height=250, label_text="Fila de Conversão")
        self.scroll_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        # Bottom Frame: Status and Controls
        bottom_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        bottom_frame.pack(fill="x", padx=10, pady=(5, 10))
        
        self.lbl_status = ctk.CTkLabel(bottom_frame, text="Adicione arquivos para começar.", text_color="gray", font=("Arial", 11))
        self.lbl_status.pack(pady=(5, 2))
        
        self.progress_bar = ctk.CTkProgressBar(bottom_frame, width=500)
        self.progress_bar.pack(pady=(2, 5))
        self.progress_bar.set(0)
        
        btn_control_frame = ctk.CTkFrame(bottom_frame, fg_color="transparent")
        btn_control_frame.pack()
        
        self.btn_add = ctk.CTkButton(btn_control_frame, text="Adicionar Arquivos", width=120, command=self._add_files_to_queue)
        self.btn_add.grid(row=0, column=0, padx=5)
        
        self.btn_clear = ctk.CTkButton(btn_control_frame, text="Limpar Fila", width=120, fg_color="#7f8c8d", hover_color="#95a5a6", command=self._clear_all_queue)
        self.btn_clear.grid(row=0, column=1, padx=5)
        
        self.btn_convert = ctk.CTkButton(btn_control_frame, text="Converter", width=120, fg_color="#27ae60", hover_color="#2ecc71", command=self._start_queue_conversion)
        self.btn_convert.grid(row=0, column=2, padx=5)
        
        self.btn_open_folder = ctk.CTkButton(btn_control_frame, text="Abrir Pasta", width=120, fg_color="#34495e", hover_color="#2c3e50", state="disabled", command=self._open_dest_folder)
        self.btn_open_folder.grid(row=0, column=3, padx=5)
        
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
            
    def _get_unique_output_path(self, out_path):
        existing_paths = {item.output_path for item in self.queue_manager.items}
        if not os.path.exists(out_path) and out_path not in existing_paths:
            return out_path
            
        base, ext = os.path.splitext(out_path)
        counter = 1
        while True:
            new_path = f"{base}_{counter}{ext}"
            if not os.path.exists(new_path) and new_path not in existing_paths:
                return new_path
            counter += 1
            
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
                
            # Auto-rename duplicate target files to avoid silent overwriting
            out_path = self._get_unique_output_path(out_path)
            
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
        
        # Click handler to show error message
        def on_row_click(event):
            current_item = next((it for it in self.queue_manager.items if it.id == item.id), None)
            if current_item and current_item.status == "Erro":
                messagebox.showerror(
                    "Detalhes do Erro",
                    f"Arquivo: {os.path.basename(current_item.input_path)}\n\n{current_item.progress_msg}"
                )
                
        row_frame.bind("<Button-1>", on_row_click)
        lbl_name.bind("<Button-1>", on_row_click)
        lbl_prog.bind("<Button-1>", on_row_click)
        lbl_status.bind("<Button-1>", on_row_click)
        
        self.row_widgets[item.id] = {
            "frame": row_frame,
            "name_lbl": lbl_name,
            "prog_lbl": lbl_prog,
            "status_lbl": lbl_status
        }
        
    def _on_item_updated(self, item):
        self.gui_queue.put(("item_updated", item))
        
    def _update_row_ui(self, item):
        widgets = self.row_widgets.get(item.id)
        if not widgets:
            return
            
        widgets["prog_lbl"].configure(text=item.progress_msg)
        widgets["status_lbl"].configure(text=item.status)
        
        if item.status == "Pendente":
            widgets["status_lbl"].configure(text_color="gray")
            widgets["prog_lbl"].configure(text_color="gray")
            for w in ["frame", "name_lbl", "prog_lbl", "status_lbl"]:
                widgets[w].configure(cursor="")
        elif item.status == "Convertendo":
            widgets["status_lbl"].configure(text_color="#d35400")
            widgets["prog_lbl"].configure(text_color="#d35400")
            for w in ["frame", "name_lbl", "prog_lbl", "status_lbl"]:
                widgets[w].configure(cursor="")
        elif item.status == "Concluído":
            widgets["status_lbl"].configure(text_color="#27ae60")
            widgets["prog_lbl"].configure(text_color="#27ae60")
            for w in ["frame", "name_lbl", "prog_lbl", "status_lbl"]:
                widgets[w].configure(cursor="")
        elif item.status == "Erro":
            widgets["status_lbl"].configure(text_color="#c0392b")
            widgets["prog_lbl"].configure(text="Erro (Clique para detalhes)", text_color="#c0392b")
            for w in ["frame", "name_lbl", "prog_lbl", "status_lbl"]:
                widgets[w].configure(cursor="hand2")
            
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
        self.btn_open_folder.configure(state="disabled")
        self.chk_same_folder.configure(state="disabled")
        self.chk_ultra_fast.configure(state="disabled")
        self.btn_dest.configure(state="disabled")
        self.lbl_status.configure(text="Processando fila de conversão...", text_color="#d35400")
        
        # Apply output directory choices to pending items
        for item in self.queue_manager.items:
            if item.status == "Pendente":
                if self.same_folder_var.get():
                    out_path = os.path.splitext(item.input_path)[0] + ".mp4"
                else:
                    dest = self.dest_folder.get()
                    if not dest:
                        dest = os.path.dirname(item.input_path)
                    out_path = os.path.join(dest, os.path.basename(os.path.splitext(item.input_path)[0] + ".mp4"))
                
                # Check conflict renaming again
                item.output_path = self._get_unique_output_path(out_path)
                        
        self.queue_manager.start_conversion(ultra_fast=self.ultra_fast_var.get())
        
    def _cancel_conversion(self):
        self.queue_manager.is_running = False
        self.converter.cancel()
        
        for item in self.queue_manager.items:
            if item.status in ["Convertendo", "Pendente"]:
                item.status = "Erro"
                item.progress_msg = "Cancelado pelo usuário"
                self._update_row_ui(item)
                
        self._on_queue_finished()
        
    def _on_queue_finished(self):
        self.gui_queue.put(("queue_finished",))
        
    def _poll_gui_queue(self):
        import queue
        try:
            while True:
                msg = self.gui_queue.get_nowait()
                msg_type = msg[0]
                
                if msg_type == "item_updated":
                    item = msg[1]
                    self._update_row_ui(item)
                    self._update_overall_progress_ui()
                elif msg_type == "queue_finished":
                    self._handle_queue_finished()
                    
                self.gui_queue.task_done()
        except queue.Empty:
            pass
            
        # Re-schedule polling every 50ms
        self.after(50, self._poll_gui_queue)
        
    def _handle_queue_finished(self):
        self.btn_convert.configure(text="Converter", fg_color="#27ae60", hover_color="#2ecc71")
        self.btn_add.configure(state="normal")
        self.btn_clear.configure(state="normal")
        self.chk_same_folder.configure(state="normal")
        self.chk_ultra_fast.configure(state="normal")
        self._toggle_dest_folder()
        
        self.progress_bar.set(1.0)
        finished, total, _, _, _ = self.queue_manager.get_overall_progress()
        
        # Enable open folder button if there is at least one finished file
        has_completed = any(item.status == "Concluído" for item in self.queue_manager.items)
        if has_completed:
            self.btn_open_folder.configure(state="normal")
            
        # Play Windows notification sound in background thread to prevent GUI hangs
        import threading
        def play_beep():
            try:
                winsound.MessageBeep(winsound.MB_ICONASTERISK)
            except Exception:
                pass
        threading.Thread(target=play_beep, daemon=True).start()
            
        has_errors = any(item.status == "Erro" for item in self.queue_manager.items)
        if has_errors:
            self.lbl_status.configure(text=f"Conversão finalizada. {finished} de {total} processados.", text_color="#c0392b")
        else:
            self.lbl_status.configure(text="Fila finalizada com sucesso!", text_color="#27ae60")
            
    def _clear_all_queue(self):
        if self.queue_manager.is_running:
            return
            
        self.queue_manager.clear_queue()
        for widgets in self.row_widgets.values():
            widgets["frame"].destroy()
        self.row_widgets.clear()
        self.progress_bar.set(0)
        self.btn_open_folder.configure(state="disabled")
        self.lbl_status.configure(text="Fila limpa.", text_color="gray")
        
    def _open_dest_folder(self):
        folder = None
        if not self.same_folder_var.get():
            folder = self.dest_folder.get()
            
        if not folder or not os.path.exists(folder):
            # Fallback to the folder of the first completed file
            completed_item = next((it for it in self.queue_manager.items if it.status == "Concluído"), None)
            if completed_item:
                folder = os.path.dirname(completed_item.output_path)
                
        if folder and os.path.exists(folder):
            try:
                os.startfile(folder)
            except Exception as e:
                messagebox.showerror("Erro", f"Não foi possível abrir a pasta:\n{str(e)}")
        else:
            messagebox.showwarning("Aviso", "Pasta de destino não encontrada ou vazia.")
            
    def _update_overall_progress_ui(self):
        finished, total, _, percent, eta = self.queue_manager.get_overall_progress()
        if total == 0:
            self.progress_bar.set(0)
            self.lbl_status.configure(text="Adicione arquivos para começar.", text_color="gray")
            return
            
        self.progress_bar.set(percent / 100.0)
        
        if eta > 0:
            eta_min = eta // 60
            eta_sec = eta % 60
            eta_str = f"{eta_min:02d}:{eta_sec:02d}"
            eta_text = f" (Restam {eta_str})"
        else:
            eta_text = ""
            
        if self.queue_manager.is_running:
            self.lbl_status.configure(
                text=f"Progresso Geral: {percent:.1f}%{eta_text} | Processado {finished} de {total} arquivo(s)",
                text_color="#d35400"
            )
        
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
