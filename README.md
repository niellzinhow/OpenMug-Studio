<div align="center">
  <img src="OpenMug%20Studio.ico" width="128" alt="OpenMug Studio Icon">
  
  # ☕ OpenMug Studio
  
  **A solução elegante e minimalista para montagem e impressão de estampas de canecas com perfis de cor!**
  
  [![Versão](https://img.shields.io/badge/Versão-1.3.4-0A84FF.svg)](https://github.com/niellzinhow/OpenMug-Studio/releases/latest)
  [![Python](https://img.shields.io/badge/Python-3.10+-3776AB.svg?style=flat&logo=python&logoColor=white)](https://www.python.org/)
  [![CustomTkinter](https://img.shields.io/badge/GUI-CustomTkinter-0A84FF.svg?style=flat)](https://github.com/TomSchimansky/CustomTkinter)
  [![PyInstaller](https://img.shields.io/badge/Compilado_com-PyInstaller-FFD43B.svg?style=flat&logo=python&logoColor=black)](https://pyinstaller.org/)
  
</div>

---

## 🎨 O que é o OpenMug Studio?

O **OpenMug Studio** é um aplicativo desktop projetado para facilitar o fluxo de trabalho de quem produz canecas por sublimação. Com uma interface moderna em estilo **Dark Glassmorphism** — papel de parede abstrato dinâmico, cards translúcidos e controles em formato de pílula —, ele resolve de forma simples a montagem das estampas e a **conversão precisa de perfis de cor (ICC/ICM)** antes da impressão.

Organize até **3 artes** para canecas padrão (325 ml) em uma única folha A4 a **300 DPI**, aplique o perfil de cor da sua tinta (opcional), visualize o resultado na hora e exporte um PDF pronto para imprimir com economia de papel e fidelidade de cores.

---

## ✨ Funcionalidades

- 🎛️ **Aplicação de Perfil ICC (Opcional):** Carregue perfis `.icc` ou `.icm` (como o perfil incluso na pasta `ICM/`) para cores precisas na sua impressora sublimática, ou limpe a seleção com um clique quando quiser exportar sem conversão.
- 📐 **Montagem Automática em A4 (300 DPI):** Posiciona de 1 a 3 artes (`2362 × 1122 px`, ~20 cm de largura com margens seguras) perfeitamente espaçadas em uma folha A4 (`2480 × 3508 px`).
- 🖼️ **3 Modos de Encaixe por Arte:**
  - **Centralizar *(padrão)*:** Ajusta a imagem à altura da caneca mantendo a proporção original e centraliza horizontalmente na folha.
  - **Cortar:** Preenche toda a área da caneca preservando a proporção e cortando o excesso pelo centro.
  - **Redimensionar:** Ajusta a largura e a altura para cobrir exatamente a área da caneca.
- 👁️‍🗨️ **Pré-visualização A4 Refinada:** Confira a folha montada com acabamento realista sobre fundo escuro e controles em cápsula flutuante.
- 💾 **Exportação em PDF:** Gere e abra imediatamente no seu leitor padrão (`Gerar PDF`) ou escolha onde guardar o arquivo (`Salvar PDF`).
- 🔄 **Atualização Automática via GitHub Releases:** O programa verifica novas versões ao iniciar (ou pelo botão `Buscar atualizações`), baixa o novo executável com verificação de integridade (SHA-256) e reinicia atualizado automaticamente.
- 📄 **Notas da Versão Integradas:** Botão dedicado no canto superior direito para consultar o histórico de novidades diretamente no app.
- 🚀 **Executável Standalone:** Não requer instalação de Python para o usuário final — basta baixar na aba [Releases](https://github.com/niellzinhow/OpenMug-Studio/releases/latest) e abrir.

---

## 📖 Como Usar

1. **Abra o OpenMug Studio.**
2. **Selecione seu Perfil ICC *(opcional)*:** No card superior, clique em `🔍 Procurar Perfil ICC` e escolha o arquivo `.icc` ou `.icm` da sua tinta sublimática. A escolha fica salva automaticamente para os próximos usos.
3. **Adicione suas Artes:**
   - Em **Arte 1**, **Arte 2** e **Arte 3**, clique em `Escolher Imagem` e selecione os arquivos (`PNG`, `JPG`, `TIFF`, `BMP`).
   - *Dica:* Use `⧉ Duplicar` para copiar rapidamente a mesma arte e seu modo de encaixe para outro espaço livre, ou `🗑 Limpar Tudo` na barra inferior para recomeçar.
4. **Escolha o Modo de Encaixe:** No menu em pílula à direita de cada card, escolha entre **Centralizar** *(padrão)*, **Cortar** ou **Redimensionar**.
5. **Gere a Prévia:** Clique em `Gerar Prévia` na barra inferior.
6. **Exporte para Impressão:** Na tela de prévia, clique em `Gerar PDF` (abre direto no leitor padrão do sistema) ou em `Salvar PDF` (escolhe a pasta de destino).

> ⚠️ **Lembrete de Impressão:** No diálogo da sua impressora (ex.: Epson), configure **Papel Apresentação Premium Fosco**, marque **Sem Ajuste de Cor** (quando o perfil ICC já tiver sido aplicado pelo programa) e ative **Espelhar Imagem**.

---

## 🗂️ Estrutura do Projeto

```text
OpenMug Studio/
├── core/
│   ├── config_manager.py    # Persistência do perfil ICC e pasta temporária
│   ├── image_processor.py   # Montagem A4 (300 DPI), modos de encaixe e perfil ICC
│   ├── updater.py           # Verificação, download e auto-atualização via GitHub Releases
│   └── version.py           # Versão atual, repositório e notas da versão embutidas
├── gui/
│   ├── app.py               # Janela principal e modal de notas da versão
│   ├── background.py        # Papel de parede dinâmico e efeito translúcido (glass)
│   ├── preview_window.py    # Janela de pré-visualização da folha A4 e exportação PDF
│   └── theme.py             # Sistema de design (paleta, tipografia e componentes pílula)
├── ICM/                     # Perfis de cor de referência (.icm)
├── main.py                  # Ponto de entrada da aplicação
├── OpenMug Studio.spec      # Configuração de empacotamento do PyInstaller
└── requirements.txt         # Dependências Python
```

---

## 🛠️ Executando e Compilando pelo Código-Fonte (Para Devs)

1. Clone o repositório:
   ```bash
   git clone https://github.com/niellzinhow/OpenMug-Studio.git
   cd "OpenMug-Studio"
   ```
2. Instale as dependências:
   ```bash
   pip install -r requirements.txt
   ```
3. Execute o programa em modo de desenvolvimento:
   ```bash
   python main.py
   ```
4. Para gerar o executável único (`dist/OpenMug Studio.exe`) com o PyInstaller:
   ```powershell
   python -m pip install pyinstaller
   python -m PyInstaller "OpenMug Studio.spec" --noconfirm
   ```

---

<div align="center">
  <p>Feito com ❤️ para tornar a sublimação mais prática e precisa — <strong>OpenMug Studio v1.3.4</strong></p>
</div>
