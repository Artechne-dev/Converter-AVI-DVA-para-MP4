import customtkinter as ctk
from tkinter import filedialog, messagebox
from tkinterdnd2 import TkinterDnD, DND_FILES
from src.core.converter import VideoConverter
from src.core.queue_manager import QueueManager, QueueItem
from src.core.config import get_path
from src.core import history
import os
import sys
import winsound
import threading

try:
    from PIL import Image
    _PIL_AVAILABLE = True
except ImportError:
    _PIL_AVAILABLE = False

# winotify: toast notifications nativas do Windows — falha silenciosa em outros OS
try:
    from winotify import Notification, audio as winotify_audio
    _WINOTIFY_AVAILABLE = True
except ImportError:
    _WINOTIFY_AVAILABLE = False

# Columns in the gallery grid
_GALLERY_COLS = 6
# Thumbnail dimensions (16:9)
_THUMB_W, _THUMB_H = 168, 95


class ConverterGUI(ctk.CTk, TkinterDnD.DnDWrapper):
    def __init__(self):
        super().__init__()
        self.TkdndVersion = TkinterDnD._require(self)

        # ── Theme (must be set before any widget is created) ─────────────────
        self._theme_mode = "dark"
        ctk.set_appearance_mode("Dark")
        ctk.set_default_color_theme("blue")

        self.title("Conversor de Vídeo para MP4 (Lote) - v1.9")
        self.state("zoomed")
        self.minsize(900, 640)

        icon_path = get_path("icon.ico", use_meipass=False)
        if os.path.exists(icon_path):
            try:
                self.iconbitmap(icon_path)
            except Exception:
                pass

        self.converter = VideoConverter()
        self.queue_manager = QueueManager(self.converter)
        self.queue_manager.on_item_updated = self._on_item_updated
        self.queue_manager.on_queue_finished = self._on_queue_finished

        self.row_widgets: dict = {}
        self.dest_folder = ctk.StringVar()
        self.same_folder_var = ctk.BooleanVar(value=True)
        self.ultra_fast_var = ctk.BooleanVar(value=True)

        # Background conversion tracking
        self._queue_finished_in_bg = False
        self._app_focused = True
        self._pending_status: tuple = ()

        # Thumbnail image references (prevent garbage collection)
        self._thumbnail_cache: dict = {}

        self.drop_target_register(DND_FILES)
        self.dnd_bind("<<Drop>>", self._on_file_drop)

        import queue
        self.gui_queue = queue.Queue()
        self._poll_gui_queue()

        self._build_ui()
        self._bind_focus_events()

    # ── UI Construction ───────────────────────────────────────────────────────

    def _build_ui(self):
        main_frame = ctk.CTkFrame(self)
        main_frame.pack(pady=12, padx=12, fill="both", expand=True)

        # Top header bar (title + theme toggle)
        self._build_header(main_frame)

        # Conversion settings panel
        self._build_conversion_panel(main_frame)

        # Queue list
        self.scroll_frame = ctk.CTkScrollableFrame(
            main_frame, height=180,
            label_text="Fila de Conversão (Arraste e solte arquivos aqui)",
        )
        self.scroll_frame.pack(fill="x", padx=10, pady=4)

        # Status bar + controls
        self._build_controls(main_frame)

        # Separator
        ctk.CTkFrame(main_frame, height=2, fg_color=("gray70", "gray30")).pack(
            fill="x", padx=10, pady=(8, 0)
        )

        # Gallery
        self._build_gallery_panel(main_frame)

    def _build_header(self, parent):
        bar = ctk.CTkFrame(parent, fg_color="transparent")
        bar.pack(fill="x", padx=10, pady=(6, 2))

        ctk.CTkLabel(
            bar,
            text="Conversor de Vídeo para MP4",
            font=ctk.CTkFont(size=15, weight="bold"),
        ).pack(side="left")

        # Dark mode by default → show blue sun (click to switch to light)
        self.btn_theme = ctk.CTkButton(
            bar,
            text="☀",
            width=38, height=30,
            font=ctk.CTkFont(size=20),
            fg_color="#1a6faf",
            hover_color="#2185cc",
            text_color="white",
            command=self._toggle_theme,
        )
        self.btn_theme.pack(side="right")

    def _build_conversion_panel(self, parent):
        out_frame = ctk.CTkFrame(parent)
        out_frame.pack(fill="x", padx=10, pady=(4, 4))

        self.chk_same_folder = ctk.CTkCheckBox(
            out_frame,
            text="Salvar vídeos na mesma pasta dos arquivos originais",
            variable=self.same_folder_var,
            command=self._toggle_dest_folder,
            font=("Arial", 11, "bold"),
        )
        self.chk_same_folder.grid(row=0, column=0, columnspan=3, padx=10, pady=8, sticky="w")

        ctk.CTkLabel(out_frame, text="Pasta de Destino:", font=("Arial", 11)).grid(
            row=1, column=0, padx=(10, 5), pady=(0, 8), sticky="e"
        )
        self.entry_dest = ctk.CTkEntry(out_frame, textvariable=self.dest_folder, width=420, state="disabled")
        self.entry_dest.grid(row=1, column=1, padx=5, pady=(0, 8))
        self.btn_dest = ctk.CTkButton(
            out_frame, text="Selecionar", width=80, state="disabled",
            command=self._select_dest_folder,
        )
        self.btn_dest.grid(row=1, column=2, padx=(5, 10), pady=(0, 8))

        self.chk_ultra_fast = ctk.CTkCheckBox(
            out_frame,
            text="Ativar Cópia Direta Ultra Rápida (Copia streams sem reprocessar quando possível)",
            variable=self.ultra_fast_var,
            font=("Arial", 11, "bold"),
        )
        self.chk_ultra_fast.grid(row=2, column=0, columnspan=3, padx=10, pady=(0, 8), sticky="w")

        ctk.CTkLabel(out_frame, text="Acelerador de Vídeo:", font=("Arial", 11)).grid(
            row=3, column=0, padx=(10, 5), pady=(0, 8), sticky="e"
        )
        self.encoder_name_to_key = {v: k for k, v in self.converter.available_encoders.items()}
        encoder_options = list(self.converter.available_encoders.values()) if self.converter.available_encoders else ["CPU (Padrão)"]
        self.opt_encoder = ctk.CTkOptionMenu(out_frame, values=encoder_options, width=420)
        self.opt_encoder.grid(row=3, column=1, padx=5, pady=(0, 8), sticky="w")
        self.opt_encoder.set(encoder_options[0])

        ctk.CTkLabel(out_frame, text="Qualidade do Vídeo:", font=("Arial", 11)).grid(
            row=4, column=0, padx=(10, 5), pady=(0, 8), sticky="e"
        )
        self.quality_name_to_key = {
            "Alta (Qualidade Extra)": "high",
            "Média (Recomendada)": "medium",
            "Baixa (Arquivos Menores)": "low",
        }
        quality_options = list(self.quality_name_to_key.keys())
        self.opt_quality = ctk.CTkOptionMenu(out_frame, values=quality_options, width=420)
        self.opt_quality.grid(row=4, column=1, padx=5, pady=(0, 8), sticky="w")
        self.opt_quality.set("Média (Recomendada)")

    def _build_controls(self, parent):
        bottom = ctk.CTkFrame(parent, fg_color="transparent")
        bottom.pack(fill="x", padx=10, pady=(4, 6))

        self.lbl_status = ctk.CTkLabel(
            bottom,
            text="Adicione arquivos ou arraste-os para começar.",
            text_color="gray", font=("Arial", 11),
        )
        self.lbl_status.pack(pady=(4, 2))

        self.progress_bar = ctk.CTkProgressBar(bottom, width=500)
        self.progress_bar.pack(pady=(2, 4))
        self.progress_bar.set(0)

        btn_row = ctk.CTkFrame(bottom, fg_color="transparent")
        btn_row.pack()

        self.btn_add = ctk.CTkButton(btn_row, text="Adicionar Arquivos", width=120, command=self._add_files_to_queue)
        self.btn_add.grid(row=0, column=0, padx=5)

        self.btn_clear = ctk.CTkButton(btn_row, text="Limpar Fila", width=120, fg_color="#7f8c8d", hover_color="#95a5a6", command=self._clear_all_queue)
        self.btn_clear.grid(row=0, column=1, padx=5)

        self.btn_convert = ctk.CTkButton(btn_row, text="Converter", width=120, fg_color="#27ae60", hover_color="#2ecc71", command=self._start_queue_conversion)
        self.btn_convert.grid(row=0, column=2, padx=5)

        self.btn_open_folder = ctk.CTkButton(btn_row, text="Abrir Pasta", width=120, fg_color="#34495e", hover_color="#2c3e50", state="disabled", command=self._open_dest_folder)
        self.btn_open_folder.grid(row=0, column=3, padx=5)

        self.btn_download = ctk.CTkButton(
            parent, text="Baixar FFmpeg Automático (Necessário)",
            command=self._start_download, fg_color="#c0392b", hover_color="#e74c3c",
        )
        self.btn_download.pack(pady=(4, 0))

        if self.converter.has_ffmpeg:
            self.btn_download.pack_forget()
        else:
            self.btn_convert.configure(state="disabled")
            self._show_error("Conversor indisponível (FFmpeg não encontrado).")

    # ── Theme toggle ──────────────────────────────────────────────────────────

    def _toggle_theme(self):
        if self._theme_mode == "dark":
            self._theme_mode = "light"
            ctk.set_appearance_mode("Light")
            # Light mode active → show black moon to switch back to dark
            self.btn_theme.configure(
                text="🌙",
                fg_color="#2c3e50",
                hover_color="#34495e",
                text_color="white",
            )
        else:
            self._theme_mode = "dark"
            ctk.set_appearance_mode("Dark")
            # Dark mode active → show blue sun to switch to light
            self.btn_theme.configure(
                text="☀",
                fg_color="#1a6faf",
                hover_color="#2185cc",
                text_color="white",
            )

    # ── Focus / background detection ─────────────────────────────────────────

    def _bind_focus_events(self):
        self.bind("<FocusIn>", self._on_focus_in)
        self.bind("<FocusOut>", self._on_focus_out)

    def _on_focus_in(self, event=None):
        self._app_focused = True
        if self._queue_finished_in_bg:
            self._queue_finished_in_bg = False
            if self._pending_status:
                msg, color = self._pending_status
                self.lbl_status.configure(text=msg, text_color=color)

    def _on_focus_out(self, event=None):
        self._app_focused = False

    def _send_toast_notification(self, has_errors: bool, finished: int, total: int):
        if not _WINOTIFY_AVAILABLE:
            return
        try:
            icon_path = get_path("icon.ico", use_meipass=False)
            title = "Conversão concluída" if not has_errors else "Conversão finalizada com erros"
            msg = (
                f"{finished} de {total} arquivo(s) convertido(s) com sucesso!"
                if not has_errors
                else f"{finished} de {total} arquivo(s) processado(s). Verifique os erros."
            )
            toast = Notification(
                app_id="Conversor de Vídeo para MP4",
                title=title,
                msg=msg,
                icon=icon_path if os.path.exists(icon_path) else "",
                duration="short",
            )
            toast.set_audio(winotify_audio.Default, loop=False)
            toast.show()
        except Exception:
            pass

    # ── Queue (drag & drop / file picker) ────────────────────────────────────

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

    def _get_unique_output_path(self, out_path: str) -> str:
        existing = {item.output_path for item in self.queue_manager.items}
        if not os.path.exists(out_path) and out_path not in existing:
            return out_path
        base, ext = os.path.splitext(out_path)
        counter = 1
        while True:
            candidate = f"{base}_{counter}{ext}"
            if not os.path.exists(candidate) and candidate not in existing:
                return candidate
            counter += 1

    def _resolve_output(self, file_path: str) -> str:
        if self.same_folder_var.get():
            out = os.path.splitext(file_path)[0] + ".mp4"
        else:
            dest = self.dest_folder.get() or os.path.dirname(file_path)
            out = os.path.join(dest, os.path.basename(os.path.splitext(file_path)[0] + ".mp4"))
        return self._get_unique_output_path(out)

    def _on_file_drop(self, event):
        if self.queue_manager.is_running:
            return
        files = self.tk.splitlist(event.data)
        self._enqueue_files(files)

    def _add_files_to_queue(self):
        files = filedialog.askopenfilenames(
            filetypes=[("Arquivos de Vídeo Suportados", "*.avi;*.dva;*.dav"), ("Todos os Arquivos", "*.*")]
        )
        self._enqueue_files(files)

    def _enqueue_files(self, files):
        added = 0
        for file_path in files:
            if os.path.splitext(file_path)[1].lower() not in (".avi", ".dva", ".dav"):
                continue
            is_dup = any(
                item.input_path == file_path and item.status in ("Pendente", "Convertendo")
                for item in self.queue_manager.items
            )
            if is_dup:
                continue
            out_path = self._resolve_output(file_path)
            item = self.queue_manager.add_item(file_path, out_path)
            self._create_queue_row(item)
            added += 1
        if added:
            self.lbl_status.configure(text=f"{added} arquivo(s) adicionado(s) à fila.", text_color="gray")

    def _create_queue_row(self, item: QueueItem):
        row_frame = ctk.CTkFrame(self.scroll_frame, fg_color="transparent")
        row_frame.pack(fill="x", padx=5, pady=2)

        lbl_name = ctk.CTkLabel(row_frame, text=os.path.basename(item.input_path), font=("Arial", 11), anchor="w", width=250)
        lbl_name.pack(side="left", padx=5)
        lbl_prog = ctk.CTkLabel(row_frame, text="Pendente", font=("Arial", 10), text_color="gray", anchor="w")
        lbl_prog.pack(side="left", fill="x", expand=True, padx=5)
        lbl_status = ctk.CTkLabel(row_frame, text="Pendente", font=("Arial", 11, "bold"), text_color="gray", width=90, anchor="e")
        lbl_status.pack(side="right", padx=5)

        def on_row_click(event):
            current = next((it for it in self.queue_manager.items if it.id == item.id), None)
            if current and current.status == "Erro":
                messagebox.showerror("Detalhes do Erro", f"Arquivo: {os.path.basename(current.input_path)}\n\n{current.progress_msg}")

        for w in (row_frame, lbl_name, lbl_prog, lbl_status):
            w.bind("<Button-1>", on_row_click)

        self.row_widgets[item.id] = {"frame": row_frame, "name_lbl": lbl_name, "prog_lbl": lbl_prog, "status_lbl": lbl_status}

    def _on_item_updated(self, item: QueueItem):
        self.gui_queue.put(("item_updated", item))

    def _update_row_ui(self, item: QueueItem):
        widgets = self.row_widgets.get(item.id)
        if not widgets:
            return
        widgets["prog_lbl"].configure(text=item.progress_msg)
        widgets["status_lbl"].configure(text=item.status)
        color_map = {
            "Pendente": "gray",
            "Convertendo": "#d35400",
            "Concluído": "#27ae60",
            "Erro": "#c0392b",
        }
        color = color_map.get(item.status, "gray")
        widgets["status_lbl"].configure(text_color=color)
        widgets["prog_lbl"].configure(text_color=color)
        if item.status == "Erro":
            widgets["prog_lbl"].configure(text="Erro (Clique para detalhes)")
            for w in widgets.values():
                w.configure(cursor="hand2")
        else:
            for w in widgets.values():
                w.configure(cursor="")

    # ── Conversion control ────────────────────────────────────────────────────

    def _start_queue_conversion(self):
        if not self.converter.has_ffmpeg:
            self._show_error("FFmpeg não encontrado.")
            return
        if self.queue_manager.is_running:
            self._cancel_conversion()
            return
        if not any(item.status == "Pendente" for item in self.queue_manager.items):
            self._show_error("Não há arquivos pendentes na fila.")
            return

        self.btn_convert.configure(text="Parar", fg_color="#c0392b", hover_color="#e74c3c")
        self.btn_add.configure(state="disabled")
        self.btn_clear.configure(state="disabled")
        self.btn_open_folder.configure(state="disabled")
        self.chk_same_folder.configure(state="disabled")
        self.chk_ultra_fast.configure(state="disabled")
        self.btn_dest.configure(state="disabled")
        self.opt_encoder.configure(state="disabled")
        self.opt_quality.configure(state="disabled")
        self.lbl_status.configure(text="Processando fila de conversão...", text_color="#d35400")

        for item in self.queue_manager.items:
            if item.status == "Pendente":
                item.output_path = self._get_unique_output_path(self._resolve_output(item.input_path))

        self.queue_manager.start_conversion(
            ultra_fast=self.ultra_fast_var.get(),
            selected_encoder=self.encoder_name_to_key.get(self.opt_encoder.get(), "auto"),
            quality=self.quality_name_to_key.get(self.opt_quality.get(), "medium"),
        )

    def _cancel_conversion(self):
        self.queue_manager.is_running = False
        self.converter.cancel()
        for item in self.queue_manager.items:
            if item.status in ("Convertendo", "Pendente"):
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
                if msg[0] == "item_updated":
                    self._update_row_ui(msg[1])
                    self._update_overall_progress_ui()
                elif msg[0] == "queue_finished":
                    self._handle_queue_finished()
                self.gui_queue.task_done()
        except queue.Empty:
            pass
        self.after(50, self._poll_gui_queue)

    def _handle_queue_finished(self):
        self.btn_convert.configure(text="Converter", fg_color="#27ae60", hover_color="#2ecc71")
        self.btn_add.configure(state="normal")
        self.btn_clear.configure(state="normal")
        self.chk_same_folder.configure(state="normal")
        self.chk_ultra_fast.configure(state="normal")
        self.opt_encoder.configure(state="normal")
        self.opt_quality.configure(state="normal")
        self._toggle_dest_folder()
        self.progress_bar.set(1.0)

        finished, total, _, _, _ = self.queue_manager.get_overall_progress()
        has_completed = any(item.status == "Concluído" for item in self.queue_manager.items)
        if has_completed:
            self.btn_open_folder.configure(state="normal")

        # Persist each completed item to history
        for item in self.queue_manager.items:
            if item.status == "Concluído" and os.path.exists(item.output_path):
                history.add_to_history(item.input_path, item.output_path)

        has_errors = any(item.status == "Erro" for item in self.queue_manager.items)
        status_msg = (
            f"Conversão finalizada. {finished} de {total} processados." if has_errors
            else "Fila finalizada com sucesso!"
        )
        status_color = "#c0392b" if has_errors else "#27ae60"

        # Refresh gallery with newly converted files
        self._refresh_gallery()

        if self._app_focused:
            threading.Thread(
                target=lambda: (winsound.MessageBeep(winsound.MB_ICONASTERISK),),
                daemon=True,
            ).start()
            self.lbl_status.configure(text=status_msg, text_color=status_color)
        else:
            # App is in background: send toast, defer status update to FocusIn
            self._send_toast_notification(has_errors, finished, total)
            self._queue_finished_in_bg = True
            self._pending_status = (status_msg, status_color)

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
            completed = next((it for it in self.queue_manager.items if it.status == "Concluído"), None)
            if completed:
                folder = os.path.dirname(completed.output_path)
        if folder and os.path.exists(folder):
            try:
                os.startfile(folder)
            except Exception as e:
                messagebox.showerror("Erro", f"Não foi possível abrir a pasta:\n{e}")
        else:
            messagebox.showwarning("Aviso", "Pasta de destino não encontrada ou vazia.")

    def _update_overall_progress_ui(self):
        finished, total, _, percent, eta = self.queue_manager.get_overall_progress()
        if total == 0:
            self.progress_bar.set(0)
            self.lbl_status.configure(text="Adicione arquivos ou arraste-os para começar.", text_color="gray")
            return
        self.progress_bar.set(percent / 100.0)
        eta_text = ""
        if eta > 0:
            eta_text = f" (Restam {eta // 60:02d}:{eta % 60:02d})"
        if self.queue_manager.is_running:
            self.lbl_status.configure(
                text=f"Progresso Geral: {percent:.1f}%{eta_text} | Processado {finished} de {total} arquivo(s)",
                text_color="#d35400",
            )

    def _show_error(self, msg: str):
        display = msg[:120] + "..." if len(msg) > 120 else msg
        self.lbl_status.configure(text=display, text_color="#c0392b")

    # ── FFmpeg download ───────────────────────────────────────────────────────

    def _start_download(self):
        self.btn_download.configure(state="disabled", text="Iniciando...")
        self.lbl_status.configure(text="Conectando...", text_color="#d35400")
        self.converter.download_ffmpeg(
            progress_callback=self._on_download_progress,
            completion_callback=self._on_download_complete,
            error_callback=self._on_download_error,
        )

    def _on_download_progress(self, msg: str):
        self.after(0, lambda: self.lbl_status.configure(text=msg, text_color="#d35400"))

    def _on_download_complete(self):
        def _handle():
            self.converter._check_ffmpeg()
            if self.converter.has_ffmpeg:
                self.btn_download.pack_forget()
                self.btn_convert.configure(state="normal")
                self.lbl_status.configure(text="FFmpeg instalado com sucesso!", text_color="#27ae60")
                self.converter._detect_encoders()
                self.encoder_name_to_key = {v: k for k, v in self.converter.available_encoders.items()}
                encoder_options = list(self.converter.available_encoders.values())
                self.opt_encoder.configure(values=encoder_options)
                self.opt_encoder.set(encoder_options[0])
            else:
                self._show_error("Falha ao configurar o FFmpeg após o download.")
                self.btn_download.configure(state="normal", text="Baixar FFmpeg Automático")
        self.after(0, _handle)

    def _on_download_error(self, err_msg: str):
        def _handle():
            self._show_error(f"Erro no download: {err_msg}")
            self.btn_download.configure(state="normal", text="Tentar Novamente")
        self.after(0, _handle)

    # ── Gallery — grid view (Windows Explorer style) ──────────────────────────

    def _build_gallery_panel(self, parent):
        panel = ctk.CTkFrame(parent, fg_color="transparent")
        panel.pack(fill="both", expand=True, padx=10, pady=(8, 0))

        # Header row
        hdr = ctk.CTkFrame(panel, fg_color="transparent")
        hdr.pack(fill="x", pady=(0, 4))

        ctk.CTkLabel(
            hdr, text="Histórico de Conversões",
            font=ctk.CTkFont(size=13, weight="bold"),
        ).pack(side="left")

        ctk.CTkButton(
            hdr, text="↺ Atualizar", width=90, height=26,
            command=self._refresh_gallery,
        ).pack(side="right")

        ctk.CTkButton(
            hdr, text="🗑 Limpar Histórico", width=130, height=26,
            fg_color=("gray60", "gray40"), hover_color=("gray50", "gray30"),
            command=self._clear_gallery_history,
        ).pack(side="right", padx=(0, 6))

        # Grid scrollable area
        self.gallery_scroll = ctk.CTkScrollableFrame(
            panel, label_text="", fg_color=("gray92", "gray15"),
        )
        self.gallery_scroll.pack(fill="both", expand=True)

        # Make all columns uniform width
        for c in range(_GALLERY_COLS):
            self.gallery_scroll.columnconfigure(c, weight=1, uniform="col")

        self._refresh_gallery()

    def _refresh_gallery(self):
        """Reloads the gallery grid from the persisted history JSON."""
        for widget in self.gallery_scroll.winfo_children():
            widget.destroy()
        self._thumbnail_cache.clear()

        entries = history.load_history()

        if not entries:
            ctk.CTkLabel(
                self.gallery_scroll,
                text="Nenhum vídeo convertido ainda.\nOs arquivos aparecem aqui após a conversão.",
                text_color="gray",
                font=ctk.CTkFont(size=12),
                justify="center",
            ).grid(row=0, column=0, columnspan=_GALLERY_COLS, pady=40)
            return

        for idx, entry in enumerate(entries):
            self._create_video_card(entry, row=idx // _GALLERY_COLS, col=idx % _GALLERY_COLS)

    def _create_video_card(self, entry: dict, row: int, col: int):
        output_path = entry.get("output_path", "")
        filename = os.path.basename(output_path)
        file_exists = os.path.exists(output_path)

        # Outer card frame
        card = ctk.CTkFrame(self.gallery_scroll, corner_radius=8)
        card.grid(row=row, column=col, padx=6, pady=8, sticky="n")

        # ── Thumbnail ─────────────────────────────────────────────────────────
        bg_color = "#2a2a2a" if self._theme_mode == "dark" else "#d0d0d8"
        # Canvas acts as the thumbnail container with a fixed size
        thumb_frame = ctk.CTkFrame(card, width=_THUMB_W + 4, height=_THUMB_H + 4,
                                   fg_color=bg_color, corner_radius=4)
        thumb_frame.pack(padx=6, pady=(6, 3))
        thumb_frame.pack_propagate(False)

        thumb_lbl = ctk.CTkLabel(thumb_frame, text="🎬", font=ctk.CTkFont(size=28),
                                  width=_THUMB_W, height=_THUMB_H)
        thumb_lbl.pack(expand=True)

        # ── Filename ──────────────────────────────────────────────────────────
        # Truncate long names, show tooltip-style on card hover (title attribute)
        display = (filename[:20] + "…") if len(filename) > 20 else filename
        name_lbl = ctk.CTkLabel(
            card, text=display,
            font=ctk.CTkFont(size=11, weight="bold"),
            wraplength=_THUMB_W,
            justify="center",
            width=_THUMB_W + 4,
        )
        name_lbl.pack(padx=6, pady=(0, 2))

        # ── Size / warning ────────────────────────────────────────────────────
        if file_exists:
            sub_text = self._format_file_size(output_path)
            sub_color = ("gray40", "gray70")
        else:
            sub_text = "⚠ Não encontrado"
            sub_color = "#c0392b"

        ctk.CTkLabel(
            card, text=sub_text,
            font=ctk.CTkFont(size=10), text_color=sub_color, justify="center",
        ).pack(padx=6, pady=(0, 4))

        # ── Action buttons ────────────────────────────────────────────────────
        btn_row = ctk.CTkFrame(card, fg_color="transparent")
        btn_row.pack(padx=6, pady=(0, 6))

        ctk.CTkButton(
            btn_row, text="▶", width=42, height=22, font=ctk.CTkFont(size=12),
            fg_color="#2980b9" if file_exists else ("gray60", "gray40"),
            hover_color="#3498db" if file_exists else ("gray50", "gray30"),
            state="normal" if file_exists else "disabled",
            command=lambda p=output_path: os.startfile(p),
        ).pack(side="left", padx=(0, 2))

        folder_dir = os.path.dirname(output_path)
        ctk.CTkButton(
            btn_row, text="📁", width=42, height=22, font=ctk.CTkFont(size=12),
            fg_color=("gray60", "gray40"), hover_color=("gray50", "gray30"),
            state="normal" if os.path.isdir(folder_dir) else "disabled",
            command=lambda p=folder_dir: os.startfile(p) if os.path.isdir(p) else None,
        ).pack(side="left", padx=(0, 2))

        ctk.CTkButton(
            btn_row, text="✕", width=32, height=22, font=ctk.CTkFont(size=11),
            fg_color="#922b21", hover_color="#c0392b",
            command=lambda p=output_path: self._remove_history_entry(p),
        ).pack(side="left")

        # ── Double-click → play ───────────────────────────────────────────────
        if file_exists:
            for w in (card, thumb_frame, thumb_lbl, name_lbl):
                w.bind("<Double-Button-1>", lambda e, p=output_path: os.startfile(p))

        # ── Async thumbnail generation ────────────────────────────────────────
        if file_exists and _PIL_AVAILABLE:
            threading.Thread(
                target=self._load_thumbnail_async,
                args=(output_path, thumb_lbl),
                daemon=True,
            ).start()

    def _load_thumbnail_async(self, video_path: str, label: ctk.CTkLabel):
        """Background thread: generates (if needed) and loads the thumbnail."""
        thumb_path = history.get_thumbnail_path(video_path)
        if not os.path.exists(thumb_path):
            self._extract_thumbnail(video_path, thumb_path)
        if not os.path.exists(thumb_path):
            return
        try:
            img = Image.open(thumb_path).resize((_THUMB_W, _THUMB_H), Image.LANCZOS)
            ctk_img = ctk.CTkImage(light_image=img, dark_image=img, size=(_THUMB_W, _THUMB_H))
            # Keep a strong reference so Python doesn't GC the image
            self._thumbnail_cache[video_path] = ctk_img
            self.after(0, lambda: label.configure(image=ctk_img, text="") if label.winfo_exists() else None)
        except Exception:
            pass

    def _extract_thumbnail(self, video_path: str, output_path: str):
        """Calls FFmpeg to extract a single frame 3 seconds into the video."""
        if not self.converter.has_ffmpeg:
            return
        try:
            import subprocess
            subprocess.run(
                [
                    self.converter.ffmpeg_path, "-y",
                    "-ss", "00:00:03",
                    "-i", video_path,
                    "-vframes", "1",
                    "-vf", f"scale={_THUMB_W * 2}:{_THUMB_H * 2}:force_original_aspect_ratio=decrease,"
                           f"pad={_THUMB_W * 2}:{_THUMB_H * 2}:(ow-iw)/2:(oh-ih)/2",
                    "-q:v", "3",
                    output_path,
                ],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
                timeout=15,
            )
        except Exception:
            pass

    def _remove_history_entry(self, output_path: str):
        history.remove_from_history(output_path)
        self._refresh_gallery()

    def _clear_gallery_history(self):
        if messagebox.askyesno(
            "Limpar Histórico",
            "Remover todos os itens do histórico?\n(Os arquivos MP4 não serão excluídos.)",
        ):
            history.clear_history()
            self._refresh_gallery()

    @staticmethod
    def _format_file_size(path: str) -> str:
        try:
            size = os.path.getsize(path)
            for unit in ("B", "KB", "MB", "GB"):
                if size < 1024:
                    return f"{size:.1f} {unit}"
                size /= 1024
            return f"{size:.1f} TB"
        except OSError:
            return "—"
