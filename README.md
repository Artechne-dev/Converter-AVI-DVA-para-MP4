# Conversor de Vídeo (AVI/DVA/DAV para MP4)

Um aplicativo de desktop moderno, rápido e elegante para converter arquivos de vídeo nos formatos `.avi`, `.dva` e `.dav` diretamente para o padrão `.mp4`, garantindo alta compatibilidade.

Desenvolvido em Python com a moderna interface gráfica **CustomTkinter** e alimentado pelo poderoso motor **FFmpeg**.

---

## 🚀 Como Usar (Sem Instalar Nada)

A forma mais fácil de utilizar o conversor é baixando o arquivo executável pronto. Você não precisa instalar Python nem configurar dependências!

1. Acesse a aba de [Releases](https://github.com/pr-gabriel/Converter-AVI-DVA-para-MP4/releases) deste repositório.
2. Baixe o arquivo `Converter-AVI-MP4.exe` da versão mais recente.
3. Clique duas vezes no arquivo baixado para abri-lo (pode demorar alguns segundos na primeira execução).
4. Adicione um ou mais vídeos de origem (`.avi`, `.dva` ou `.dav`) à fila de conversão.
5. Configure o destino (salvar na mesma pasta ou selecionar uma pasta específica).
6. Escolha se deseja habilitar a **Cópia Direta Ultra Rápida** (copia os streams de vídeo diretamente sem re-codificar se o formato for compatível).
7. Clique em **Converter** e acompanhe o progresso de cada arquivo e da fila geral.
8. Ao finalizar, o conversor emitirá um aviso sonoro e habilitará o botão **Abrir Pasta** para acessar os arquivos gerados.

---

## 🛠️ Detalhes Técnicos e Requisitos

### O FFmpeg
O aplicativo utiliza o **FFmpeg** como motor de conversão de vídeo.
- **Detecção automática:** O aplicativo tenta detectar o FFmpeg no PATH do sistema ou na pasta raiz do aplicativo.
- **Download automático:** Se o FFmpeg não for encontrado, a interface exibirá um botão vermelho **Baixar FFmpeg Automático**. Clique nele para que o aplicativo baixe, extraia e configure o FFmpeg localmente de forma 100% automatizada.

---

## 💻 Para Desenvolvedores

Caso queira fazer alterações no código, estudar ou gerar o seu próprio executável, siga os passos abaixo:

### Estrutura do Projeto

O código é organizado seguindo boas práticas de desenvolvimento de pacotes em Python:
```
Converter-AVI-DVA-para-MP4/
├── main.py                 # Ponto de entrada do aplicativo
├── icon.ico                # Ícone do aplicativo
├── Converter-AVI-MP4.spec  # Arquivo de especificação para PyInstaller
└── src/
    ├── __init__.py
    ├── core/
    │   ├── __init__.py
    │   ├── config.py       # Resolução dinâmica de caminhos (local e frozen)
    │   ├── converter.py    # Motor de execução do FFmpeg e Watchdog de processos
    │   └── queue_manager.py # Fila multithreaded de conversão de arquivos
    └── gui/
        ├── __init__.py
        └── app.py          # Interface gráfica construída em CustomTkinter
```

### Pré-requisitos
- Python 3.10 ou superior.
- Git.

### Passos de Instalação e Compilação

1. Clone este repositório:
   ```bash
   git clone https://github.com/pr-gabriel/Converter-AVI-DVA-para-MP4.git
   cd Converter-AVI-DVA-para-MP4
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

4. Compile o executável usando o arquivo `.spec` configurado:
   ```bash
   pyinstaller Converter-AVI-MP4.spec
   ```

O arquivo final `.exe` com o ícone embutido e suporte a CustomTkinter será gerado na pasta `dist/`.

---

## 📄 Licença

Este projeto é de código aberto e está disponível sob a licença MIT para modificações e estudos. Fique à vontade para contribuir!
