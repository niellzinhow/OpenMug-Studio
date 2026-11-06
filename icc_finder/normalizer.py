"""Normalização e identificação de Marcas e Modelos de Impressoras para sublimação.

Converte nomes heterogêneos encontrados em arquivos .icc/.icm, pastas do Google Drive e
páginas web de fabricantes em pares padronizados: (Marca de Impressora, Modelo de Impressora).
"""
import re
from typing import List, Tuple

# Regras ordenadas de modelos conhecidos: (regex, marca_impressora, lista_de_modelos_canonicos)
# Quando um pacote/pasta cobre uma família inteira (ex.: "Série L3000"), expande para os modelos reais.
PRINTER_RULES: List[Tuple[re.Pattern, str, List[str]]] = [
    # --- EPSON SURECOLOR (Sublimação / Plotters) ---
    (re.compile(r"\b(?:sc[-\s]?)?f170\b", re.I), "Epson", ["SureColor F170"]),
    (re.compile(r"\b(?:sc[-\s]?)?f570\b", re.I), "Epson", ["SureColor F570"]),
    (re.compile(r"\b(?:sc[-\s]?)?f571\b", re.I), "Epson", ["SureColor F571"]),
    (re.compile(r"\b(?:sc[-\s]?)?f6370\b", re.I), "Epson", ["SureColor F6370"]),
    (re.compile(r"\b(?:sc[-\s]?)?f6470\b", re.I), "Epson", ["SureColor F6470"]),
    (re.compile(r"\b(?:sc[-\s]?)?t3170x?\b", re.I), "Epson", ["SureColor T3170 / T3170x"]),

    # --- EPSON ECOTANK LINHA L (Brasil / América Latina / Europa) ---
    (re.compile(r"\bl110\b", re.I), "Epson", ["EcoTank L110"]),
    (re.compile(r"\bl120\b", re.I), "Epson", ["EcoTank L120"]),
    (re.compile(r"\bl121\b", re.I), "Epson", ["EcoTank L121"]),
    (re.compile(r"\bs[eé]rie\s*l100\b", re.I), "Epson", ["EcoTank L110", "EcoTank L120", "EcoTank L121"]),
    (re.compile(r"\bl210\b", re.I), "Epson", ["EcoTank L210"]),
    (re.compile(r"\bl220\b", re.I), "Epson", ["EcoTank L220"]),
    (re.compile(r"\bl355\b", re.I), "Epson", ["EcoTank L355"]),
    (re.compile(r"\bl365\b", re.I), "Epson", ["EcoTank L365"]),
    (re.compile(r"\bl375\b", re.I), "Epson", ["EcoTank L375"]),
    (re.compile(r"\bl380\b", re.I), "Epson", ["EcoTank L380"]),
    (re.compile(r"\bl395\b", re.I), "Epson", ["EcoTank L395"]),
    (re.compile(r"\bl396\b", re.I), "Epson", ["EcoTank L396"]),
    (re.compile(r"\bs[eé]rie\s*l300\b", re.I), "Epson", [
        "EcoTank L355", "EcoTank L365", "EcoTank L375", "EcoTank L380", "EcoTank L395", "EcoTank L396"
    ]),
    (re.compile(r"\bl800\b", re.I), "Epson", ["EcoTank L800"]),
    (re.compile(r"\bl805\b", re.I), "Epson", ["EcoTank L805"]),
    (re.compile(r"\bl810\b", re.I), "Epson", ["EcoTank L810"]),
    (re.compile(r"\bl850\b", re.I), "Epson", ["EcoTank L850"]),
    (re.compile(r"\bl1110\b", re.I), "Epson", ["EcoTank L1110"]),
    (re.compile(r"\bl1210\b", re.I), "Epson", ["EcoTank L1210"]),
    (re.compile(r"\bl1250\b", re.I), "Epson", ["EcoTank L1250"]),
    (re.compile(r"\bl1300\b", re.I), "Epson", ["EcoTank L1300"]),
    (re.compile(r"\bl1800\b", re.I), "Epson", ["EcoTank L1800"]),
    (re.compile(r"\b(?:l3110|3110)\b", re.I), "Epson", ["EcoTank L3110"]),
    (re.compile(r"\b(?:l3150|3150)\b", re.I), "Epson", ["EcoTank L3150"]),
    (re.compile(r"\b(?:l3210|3210)\b", re.I), "Epson", ["EcoTank L3210"]),
    (re.compile(r"\b(?:l3250|3250)\b", re.I), "Epson", ["EcoTank L3250"]),
    (re.compile(r"\b(?:s[eé]rie|linha)\s*l3000\b", re.I), "Epson", [
        "EcoTank L3110", "EcoTank L3150", "EcoTank L3210", "EcoTank L3250"
    ]),
    (re.compile(r"\bl4150\b", re.I), "Epson", ["EcoTank L4150"]),
    (re.compile(r"\bl4160\b", re.I), "Epson", ["EcoTank L4160"]),
    (re.compile(r"\bl4260\b", re.I), "Epson", ["EcoTank L4260"]),
    (re.compile(r"\bl5190\b", re.I), "Epson", ["EcoTank L5190"]),
    (re.compile(r"\bl5290\b", re.I), "Epson", ["EcoTank L5290"]),
    (re.compile(r"\bl5590\b", re.I), "Epson", ["EcoTank L5590"]),
    (re.compile(r"\bl6270\b", re.I), "Epson", ["EcoTank L6270"]),
    (re.compile(r"\bl8050\b", re.I), "Epson", ["EcoTank L8050"]),
    (re.compile(r"\bl8180\b", re.I), "Epson", ["EcoTank L8180"]),
    (re.compile(r"\bl14150\b", re.I), "Epson", ["EcoTank L14150"]),
    (re.compile(r"\b(?:l18050|18050)\b", re.I), "Epson", ["EcoTank L18050"]),

    # --- EPSON ECOTANK LINHA ET (Global / EUA / Europa) ---
    (re.compile(r"\bet[-\s]?2720\b", re.I), "Epson", ["EcoTank ET-2720"]),
    (re.compile(r"\bet[-\s]?2750\b", re.I), "Epson", ["EcoTank ET-2750"]),
    (re.compile(r"\bet[-\s]?2760\b", re.I), "Epson", ["EcoTank ET-2760"]),
    (re.compile(r"\bet[-\s]?2800\b", re.I), "Epson", ["EcoTank ET-2800"]),
    (re.compile(r"\bet[-\s]?2803\b", re.I), "Epson", ["EcoTank ET-2803"]),
    (re.compile(r"\bet[-\s]?2850\b", re.I), "Epson", ["EcoTank ET-2850"]),
    (re.compile(r"\bet[-\s]?3760\b", re.I), "Epson", ["EcoTank ET-3760"]),
    (re.compile(r"\bet[-\s]?4760\b", re.I), "Epson", ["EcoTank ET-4760"]),
    (re.compile(r"\bet[-\s]?8500\b", re.I), "Epson", ["EcoTank ET-8500"]),
    (re.compile(r"\bet[-\s]?8550\b", re.I), "Epson", ["EcoTank ET-8550"]),
    (re.compile(r"\bet[-\s]?15000\b", re.I), "Epson", ["EcoTank ET-15000"]),
    (re.compile(r"\bet[-\s]?16650\b", re.I), "Epson", ["EcoTank ET-16650"]),

    # --- EPSON WORKFORCE / EXPRESSION / STYLUS ---
    (re.compile(r"\bt1110\b", re.I), "Epson", ["Stylus Office T1110"]),
    (re.compile(r"\bxp[-\s]?214\b", re.I), "Epson", ["Expression XP-214"]),
    (re.compile(r"\b(?:xp[-\s]?)?241\b", re.I), "Epson", ["Expression XP-241"]),
    (re.compile(r"\bwf[-\s]?7710\b", re.I), "Epson", ["WorkForce WF-7710"]),
    (re.compile(r"\bwf[-\s]?7720\b", re.I), "Epson", ["WorkForce WF-7720"]),
    (re.compile(r"\bwf[-\s]?7310\b", re.I), "Epson", ["WorkForce WF-7310"]),
    (re.compile(r"\bwf[-\s]?7840\b", re.I), "Epson", ["WorkForce WF-7840"]),
    (re.compile(r"\bc?5290\b", re.I), "Epson", ["WorkForce WF-C5290"]),
    (re.compile(r"\bc?5390\b", re.I), "Epson", ["WorkForce WF-C5390"]),
    (re.compile(r"\bc?5710\b", re.I), "Epson", ["WorkForce WF-C5710"]),
    (re.compile(r"\bc?5790\b", re.I), "Epson", ["WorkForce WF-C5790"]),
    (re.compile(r"\bc?5810\b", re.I), "Epson", ["WorkForce WF-C5810"]),
    (re.compile(r"\bc?5890\b", re.I), "Epson", ["WorkForce WF-C5890"]),

    # --- SAWGRASS ---
    (re.compile(r"\bsg[-\s]?400\b", re.I), "Sawgrass", ["Virtuoso SG400"]),
    (re.compile(r"\bsg[-\s]?500\b", re.I), "Sawgrass", ["Virtuoso SG500"]),
    (re.compile(r"\bsg[-\s]?800\b", re.I), "Sawgrass", ["Virtuoso SG800"]),
    (re.compile(r"\bsg[-\s]?1000\b", re.I), "Sawgrass", ["Virtuoso SG1000"]),

    # --- CANON ---
    (re.compile(r"\bgx[-\s]?6010\b", re.I), "Canon", ["MegaTank GX6010"]),
    (re.compile(r"\bgx[-\s]?7010\b", re.I), "Canon", ["MegaTank GX7010"]),
    (re.compile(r"\bix[-\s]?6810\b", re.I), "Canon", ["PIXMA iX6810"]),

    # --- HP ---
    (re.compile(r"\b(?:hp[-\s]*)?7740\b", re.I), "HP", ["OfficeJet Pro 7740"]),
    (re.compile(r"\b(?:hp[-\s]*|designjet[-\s]*)?t650\b", re.I), "HP", ["DesignJet T650"]),

    # --- BROTHER ---
    (re.compile(r"\bsp[-\s]?1\b", re.I), "Brother", ["Sublimation SP-1"]),
]


