# Conversor de Vídeo (AVI/DVA para MP4)

Um aplicativo de desktop simples e elegante para converter arquivos de vídeo nos formatos `.avi` e `.dva` diretamente para o padrão `.mp4`, garantindo alta compatibilidade. 

Desenvolvido em Python com a moderna interface gráfica **CustomTkinter** e alimentado pelo poderoso motor **FFmpeg**.

---

## 🚀 Como Usar (Sem Instalar Nada)

A forma mais fácil de utilizar o conversor é baixando o arquivo executável pronto. Você não precisa instalar Python nem configurar dependências!

1. Acesse a aba de [Releases](https://github.com/pr-gabriel/Converter-AVI-DVA-para-MP4/releases) deste repositório.
2. Baixe o arquivo `Converter-AVI-MP4.exe` da versão mais recente.
3. Clique duas vezes no arquivo baixado para abri-lo (pode demorar alguns segundos na primeira execução).
4. Selecione seu vídeo de origem (`.avi` ou `.dva`).
5. Escolha onde salvar o novo `.mp4`.
6. Clique em **Converter** e aguarde a finalização!

---

## 🛠️ Detalhes Técnicos e Requisitos

### O FFmpeg
Para manter o executável extremamente leve (cerca de 20MB ao invés de 100MB+), optamos por não embutir o motor de conversão de vídeo dentro do arquivo.
O aplicativo **exige** que o `ffmpeg` esteja instalado no seu computador e adicionado às variáveis de ambiente (PATH).
Se ele não for detectado, o aplicativo irá avisá-lo e sugerir o download.

[Download oficial do FFmpeg](https://ffmpeg.org/download.html)

---

## 💻 Para Desenvolvedores (Como Compilar)

Caso queira fazer alterações no código e gerar o seu próprio executável, siga os passos abaixo:

### Pré-requisitos
- Python 3.10 ou superior.
- Git.

### Passos de Instalação e Compilação

1. Clone este repositório:
   ```bash
   git clone https://github.com/pr-gabriel/Converter-AVI-DVA-para-MP4.git
   cd Converter-AVI-MP4
   ```

2. Crie e ative um ambiente virtual:
   ```bash
   python -m venv .venv
   # No Windows:
   .venv\Scripts\activate
   ```

3. Instale as dependências:
   ```bash
   pip install -r requirements.txt
   pip install pyinstaller
   ```

4. Compile o executável:
   ```bash
   pyinstaller --noconfirm --onefile --windowed --add-data "ffmpeg;ffmpeg" --add-data ".venv\Lib\site-packages\customtkinter;customtkinter/" --icon="icon.ico" --name Converter-AVI-MP4 "main.py"
   ```

O arquivo final `.exe` será gerado na pasta `dist`.

---

## 📄 Licença

Este projeto é de código aberto e está disponível para modificações e estudos. Fique à vontade para contribuir!
