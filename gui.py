import customtkinter as ctk
from tkinter import filedialog
from converter import VideoConverter
import os

class ConverterGUI(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        self.title("Conversor de Vídeo para MP4")
        self.geometry("550x350")
        self.resizable(False, False)
        
        import sys
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
        
        self.input_file = ctk.StringVar()
        self.output_file = ctk.StringVar()
        
        self.converter = VideoConverter()

        self._build_ui()
        
    def _build_ui(self):
        main_frame = ctk.CTkFrame(self)
        main_frame.pack(pady=20, padx=20, fill="both", expand=True)
        
        lbl_input = ctk.CTkLabel(main_frame, text="Arquivo de Vídeo de Origem:", font=("Arial", 12, "bold"))
        lbl_input.grid(row=0, column=0, padx=10, pady=(10, 5), sticky="w")
        
        entry_input = ctk.CTkEntry(main_frame, textvariable=self.input_file, width=350, state="disabled")
        entry_input.grid(row=1, column=0, padx=10, pady=5)
        
        btn_input = ctk.CTkButton(main_frame, text="Buscar", width=80, command=self._select_input)
        btn_input.grid(row=1, column=1, padx=10, pady=5)
        
        lbl_output = ctk.CTkLabel(main_frame, text="Salvar como (MP4):", font=("Arial", 12, "bold"))
        lbl_output.grid(row=2, column=0, padx=10, pady=(15, 5), sticky="w")
        
        entry_output = ctk.CTkEntry(main_frame, textvariable=self.output_file, width=350, state="disabled")
        entry_output.grid(row=3, column=0, padx=10, pady=5)
        
        btn_output = ctk.CTkButton(main_frame, text="Buscar", width=80, command=self._select_output)
        btn_output.grid(row=3, column=1, padx=10, pady=5)
        
        self.lbl_status = ctk.CTkLabel(main_frame, text="", text_color="gray")
        self.lbl_status.grid(row=4, column=0, columnspan=2, pady=(10, 5))
        
        self.btn_convert = ctk.CTkButton(main_frame, text="Converter", command=self._start_conversion, fg_color="#27ae60", hover_color="#2ecc71")
        self.btn_convert.grid(row=5, column=0, columnspan=2, pady=(5, 10))

        self.btn_download = ctk.CTkButton(main_frame, text="Baixar FFmpeg Automático (Necessário)", command=self._start_download, fg_color="#c0392b", hover_color="#e74c3c")
        self.btn_download.grid(row=6, column=0, columnspan=2, pady=(0, 10))

        if self.converter.has_ffmpeg:
            self.btn_download.grid_remove()
        else:
            self.btn_convert.configure(state="disabled")
            self._show_error("Conversor indisponível (FFmpeg não encontrado).")

    def _select_input(self):
        file_path = filedialog.askopenfilename(filetypes=[("Arquivos de Vídeo Suportados", "*.avi;*.dva;*.dav"), ("Todos os Arquivos", "*.*")])
        if file_path:
            ext = os.path.splitext(file_path)[1].lower()
            if ext not in [".avi", ".dva", ".dav"]:
                self._show_error("Formato inválido. Selecione apenas arquivos .avi, .dva ou .dav.")
                self.input_file.set("")
                self.output_file.set("")
                return
                
            self.input_file.set(file_path)
            suggested_out = os.path.splitext(file_path)[0] + ".mp4"
            self.output_file.set(suggested_out)
            self.lbl_status.configure(text="Pronto para converter.", text_color="gray")

    def _select_output(self):
        file_path = filedialog.asksaveasfilename(defaultextension=".mp4", filetypes=[("Arquivos MP4", "*.mp4")])
        if file_path:
            self.output_file.set(file_path)

    def _start_conversion(self):
        if not self.converter.has_ffmpeg:
            self._show_error("Conversor indisponível (FFmpeg não encontrado).")
            return
            
        in_path = self.input_file.get()
        out_path = self.output_file.get()
        
        if not in_path or not out_path:
            self._show_error("Selecione os arquivos de entrada e saída.")
            return

        if in_path.lower().endswith(".mp4") and out_path.lower().endswith(".mp4"):
            self._show_error("Arquivo de origem já é MP4. Conversão redundante bloqueada.")
            return

        if os.path.abspath(in_path) == os.path.abspath(out_path):
            self._show_error("Arquivo de origem e destino não podem ser iguais.")
            return

        self.btn_convert.configure(state="disabled", text="Convertendo...")
        self.lbl_status.configure(text="Conversão em andamento... Aguarde.", text_color="#d35400")

        self.converter.convert(
            input_path=in_path,
            output_path=out_path,
            completion_callback=self._on_conversion_complete,
            error_callback=self._on_conversion_error,
            encoder_callback=self._on_encoder_status
        )

    def _on_encoder_status(self, msg):
        self.after(0, lambda: self.lbl_status.configure(text=msg, text_color="#d35400"))

    def _on_conversion_complete(self):
        self.after(0, self._handle_complete)
        
    def _handle_complete(self):
        self.btn_convert.configure(state="normal", text="Converter")
        self.lbl_status.configure(text="Conversão concluída com sucesso!", text_color="#27ae60")
        
    def _on_conversion_error(self, err_msg):
        self.after(0, lambda: self._show_error(f"Erro: {err_msg}"))
        
    def _show_error(self, msg):
        if hasattr(self, 'btn_convert') and self.converter.has_ffmpeg:
            self.btn_convert.configure(state="normal", text="Converter")
        if hasattr(self, 'lbl_status'):
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
            self.converter._check_ffmpeg() # Re-check
            if self.converter.has_ffmpeg:
                self.btn_download.grid_remove()
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
