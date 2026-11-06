"""Versão do aplicativo e repositório usado para buscar atualizações.

Histórico (reconstruído a partir dos commits que alteraram o executável):
    1.0.0  - 0ad860a  Primeiro executável publicado
    1.0.1  - 8758ab3  Executável atualizado com a correção de erro
    1.1.0  - d88c869  Código modularizado, otimizações e prévia ajustada (executável atual no repositório)
    1.2.0  - Modo "Centralizar" (padrão), seletor aprimorado e atualização via GitHub Releases
    1.2.1  - Versão de teste do atualizador
    1.3.0  - Novo design Dark Glassmorphism, modal de notas da versão e seletor pílula
    1.3.1  - Suporte a rolagem por Touchpad, abertura instantânea das notas e foco sempre à frente
    1.3.2  - (atual)  Novo modal de atualização com texto completo rolável das notas da release
"""

VERSION = "1.3.2"
GITHUB_REPO = "niellzinhow/OpenMug-Studio"

# Notas embutidas da versão atual (abertura instantânea e fallback caso o GitHub esteja instável)
RELEASE_NOTES = """## Novidades (v1.3.2)

- **Novo Modal de Atualização:** ao detectar uma nova versão, o aplicativo agora abre uma janela moderna no estilo Dark Glassmorphism com rolagem completa por mouse e Touchpad, exibindo todo o texto das notas sem cortes.

## Correções e Ajustes (v1.3.1)

- **Rolagem via Touchpad:** suporte nativo a gestos de dois dedos em Precision Touchpad no modal de notas da versão (além da roda do mouse).
- **Abertura instantânea das Notas:** o modal agora abre na hora usando as notas embutidas da versão e sincroniza silenciosamente em segundo plano com o GitHub.
- **Janelas sempre em primeiro plano:** garantia de elevação e foco automático ao abrir os modais e a pré-visualização de impressão.

## Redesenho Visual (v1.3.0)

- **Interface Dark Glassmorphism:** papel de parede abstrato dinâmico, cards translúcidos, miniaturas 16:9 arredondadas, controles em pílula, seletor suspenso sem bordas brancas do sistema e pré-visualização A4 com barra flutuante.
"""
