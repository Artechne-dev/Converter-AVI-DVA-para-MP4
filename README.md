# Conversor de Vídeo (AVI/DVA/DAV para MP4)
Um aplicativo de desktop moderno, rápido e seguro para converter arquivos de vídeo de CFTV e DVRs (`.avi`, `.dva` e `.dav`) diretamente para o padrão universal `.mp4`, garantindo alta compatibilidade.
Desenvolvido em Python com a moderna interface gráfica **CustomTkinter** e alimentado pelo poderoso motor **FFmpeg** com suporte a aceleração de hardware nativa.
---
## ✨ Principais Funcionalidades (v2.0)
* 🎨 **Interface Moderna e Temas:** UI responsiva e maximizada, com alternância instantânea entre Modo Escuro e Claro (☽/☀).
* ⚡ **Aceleração por Hardware:** Detecta e utiliza automaticamente as placas de vídeo NVIDIA (NVENC), Intel (QSV) ou AMD (AMF) para conversões extremamente rápidas.
* 🎥 **Galeria em Grade (Estilo Windows Explorer):** Visualize rapidamente os vídeos convertidos em formato de galeria, com extração assíncrona de miniaturas e informações de tamanho do arquivo.
* 📋 **Histórico Portátil:** Histórico persistente de conversões gravado ao lado do EXE. Mantenha seu histórico seguro sem precisar instalar o software no Windows.
* 🔔 **Notificações de 2º Plano:** Conversão finalizada com a janela minimizada? O aplicativo envia uma notificação "Toast" nativa do Windows 10/11 avisando a conclusão.
* 🛡️ **Hardening e Segurança:** Validação estrita de extensões contra injeções, proteção contra ataques de Path Traversal de pastas e checagens de permissão de escrita em disco.
* 🏢 **Integração Intelbras:** Um prático botão de preenchimento rápido injeta instantaneamente o caminho padrão de gravação Intelbras SIMNext (`C:\ProgramData\Intelbras\SIMNext\Recording`).
* 🖱️ **Drag and Drop:** Arraste e solte dezenas de arquivos direto do Windows Explorer para dentro da fila.
---
## 🚀 Como Usar (Sem Instalar Nada)
A forma mais fácil de utilizar o conversor é baixando o arquivo executável pronto. Você não precisa instalar Python, bibliotecas e nem ter direitos de administrador!
1. Acesse a aba de [Releases](https://github.com/pr-gabriel/Converter-AVI-DVA-para-MP4/releases) deste repositório.
2. Baixe o arquivo `Converter-AVI-MP4.exe` da versão mais recente.
3. Clique duas vezes no arquivo baixado para abri-lo (pode demorar alguns segundos na primeira execução).
4. Adicione vídeos arrastando e soltando na tela, ou pelo botão "Adicionar Arquivos".
5. Configure o destino: marque para salvar na mesma pasta, escolha uma pasta específica, ou clique no **atalho da Intelbras** para preenchimento rápido.
6. Escolha se deseja habilitar a **Cópia Direta Ultra Rápida** (copia os streams de vídeo diretamente sem re-codificar se o formato original permitir).
7. Clique em **Converter** e acompanhe o progresso geral e por arquivo. Você pode minimizar a janela e será notificado pelo Windows ao finalizar!
8. Dê duplo clique em qualquer miniatura na **Galeria de Vídeos** para abri-la no seu player padrão.
---
## 🛠️ Detalhes Técnicos e Requisitos
### O FFmpeg
O aplicativo utiliza o **FFmpeg** como motor de conversão de vídeo assíncrono.
- **Detecção automática:** Tenta detectar o FFmpeg no PATH do sistema ou na pasta raiz do aplicativo.
- **Download automático:** Se o FFmpeg não for encontrado, a interface exibirá um botão vermelho **Baixar FFmpeg Automático**. Clique nele para baixar, extrair e configurar o FFmpeg de forma 100% automatizada direto do repositório oficial (BtbN).
---
## 💻 Para Desenvolvedores
Caso queira fazer alterações no código, estudar ou gerar o seu próprio executável, siga os passos abaixo:
### Estrutura do Projeto
O código é organizado seguindo boas práticas de desenvolvimento orientado a pacotes (Python):
Converter-AVI-DVA-para-MP4/ ├── main.py # Ponto de entrada (Bootstrapper) ├── icon.ico # Ícone em múltiplas resoluções ├── requirements.txt # Dependências do projeto ├── Converter-AVI-MP4.spec # Specs PyInstaller contendo hooks collect_all (winotify, tkinterdnd2, PIL) └── src/ ├── init.py ├── core/ │ ├── init.py │ ├── config.py # Resolução dinâmica de paths absolutos e temp (MEIPASS) │ ├── converter.py # Motor multithread de FFmpeg, hardware detection e cancelamentos │ ├── queue_manager.py # Regras de negócios, status, e progresso de fila global │ └── history.py # Gestão de I/O para persistência JSON do histórico e cache MD5 └── gui/ ├── init.py └── app.py # View e Controller — UI em CustomTkinter

### Pré-requisitos
- Python 3.10 ou superior
- Git
### Passos de Instalação e Compilação
1. Clone este repositório:
   ```bash
   git clone https://github.com/pr-gabriel/Converter-AVI-DVA-para-MP4.git
   cd Converter-AVI-DVA-para-MP4
Crie e ative um ambiente virtual:

bash
python -m venv .venv
# No Windows:
.venv\Scripts\activate
Instale as dependências. Note que o tkinterdnd2 requer acesso de build se não for instalado via wheel pré-compilado:

bash
pip install --upgrade pip
pip install -r requirements.txt
Compile o executável através do arquivo de spec que resolve as injeções estáticas das DLLs e assets:

bash
pyinstaller --clean Converter-AVI-MP4.spec
O arquivo final .exe standalone será gerado e comprimido na pasta dist/.

📄 Licença
Este projeto é de código aberto e está disponível sob a licença MIT para modificações e estudos. Fique à vontade para contribuir!