def extract_printers(text: str) -> List[Tuple[str, str]]:
    """Extrai todos os pares (marca_impressora, modelo_impressora) reconhecidos em um texto."""
    if not text:
        return []
    normalized_text = text.replace("_", " ").replace(".", " ")
    found: List[Tuple[str, str]] = []
    seen = set()

    for pattern, p_brand, models in PRINTER_RULES:
        if pattern.search(normalized_text):
            for model in models:
                key = (p_brand, model)
                if key not in seen:
                    seen.add(key)
                    found.append(key)

    # Fallback genérico para novos modelos lançados pelos fabricantes
    if not found:
        for m in re.finditer(r"\bepson[-\s]+(l\d{3,5}|et[-\s]?\d{4,5}|wf[-\s]?c?\d{4})\b", normalized_text, re.I):
            code = m.group(1).upper().replace(" ", "-")
            label = f"EcoTank {code}" if code.startswith(("L", "ET")) else f"WorkForce {code}"
            key = ("Epson", label)
            if key not in seen:
                seen.add(key)
                found.append(key)

        for m in re.finditer(r"\bcanon[-\s]+([a-z]{1,4}[-\s]?\d{3,5})\b", normalized_text, re.I):
            code = m.group(1).upper().replace(" ", "")
            key = ("Canon", f"Canon {code}")
            if key not in seen:
                seen.add(key)
                found.append(key)

        for m in re.finditer(r"\bbrother[-\s]+([a-z]{2,5}[-\s]?[a-z]?\d{3,5}[a-z]*)\b", normalized_text, re.I):
            code = m.group(1).upper()
            key = ("Brother", f"Brother {code}")
            if key not in seen:
                seen.add(key)
                found.append(key)

    return found


def model_sort_key(model_name: str) -> Tuple[int, int, str]:
    """Ordena modelos de forma natural (EcoTank L120 < L1250 < L3250 < L18050, depois ET, SureColor, etc.)."""
    prefix_rank = 5
    if model_name.startswith("EcoTank L"):
        prefix_rank = 0
    elif model_name.startswith("EcoTank ET"):
        prefix_rank = 1
    elif model_name.startswith("SureColor"):
        prefix_rank = 2
    elif model_name.startswith("WorkForce"):
        prefix_rank = 3
    elif model_name.startswith(("Expression", "Stylus")):
        prefix_rank = 4

    nums = re.findall(r"\d+", model_name)
    first_num = int(nums[0]) if nums else 999999
    return (prefix_rank, first_num, model_name.lower())

