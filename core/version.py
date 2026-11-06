"""Versão do aplicativo e repositório usado para buscar atualizações.

Histórico (reconstruído a partir dos commits que alteraram o executável):
    1.0.0  - 0ad860a  Primeiro executável publicado
    1.0.1  - 8758ab3  Executável atualizado com a correção de erro
    1.1.0  - d88c869  Código modularizado, otimizações e prévia ajustada (executável atual no repositório)
    1.2.0  - Modo "Centralizar" (padrão), seletor aprimorado e atualização via GitHub Releases
    1.2.1  - Versão de teste do atualizador
    1.3.0  - Novo design Dark Glassmorphism, modal de notas da versão e seletor pílula
    1.3.1  - (atual)  Suporte a rolagem por Touchpad, abertura instantânea das notas e foco sempre à frente
"""

VERSION = "1.3.1"
GITHUB_REPO = "niellzinhow/OpenMug-Studio"

# Notas embutidas da versão atual (abertura instantânea e fallback caso o GitHub esteja instável)
RELEASE_NOTES = """## Novidades (v1.3.0)

- **Interface totalmente redesenhada (Dark Glassmorphism):** novo visual minimalista e fluido com papel de parede abstrato dinâmico, cards translúcidos com bordas sutis iluminadas e controles em formato de pílula.
- **Botão de Notas da Versão:** novo ícone no canto superior direito que abre um modal moderno com o histórico da versão atual e atalho direto para o repositório.
- **Nova Tela de Pré-visualização:** exibição da folha A4 com acabamento de borda e sombra sobre o fundo escuro, acompanhada de uma barra de ações inferior flutuante em formato de cápsula.

## Melhorias (v1.3.0)

- **Novo seletor de Modo de Encaixe:** botão em pílula contínua com menu suspenso flutuante arredondado, sem bordas brancas do sistema e com maior respiro entre as opções.
- **Miniaturas arredondadas:** pré-visualização das artes nos cards em proporção 16:9 com cantos suaves e realce ao passar o mouse.
- **Formatação limpa no atualizador:** os avisos de atualização agora exibem as notas formatadas e legíveis, sem símbolos brutos de Markdown.

## Correções e Ajustes (v1.3.1)

- **Rolagem via Touchpad:** suporte nativo a gestos de dois dedos em Precision Touchpad no modal de notas da versão (além da roda do mouse).
- **Abertura instantânea das Notas:** o modal agora abre na hora usando as notas embutidas da versão e sincroniza silenciosamente em segundo plano com o GitHub, evitando erros ou espera em oscilações da rede.
- **Janelas sempre em primeiro plano:** garantia de elevação e foco automático ao abrir o modal de notas da versão e a pré-visualização de impressão, evitando que abram atrás da janela principal.
"""
