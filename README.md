<div align="center">
  <img src="OpenMug%20Studio.ico" width="128" alt="OpenMug Studio Icon">
  
  # ☕ OpenMug Studio
  
  **A solução definitiva e elegante para impressão de estampas de canecas com perfis de cor!**
  
  [![Versão](https://img.shields.io/badge/Versão-1.0-blue.svg)](https://github.com/niellzinhow/OpenMug-Studio)
  [![Python](https://img.shields.io/badge/Python-3.x-3776AB.svg?style=flat&logo=python&logoColor=white)](https://www.python.org/)
  [![CustomTkinter](https://img.shields.io/badge/GUI-CustomTkinter-005b9f.svg?style=flat)](https://github.com/TomSchimansky/CustomTkinter)
  [![PyInstaller](https://img.shields.io/badge/Compilado_com-PyInstaller-FFD43B.svg?style=flat&logo=python&logoColor=black)](https://pyinstaller.org/)
  
</div>

---

## 🎨 O que é o OpenMug Studio?

O **OpenMug Studio** é um aplicativo desktop projetado para facilitar a vida de profissionais que trabalham com sublimação de canecas. Com uma interface linda e moderna no estilo *Midnight CMYK* (Dark Mode), ele resolve o maior problema da sublimação: **a conversão e aplicação precisa de perfis de cor (ICC)** antes da impressão.

Ele permite organizar facilmente até **3 artes** para canecas padrão (325 ml) em uma única folha A4, redimensionando automaticamente na medida perfeita, aplicando o perfil de cor da sua tinta e gerando um PDF pronto para a impressão, tudo isso garantindo economia de papel e cores fiéis!

---

## ✨ Funcionalidades

- 🎛️ **Aplicação de Perfil ICC:** Suporte completo para carregar perfis `.icc` ou `.icm` para cores 100% precisas na sua impressora sublimática.
- 📐 **Montagem Automática em A4:** Encaixa de 1 a 3 artes (tamanho padrão de canecas de 325 ml) em uma única folha A4 em alta resolução (300 DPI).
- 🖼️ **Modos de Encaixe:** Escolha entre *Cortar* (mantém a proporção centralizando a arte) ou *Redimensionar* (estica para cobrir a área exata).
- 👁️‍🗨️ **Visualização (Preview) Realista:** Veja como sua folha A4 ficará antes de imprimir.
- 💾 **Geração de PDF:** O programa sempre exportará o seu trabalho como um arquivo PDF pronto para a impressão (a impressão direta na impressora ainda não está disponível pelo programa).
- 🚀 **Pronto para uso:** Não requer instalação, basta baixar o executável (versão Standalone).

---

## 📖 Tutorial: Como Usar

O uso do OpenMug Studio é focado em praticidade. Siga os passos abaixo:

1. **Abra o programa.**
2. **Selecione seu Perfil ICC:** No topo da tela, clique em `Procurar Perfil ICC` e escolha o arquivo fornecido pelo fabricante da sua tinta sublimática.
3. **Adicione suas Artes:**
   - Nos blocos de "Arte 1", "Arte 2" e "Arte 3", clique em `Escolher Imagem`.
   - Selecione as imagens da sua caneca (PNG, JPG, etc).
   - *Dica:* Você pode duplicar uma arte rapidamente clicando no botão `⧉ Duplicar`!
4. **Ajuste o Modo de Encaixe:** Para cada arte, selecione se deseja *Cortar* ou *Redimensionar*.
5. **Gere a Prévia:** Clique no botão azul gigante na parte inferior: `Gerar Prévia`.
6. **Imprima ou Salve:** Na tela de visualização, você pode clicar em `Salvar PDF` para guardar o arquivo, ou em `Gerar PDF` para abrir automaticamente o PDF gerado no seu leitor padrão, de onde você fará a impressão. *(Nota: A impressão não é feita diretamente pelo programa, ele gera o PDF para garantir a qualidade final).*

> ⚠️ **Lembrete de Impressão:** Ao imprimir, certifique-se de configurar a sua impressora (ex: Epson) para "Papel Apresentação Premium Fosco", marcar a opção "Sem Ajuste de Cor" (já que o programa aplicou o perfil) e ativar "Espelhar Imagem".

---

## 📦 O Executável (Versão 1.0)

Para tornar a experiência a mais amigável possível, o OpenMug Studio é distribuído como um **Executável Único** (Standalone) para Windows. Isso significa que você não precisa instalar o Python, nem lidar com códigos se não quiser. É só baixar os arquivos na aba *Releases* e usar!

### Como o executável foi feito?
Utilizamos a ferramenta poderosa chamada **PyInstaller**. Ela empacota todo o código Python, juntamente com o CustomTkinter, a biblioteca Pillow (para edição de imagem) e os arquivos necessários (como ícones), em um único arquivo `.exe`. 

O comando básico utilizado para gerar a build (configurado no arquivo `.spec` incluso no repositório) foi:
```bash
pyinstaller --noconfirm --windowed --icon "OpenMug Studio.ico" main.py
```
Isso garante que ao abrir o programa não apareça nenhuma tela preta (console) no fundo, entregando uma experiência 100% profissional ao usuário.

---

## 🛠️ Como rodar a partir do código-fonte (Para Devs)

Se você é um desenvolvedor e quer modificar o OpenMug Studio:

1. Clone o repositório:
   ```bash
   git clone https://github.com/niellzinhow/OpenMug-Studio.git
   ```
2. Instale as dependências:
   ```bash
   pip install customtkinter Pillow
   ```
3. Execute o programa:
   ```bash
   python main.py
   ```

---

<div align="center">
  <p>Feito com ❤️ e muita criatividade. Aproveite a Versão 1.0!</p>
</div>
