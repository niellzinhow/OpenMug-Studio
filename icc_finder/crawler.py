"""Motor de varredura web (Crawler) das 10 principais marcas de tinta sublimática.

Varre páginas oficiais, CDNs e pastas públicas do Google Drive (sem API key e sem burlar
qualquer bloqueio/CAPTCHA) para localizar onde cada marca hospeda seus perfis ICC/ICM e
indexá-los na hierarquia:
    Marca de Impressora > Modelo de Impressora > Marca de Tinta
"""
import concurrent.futures
import html
import io
import json
import os
import re
import time
import urllib.parse
import urllib.request
import zipfile
from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Callable, Dict, List, Optional, Tuple

try:
    from icc_finder.normalizer import extract_printers, model_sort_key
except ImportError:
    from normalizer import extract_printers, model_sort_key


HTTP_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,es;q=0.7",
}

MODULE_DIR = os.path.dirname(os.path.abspath(__file__))
CACHE_PATH = os.path.join(MODULE_DIR, "cache_perfis.json")
DOWNLOADS_DIR = os.path.join(MODULE_DIR, "downloads")


# As 10 principais marcas de tinta sublimática rastreadas na internet
TOP_10_INK_BRANDS: List[Dict[str, str]] = [
    {
        "id": "jetink",
        "name": "JetInk",
        "origin": "Brasil",
        "official_url": "https://jetink.com.br/perfil-de-cor/",
        "hosting": "Google Drive Público + Dropbox Oficial (.icm diretos)",
        "notes": "Perfis .icm individuais calibrados para linha Epson EcoTank L, SureColor F170/F571 e T3170x.",
    },
    {
        "id": "inkit",
        "name": "Ink It (NanoSub)",
        "origin": "Brasil",
        "official_url": "https://www.proink.com.br/pages/perfis-de-cor-icc",
        "hosting": "Google Drive Público (Subpastas por Série Epson .icm/.rar)",
        "notes": "Linha NanoSub Sublimática distribuída pela Proink com perfis separados para fundo branco/papel comum.",
    },
    {
        "id": "proink",
        "name": "Proink",
        "origin": "Brasil",
        "official_url": "https://www.proink.com.br/pages/perfis-de-cor-icc",
        "hosting": "Portal Proink + Repositório Google Drive Oficial",
        "notes": "Central oficial Proink cobrindo linhas EcoTank L1250/L3250, A3 (L1300/L1800/L18050) e SureColor.",
    },
    {
        "id": "genesis",
        "name": "Gênesis (Sublidesk)",
        "origin": "Brasil",
        "official_url": "https://tintasublimatica.com.br/#downloads",
        "hosting": "Portal TintaSublimatica.com.br (Tabelas, Manuais e Suporte Técnico)",
        "notes": "Linha Sublidesk DS.7000 / Sublitop com tabela oficial cruzando impressora x papel sublimático.",
    },
    {
        "id": "sulink",
        "name": "Sulink",
        "origin": "Brasil",
        "official_url": (
            "https://sulink.com.br/categoria/"
            "17-perfil-de-coresperfil-de-cores-servicos-online-suporte-online-perfil-icc-suporte-tecnico"
        ),
        "hosting": "Catálogo Oficial Sulink (Epson, Canon e HP)",
        "notes": "Maior variedade multimarcas no Brasil (Epson EcoTank/WorkForce, Canon MegaTank/PIXMA e HP).",
    },
    {
        "id": "colormake",
        "name": "Color Make",
        "origin": "América Latina",
        "official_url": "https://colormake.com/blog/perfiles-de-color-icc/",
        "hosting": "Servidor Próprio WordPress (.icc e .zip diretos)",
        "notes": "Disponibiliza arquivos .icc e pacote .zip direto para EcoTank L1110–L3250 e WorkForce.",
    },
    {
        "id": "hiipoo",
        "name": "Hiipoo",
        "origin": "Internacional",
        "official_url": "https://www.hiipoo.com/",
        "hosting": "Google Drive Público (.icc diretos por modelo ET)",
        "notes": "Perfis .icc diretos calibrados para tintas Hiipoo em EcoTank série ET (papel Hiipoo e A-SUB).",
    },
    {
        "id": "asub",
        "name": "A-SUB",
        "origin": "Internacional",
        "official_url": "https://www.a-sub.com/pages/icc-profile",
        "hosting": "Shopify CDN Oficial (.icm diretos)",
        "notes": "Perfis .icm diretos para EcoTank série ET (EUA) e série L805/L1800/L3250 (Europa/América Latina).",
    },
    {
        "id": "cosmos",
        "name": "Cosmos Ink",
        "origin": "Internacional",
        "official_url": "https://cosmos-ink.com/products/color-profiles-cosmos-ink%C2%AE",
        "hosting": "Portal Oficial Shopify (Pacote gratuito sob pedido/download)",
        "notes": "Perfis dedicados para conversões Epson EcoTank, WorkForce WF-7710/7720 e Sawgrass SG400–SG1000.",
    },
    {
        "id": "sawgrass",
        "name": "Sawgrass (SubliJet UHD)",
        "origin": "Internacional",
        "official_url": "https://www.sawgrassink.com/products/software/",
        "hosting": "Sawgrass Print Utility / Print Manager (Gerenciamento Integrado)",
        "notes": "Impressoras Sawgrass SG400/SG500/SG800/SG1000 aplicam o perfil automaticamente via Print Utility.",
    },
]


@dataclass
class ProfileEntry:
    """Representa um perfil ICC/ICM ou repositório oficial associado a uma combinação única."""
    printer_brand: str          # Ex.: "Epson", "Canon", "HP", "Sawgrass"
    printer_model: str          # Ex.: "EcoTank L3250", "SureColor F170"
    ink_brand: str              # Ex.: "JetInk", "Ink It (NanoSub)"
    profile_name: str           # Nome amigável ou nome real do arquivo (.icc/.icm)
    download_url: str           # Link direto (.icc/.icm/.zip) ou URL da pasta/página oficial
    source_page: str            # Página onde o perfil foi encontrado
    delivery_type: str          # "direct_icc" | "direct_archive" | "cloud_folder" | "official_portal" | "software_spm"
    hosting_label: str          # Ex.: "Google Drive (.icm direto)", "Servidor Color Make (.icc)"
    details: str = ""           # Observações de papel / qualidade / compatibilidade


@dataclass
class BrandScanReport:
    """Resumo do rastreamento de onde cada uma das 10 marcas hospeda seus perfis."""
    ink_brand: str
    origin: str
    official_url: str
    discovered_repo_url: str
    hosting_summary: str
    status: str                 # "online" | "fallback"
    profiles_count: int
    printers_count: int
    scanned_at: str
    message: str = ""


def _fetch_html(url: str, timeout: int = 10) -> Tuple[str, str]:
    req = urllib.request.Request(url, headers=HTTP_HEADERS)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        final_url = resp.geturl()
        raw = resp.read().decode("utf-8", errors="ignore")
        return final_url, raw


def _parse_gdrive_public_folder(folder_id: str, timeout: int = 10) -> List[Tuple[str, str, str]]:
    """Extrai (file_id, nome, mime_type) de uma pasta pública do Google Drive sem exigir API key."""
    url = f"https://drive.google.com/drive/folders/{folder_id}"
    _, raw = _fetch_html(url, timeout=timeout)
    unesc = html.unescape(raw)
    unesc = re.sub(r"\\x([0-9a-fA-F]{2})", lambda m: chr(int(m.group(1), 16)), unesc)
    unesc = unesc.replace('\\"', '"').replace("\\/", "/")
    try:
        unesc = re.sub(r"\\u([0-9a-fA-F]{4})", lambda m: chr(int(m.group(1), 16)), unesc)
    except Exception:
        pass

    items: List[Tuple[str, str, str]] = []
    seen = set()
    pattern = re.compile(
        r'\["([A-Za-z0-9_-]{20,55})",\["[A-Za-z0-9_-]{15,55}"\],"([^"]{1,180})","([^"]{3,95})"'
    )
    for m in pattern.finditer(unesc):
        fid, name, mime = m.group(1), m.group(2).strip(), m.group(3).strip()
        if fid not in seen:
            seen.add(fid)
            items.append((fid, name, mime))
    return items


def _gdrive_direct_url(file_id: str) -> str:
    return f"https://drive.google.com/uc?export=download&id={file_id}"


def _gdrive_folder_url(folder_id: str) -> str:
    return f"https://drive.google.com/drive/folders/{folder_id}"


# ---------------------------------------------------------------------------
# Varredores individuais das 10 marcas
# ---------------------------------------------------------------------------

def _crawl_jetink() -> Tuple[List[ProfileEntry], str, str]:
    page_url = "https://jetink.com.br/perfil-de-cor/"
    _, raw = _fetch_html(page_url)

    # Localiza dinamicamente o ID da pasta do Google Drive na página oficial da JetInk
    m_drive = re.search(r"drive\.google\.com/drive/folders/([A-Za-z0-9_-]{20,50})", raw)
    folder_id = m_drive.group(1) if m_drive else "1FBRfw4c29w9H0SJtbjSoda_iwcwFHKzv"
    repo_url = _gdrive_folder_url(folder_id)

    items = _parse_gdrive_public_folder(folder_id)
    entries: List[ProfileEntry] = []
    for fid, filename, _mime in items:
        if not filename.lower().endswith((".icc", ".icm", ".zip")):
            continue
        printers = extract_printers(filename)
        dtype = "direct_icc" if filename.lower().endswith((".icc", ".icm")) else "direct_archive"
        for p_brand, p_model in printers:
            entries.append(ProfileEntry(
                printer_brand=p_brand,
                printer_model=p_model,
                ink_brand="JetInk",
                profile_name=filename,
                download_url=_gdrive_direct_url(fid),
                source_page=repo_url,
                delivery_type=dtype,
                hosting_label="Google Drive Oficial (.icm direto)",
                details="Perfil oficial JetInk Sublimática (extraído da nuvem pública da marca).",
            ))
    return entries, repo_url, f"{len(items)} itens lidos no Google Drive oficial"


def _crawl_inkit_and_proink() -> Dict[str, Tuple[List[ProfileEntry], str, str]]:
    page_url = "https://www.proink.com.br/pages/perfis-de-cor-icc"
    _, raw = _fetch_html(page_url)
    folder_ids = re.findall(r"drive\.google\.com/drive/folders/([A-Za-z0-9_-]{20,50})", raw)

    # Na tabela oficial da Proink: pasta sublimática Ink It NanoSub é 1e8gfEXVcku6FGw8NZyIZdJ4HWAn2uYAL
    sub_folder_id = "1e8gfEXVcku6FGw8NZyIZdJ4HWAn2uYAL"
    proink_folder_id = "1_t84owmnFHyeAVMnjS936EsW18uLw90w"
    for fid in folder_ids:
        if "1e8gf" in fid:
            sub_folder_id = fid
        elif "1_t84" in fid:
            proink_folder_id = fid

    sub_repo_url = _gdrive_folder_url(sub_folder_id)
    top_items = _parse_gdrive_public_folder(sub_folder_id)

    inkit_entries: List[ProfileEntry] = []
    proink_entries: List[ProfileEntry] = []

    # Inspeciona concorrentemente as subpastas da linha sublimática para pegar os .icm diretos!
    subfolders = [(fid, name) for fid, name, mime in top_items if "folder" in mime]

    def _inspect_sub(pair: Tuple[str, str]):
        sf_id, sf_name = pair
        try:
            return sf_id, sf_name, _parse_gdrive_public_folder(sf_id, timeout=8)
        except Exception:
            return sf_id, sf_name, []

    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as pool:
        sub_results = list(pool.map(_inspect_sub, subfolders))

    for sf_id, sf_name, children in sub_results:
        parent_printers = extract_printers(sf_name)
        sf_url = _gdrive_folder_url(sf_id)
        matched_child = False

        for cf_id, cf_name, cf_mime in children:
            lower = cf_name.lower()
            if lower.endswith((".icc", ".icm", ".zip", ".rar")):
                child_specific = extract_printers(cf_name)
                if "compat" in sf_name.lower() or "linha" in sf_name.lower() or not child_specific:
                    child_printers = list(dict.fromkeys(child_specific + parent_printers))
                else:
                    child_printers = child_specific
                dtype = "direct_icc" if lower.endswith((".icc", ".icm")) else "direct_archive"
                for p_brand, p_model in child_printers:
                    matched_child = True
                    inkit_entries.append(ProfileEntry(
                        printer_brand=p_brand,
                        printer_model=p_model,
                        ink_brand="Ink It (NanoSub)",
                        profile_name=cf_name,
                        download_url=_gdrive_direct_url(cf_id),
                        source_page=sf_url,
                        delivery_type=dtype,
                        hosting_label="Google Drive Ink It / Proink",
                        details=f"Subpasta oficial: {sf_name}",
                    ))

        if not matched_child:
            for p_brand, p_model in parent_printers:
                inkit_entries.append(ProfileEntry(
                    printer_brand=p_brand,
                    printer_model=p_model,
                    ink_brand="Ink It (NanoSub)",
                    profile_name=f"Pasta Oficial Ink It — {sf_name}",
                    download_url=sf_url,
                    source_page=sub_repo_url,
                    delivery_type="cloud_folder",
                    hosting_label="Pasta Google Drive Ink It",
                    details="Contém arquivo .icc/.icm e instruções de configuração do driver Epson.",
                ))

    # Mapeia também a marca Proink (repositório geral da marca para impressoras Epson)
    proink_repo_url = _gdrive_folder_url(proink_folder_id)
    proink_items = _parse_gdrive_public_folder(proink_folder_id)
    for item_id, item_name, item_mime in proink_items:
        printers = extract_printers(item_name)
        is_folder = "folder" in item_mime
        target_url = _gdrive_folder_url(item_id) if is_folder else _gdrive_direct_url(item_id)
        dtype = (
            "cloud_folder" if is_folder
            else ("direct_icc" if item_name.lower().endswith((".icc", ".icm")) else "direct_archive")
        )
        for p_brand, p_model in printers:
            proink_entries.append(ProfileEntry(
                printer_brand=p_brand,
                printer_model=p_model,
                ink_brand="Proink",
                profile_name=f"Perfil Proink — {item_name}",
                download_url=target_url,
                source_page=page_url,
                delivery_type=dtype,
                hosting_label="Google Drive Oficial Proink",
                details="Repositório oficial Proink (verifique a linha de tinta correspondente na pasta).",
            ))

    # Inclui também os perfis NanoSub sob Proink caso o usuário busque pela distribuidora Proink
    existing_proink_models = {(e.printer_brand, e.printer_model) for e in proink_entries}
    for e in inkit_entries:
        if (e.printer_brand, e.printer_model) not in existing_proink_models:
            proink_entries.append(ProfileEntry(
                printer_brand=e.printer_brand,
                printer_model=e.printer_model,
                ink_brand="Proink",
                profile_name=e.profile_name,
                download_url=e.download_url,
                source_page=page_url,
                delivery_type=e.delivery_type,
                hosting_label="Google Drive Proink (Linha Sublimática)",
                details="Distribuído oficialmente no portal Proink (linha NanoSub).",
            ))

    return {
        "inkit": (inkit_entries, sub_repo_url, f"{len(subfolders)} subpastas de modelos inspecionadas"),
        "proink": (proink_entries, page_url, f"{len(proink_entries)} perfis/pastas indexados na Proink"),
    }


def _crawl_sulink() -> Tuple[List[ProfileEntry], str, str]:
    base_cat = (
        "https://sulink.com.br/categoria/"
        "17-perfil-de-coresperfil-de-cores-servicos-online-suporte-online-perfil-icc-suporte-tecnico"
    )
    product_urls = []
    seen_urls = set()

    for pg in (1, 2, 3):
        url = f"{base_cat}?sort=newest&pg={pg}"
        try:
            _, raw = _fetch_html(url, timeout=9)
            matches = re.findall(
                r'href=["\'](https://sulink\.com\.br/produto/[^"\']*perfil-de-cores-icc[^"\']*)["\']',
                raw,
                re.I,
            )
            new_on_page = 0
            for u in matches:
                if u not in seen_urls:
                    seen_urls.add(u)
                    product_urls.append(u)
                    new_on_page += 1
            if new_on_page == 0:
                break
        except Exception:
            if pg == 1:
                raise
            break

    entries: List[ProfileEntry] = []
    for prod_url in product_urls:
        slug = prod_url.split("/produto/")[-1].split("/")[0]
        printers = extract_printers(slug)
        for p_brand, p_model in printers:
            entries.append(ProfileEntry(
                printer_brand=p_brand,
                printer_model=p_model,
                ink_brand="Sulink",
                profile_name=f"Perfil ICC Sulink — {p_brand} {p_model}",
                download_url=prod_url,
                source_page=base_cat,
                delivery_type="official_portal",
                hosting_label="Portal Técnico Sulink",
                details="Página oficial do perfil ICC Sulink com parâmetros de impressão e papel.",
            ))

    return entries, base_cat, f"{len(product_urls)} páginas de impressoras varridas no catálogo Sulink"


def _crawl_colormake() -> Tuple[List[ProfileEntry], str, str]:
    page_url = "https://colormake.com/blog/perfiles-de-color-icc/"
    _, raw = _fetch_html(page_url)

    direct_links = list(dict.fromkeys(
        re.findall(r'href=["\'](https?://[^"\']+\.(?:icc|icm|zip))["\']', raw, re.I)
    ))

    entries: List[ProfileEntry] = []
    ecotank_models = [
        ("Epson", "EcoTank L1110"),
        ("Epson", "EcoTank L1210"),
        ("Epson", "EcoTank L1250"),
        ("Epson", "EcoTank L3110"),
        ("Epson", "EcoTank L3150"),
        ("Epson", "EcoTank L3210"),
        ("Epson", "EcoTank L3250"),
        ("Epson", "EcoTank L1300"),
        ("Epson", "EcoTank L1800"),
    ]
    wf_models = [
        ("Epson", "WorkForce WF-7710"),
        ("Epson", "WorkForce WF-7720"),
    ]

    for durl in direct_links:
        fname = urllib.parse.unquote(durl.split("/")[-1])
        lower = fname.lower()
        if "dtf" in lower:
            continue
        dtype = "direct_icc" if lower.endswith((".icc", ".icm")) else "direct_archive"

        if "wf" in lower:
            targets = wf_models
            detail = "Perfil ICC direto Color Make para linha Epson WorkForce (papel 80g / 720x1200)."
        elif "hd" in lower:
            targets = ecotank_models
            detail = "Perfil ICC direto Color Make Tinta HD (papel 100g / 720x1800 6 passadas)."
        else:
            targets = ecotank_models
            detail = "Pacote ZIP oficial de perfis de cor sublimáticos Color Make."

        for p_brand, p_model in targets:
            entries.append(ProfileEntry(
                printer_brand=p_brand,
                printer_model=p_model,
                ink_brand="Color Make",
                profile_name=fname,
                download_url=durl,
                source_page=page_url,
                delivery_type=dtype,
                hosting_label="Servidor Oficial Color Make (.icc/.zip direto)",
                details=detail,
            ))

    return entries, page_url, f"{len(direct_links)} arquivos diretos (.icc/.zip) encontrados"


def _crawl_genesis() -> Tuple[List[ProfileEntry], str, str]:
    page_url = "https://tintasublimatica.com.br/"
    _, raw = _fetch_html(page_url)

    tabela_match = re.search(r'href=["\'](https?://[^"\']*Tabela-Perfil-Cores-Sublidesk\.pdf)["\']', raw, re.I)
    f570_match = re.search(r'href=["\'](https?://[^"\']*SC-F570[^"\']*\.pdf)["\']', raw, re.I)
    tabela_url = tabela_match.group(1) if tabela_match else "https://tintasublimatica.com.br/pdf/Tabela-Perfil-Cores-Sublidesk.pdf"
    f570_url = f570_match.group(1) if f570_match else "https://tintasublimatica.com.br/#downloads"

    supported_ecotank = [
        "EcoTank L120", "EcoTank L380", "EcoTank L395", "EcoTank L805",
        "EcoTank L1250", "EcoTank L1300", "EcoTank L1800",
        "EcoTank L3110", "EcoTank L3150", "EcoTank L3210", "EcoTank L3250",
        "EcoTank L4150", "EcoTank L4260", "EcoTank L14150",
        "SureColor F170",
    ]
    entries: List[ProfileEntry] = [
        ProfileEntry(
            printer_brand="Epson",
            printer_model="SureColor F570",
            ink_brand="Gênesis (Sublidesk)",
            profile_name="Guia & Perfil Gênesis Sublidesk DS.7000 — SC-F570",
            download_url=f570_url,
            source_page="https://tintasublimatica.com.br/#downloads",
            delivery_type="official_portal",
            hosting_label="Portal Oficial Gênesis Tintas",
            details="Documentação oficial Gênesis Sublidesk para Epson SureColor SC-F570.",
        )
    ]
    for model in supported_ecotank:
        entries.append(ProfileEntry(
            printer_brand="Epson",
            printer_model=model,
            ink_brand="Gênesis (Sublidesk)",
            profile_name=f"Perfil Gênesis Sublidesk DS.7000 — {model}",
            download_url="https://tintasublimatica.com.br/#downloads",
            source_page=tabela_url,
            delivery_type="official_portal",
            hosting_label="Portal TintaSublimatica.com.br (Gênesis)",
            details="Consulte a Tabela Oficial Impressoras x Papéis da Gênesis na seção de Downloads.",
        ))

    return entries, "https://tintasublimatica.com.br/#downloads", "Portal e tabela Sublidesk verificados online"


def _crawl_hiipoo() -> Tuple[List[ProfileEntry], str, str]:
    page_url = "https://www.hiipoo.com/"
    _, raw = _fetch_html(page_url)

    m_drive = re.search(r"drive\.google\.com/drive/folders/([A-Za-z0-9_-]{20,50})", raw)
    folder_id = m_drive.group(1) if m_drive else "1dtp5cB6rHGfDdroN3OToKC9gz7VsxJuk"
    repo_url = _gdrive_folder_url(folder_id)

    items = _parse_gdrive_public_folder(folder_id)
    entries: List[ProfileEntry] = []
    for fid, filename, _mime in items:
        if not filename.lower().endswith((".icc", ".icm", ".zip")):
            continue
        printers = extract_printers(filename)
        dtype = "direct_icc" if filename.lower().endswith((".icc", ".icm")) else "direct_archive"
        for p_brand, p_model in printers:
            entries.append(ProfileEntry(
                printer_brand=p_brand,
                printer_model=p_model,
                ink_brand="Hiipoo",
                profile_name=filename,
                download_url=_gdrive_direct_url(fid),
                source_page=repo_url,
                delivery_type=dtype,
                hosting_label="Google Drive Oficial Hiipoo (.icc direto)",
                details="Perfil .icc oficial extraído diretamente da pasta Google Drive da Hiipoo.",
            ))
    return entries, repo_url, f"{len(entries)} perfis .icc lidos no Google Drive da Hiipoo"


def _crawl_asub() -> Tuple[List[ProfileEntry], str, str]:
    page_url = "https://www.a-sub.com/pages/icc-profile"
    _, raw = _fetch_html(page_url)

    icm_links = list(dict.fromkeys(
        re.findall(r'href=["\'](https://cdn\.shopify\.com/[^"\']+\.(?:icc|icm)[^"\']*)["\']', raw, re.I)
    ))

    entries: List[ProfileEntry] = []
    et_models = [
        "EcoTank ET-2720", "EcoTank ET-2760", "EcoTank ET-2800",
        "EcoTank ET-2803", "EcoTank ET-2850", "EcoTank ET-3760",
        "EcoTank ET-4760", "EcoTank ET-15000",
    ]
    eu_latam_models = [
        "EcoTank L805", "EcoTank L1800", "EcoTank L3150", "EcoTank L3250",
    ]

    for link in icm_links:
        clean_link = html.unescape(link)
        fname = clean_link.split("/")[-1].split("?")[0]
        if "l805" in fname.lower():
            for model in eu_latam_models:
                entries.append(ProfileEntry(
                    printer_brand="Epson",
                    printer_model=model,
                    ink_brand="A-SUB",
                    profile_name=fname,
                    download_url=clean_link,
                    source_page=page_url,
                    delivery_type="direct_icc",
                    hosting_label="Shopify CDN Oficial A-SUB (.icm direto)",
                    details="Perfil .icm direto A-SUB para linha Epson EcoTank série L (800dpi).",
                ))
        else:
            for model in et_models:
                entries.append(ProfileEntry(
                    printer_brand="Epson",
                    printer_model=model,
                    ink_brand="A-SUB",
                    profile_name=fname,
                    download_url=clean_link,
                    source_page=page_url,
                    delivery_type="direct_icc",
                    hosting_label="Shopify CDN Oficial A-SUB (.icm direto)",
                    details="Perfil .icm direto A-SUB para linha Epson EcoTank série ET.",
                ))

    return entries, page_url, f"{len(icm_links)} arquivos .icm diretos encontrados no CDN da A-SUB"


def _crawl_cosmos() -> Tuple[List[ProfileEntry], str, str]:
    page_url = "https://cosmos-ink.com/products/color-profiles-cosmos-ink%C2%AE"
    _, raw = _fetch_html(page_url)

    discovered = extract_printers(raw)
    baseline = [
        ("Epson", "EcoTank ET-2720"), ("Epson", "EcoTank ET-2760"),
        ("Epson", "EcoTank ET-2800"), ("Epson", "EcoTank ET-2803"),
        ("Epson", "EcoTank ET-2850"), ("Epson", "EcoTank ET-4760"),
        ("Epson", "EcoTank ET-8500"), ("Epson", "EcoTank ET-8550"),
        ("Epson", "EcoTank ET-15000"), ("Epson", "WorkForce WF-7710"),
        ("Epson", "WorkForce WF-7720"), ("Sawgrass", "Virtuoso SG400"),
        ("Sawgrass", "Virtuoso SG500"), ("Sawgrass", "Virtuoso SG800"),
        ("Sawgrass", "Virtuoso SG1000"),
    ]
    merged = list(dict.fromkeys(discovered + baseline))

    entries = [
        ProfileEntry(
            printer_brand=pb,
            printer_model=pm,
            ink_brand="Cosmos Ink",
            profile_name=f"Cosmos Ink Color Profile — {pb} {pm}",
            download_url=page_url,
            source_page=page_url,
            delivery_type="official_portal",
            hosting_label="Portal Oficial Cosmos Ink",
            details="Disponibilizado gratuitamente no portal oficial Cosmos Ink com vídeo-tutorial.",
        )
        for pb, pm in merged
    ]
    return entries, page_url, f"{len(entries)} modelos mapeados na página oficial Cosmos Ink"


def _crawl_sawgrass() -> Tuple[List[ProfileEntry], str, str]:
    home_url = "https://www.sawgrassink.com/"
    _, raw = _fetch_html(home_url)
    m_sw = re.search(r'href=["\'](https://www\.sawgrassink\.com/[^"\']*software[^"\']*)["\']', raw, re.I)
    sw_url = m_sw.group(1) if m_sw else "https://www.sawgrassink.com/products/software/"

    models = ["Virtuoso SG400", "Virtuoso SG500", "Virtuoso SG800", "Virtuoso SG1000"]
    entries = [
        ProfileEntry(
            printer_brand="Sawgrass",
            printer_model=m,
            ink_brand="Sawgrass (SubliJet UHD)",
            profile_name=f"Sawgrass Print Utility (Perfil SubliJet Integrado — {m})",
            download_url=sw_url,
            source_page=home_url,
            delivery_type="software_spm",
            hosting_label="Sawgrass Print Utility / Manager",
            details=(
                "A Sawgrass não usa arquivo .icc avulso: o gerenciamento de cores SubliJet UHD/HD "
                "é aplicado automaticamente pelo software oficial Sawgrass Print Utility."
            ),
        )
        for m in models
    ]
    return entries, sw_url, "Portal Sawgrass Print Utility verificado online"


# ---------------------------------------------------------------------------
# Catálogo de contingência (caso alguma marca esteja temporariamente offline)
# ---------------------------------------------------------------------------

def _fallback_entries_for_brand(brand_id: str) -> List[ProfileEntry]:
    if brand_id == "jetink":
        models = [
            "SureColor F170", "SureColor F571", "EcoTank L120", "EcoTank L121",
            "EcoTank L365", "EcoTank L396", "EcoTank L1250", "EcoTank L1300",
            "EcoTank L3150", "EcoTank L3210", "EcoTank L3250", "EcoTank L4150",
            "EcoTank L4260", "EcoTank L5590", "EcoTank L14150", "EcoTank L18050",
            "Stylus Office T1110", "SureColor T3170 / T3170x", "Expression XP-241",
        ]
        return [
            ProfileEntry(
                printer_brand="Epson",
                printer_model=m,
                ink_brand="JetInk",
                profile_name=f"Perfil JetInk — {m}",
                download_url="https://drive.google.com/drive/folders/1FBRfw4c29w9H0SJtbjSoda_iwcwFHKzv",
                source_page="https://jetink.com.br/perfil-de-cor/",
                delivery_type="cloud_folder",
                hosting_label="Google Drive Oficial JetInk",
                details="Pasta oficial de perfis .icm da JetInk.",
            )
            for m in models
        ]
    if brand_id in ("inkit", "proink"):
        ink_name = "Ink It (NanoSub)" if brand_id == "inkit" else "Proink"
        models = [
            "EcoTank L120", "EcoTank L380", "EcoTank L395", "EcoTank L805",
            "EcoTank L1250", "EcoTank L1300", "EcoTank L1800", "EcoTank L3150",
            "EcoTank L3250", "EcoTank L8050", "EcoTank L14150", "EcoTank L18050",
            "SureColor F170", "SureColor T3170 / T3170x", "Expression XP-241",
        ]
        return [
            ProfileEntry(
                printer_brand="Epson",
                printer_model=m,
                ink_brand=ink_name,
                profile_name=f"Perfil {ink_name} — {m}",
                download_url="https://drive.google.com/drive/folders/1e8gfEXVcku6FGw8NZyIZdJ4HWAn2uYAL",
                source_page="https://www.proink.com.br/pages/perfis-de-cor-icc",
                delivery_type="cloud_folder",
                hosting_label="Google Drive Oficial Proink / Ink It",
                details="Pasta oficial de perfis sublimáticos Proink / Ink It.",
            )
            for m in models
        ]
    if brand_id == "sulink":
        pairs = [
            ("Epson", "EcoTank L1250"), ("Epson", "EcoTank L1300"), ("Epson", "EcoTank L14150"),
            ("Epson", "EcoTank L1800"), ("Epson", "EcoTank L3150"), ("Epson", "EcoTank L3250"),
            ("Epson", "EcoTank L380"), ("Epson", "EcoTank L395"), ("Epson", "EcoTank L4150"),
            ("Epson", "WorkForce WF-C5710"), ("Epson", "WorkForce WF-C5810"), ("Epson", "WorkForce WF-C5890"),
            ("Canon", "MegaTank GX6010"), ("Canon", "MegaTank GX7010"), ("Canon", "PIXMA iX6810"),
            ("HP", "OfficeJet Pro 7740"), ("HP", "DesignJet T650"),
        ]
        cat_url = TOP_10_INK_BRANDS[4]["official_url"]
        return [
            ProfileEntry(
                printer_brand=pb,
                printer_model=pm,
                ink_brand="Sulink",
                profile_name=f"Perfil ICC Sulink — {pb} {pm}",
                download_url=cat_url,
                source_page=cat_url,
                delivery_type="official_portal",
                hosting_label="Catálogo Oficial Sulink",
                details="Portal de perfis ICC Sulink.",
            )
            for pb, pm in pairs
        ]
    if brand_id == "colormake":
        return [
            ProfileEntry(
                printer_brand="Epson",
                printer_model=m,
                ink_brand="Color Make",
                profile_name="Colormake-Sublimation-Color-Profile.zip",
                download_url="https://colormake.com/blog/perfiles-de-color-icc/",
                source_page="https://colormake.com/blog/perfiles-de-color-icc/",
                delivery_type="official_portal",
                hosting_label="Servidor Color Make",
                details="Página oficial de perfis ICC Color Make.",
            )
            for m in ["EcoTank L1110", "EcoTank L1250", "EcoTank L3110", "EcoTank L3150", "EcoTank L3210", "EcoTank L3250"]
        ]
    if brand_id == "genesis":
        return [
            ProfileEntry(
                printer_brand="Epson",
                printer_model=m,
                ink_brand="Gênesis (Sublidesk)",
                profile_name=f"Perfil Gênesis Sublidesk — {m}",
                download_url="https://tintasublimatica.com.br/#downloads",
                source_page="https://tintasublimatica.com.br/",
                delivery_type="official_portal",
                hosting_label="Portal TintaSublimatica.com.br",
                details="Portal oficial Gênesis Sublidesk.",
            )
            for m in ["SureColor F570", "SureColor F170", "EcoTank L1250", "EcoTank L3150", "EcoTank L3250", "EcoTank L1300", "EcoTank L1800"]
        ]
    if brand_id == "hiipoo":
        return [
            ProfileEntry(
                printer_brand="Epson",
                printer_model=m,
                ink_brand="Hiipoo",
                profile_name=f"Hiipoo ICC — {m}",
                download_url="https://drive.google.com/drive/folders/1dtp5cB6rHGfDdroN3OToKC9gz7VsxJuk",
                source_page="https://www.hiipoo.com/",
                delivery_type="cloud_folder",
                hosting_label="Google Drive Oficial Hiipoo",
                details="Pasta Google Drive oficial Hiipoo.",
            )
            for m in ["EcoTank ET-2720", "EcoTank ET-2760", "EcoTank ET-2800", "EcoTank ET-2803", "EcoTank ET-8550", "EcoTank ET-15000"]
        ]
    if brand_id == "asub":
        return [
            ProfileEntry(
                printer_brand="Epson",
                printer_model=m,
                ink_brand="A-SUB",
                profile_name=f"A-SUB ICC — {m}",
                download_url="https://www.a-sub.com/pages/icc-profile",
                source_page="https://www.a-sub.com/pages/icc-profile",
                delivery_type="official_portal",
                hosting_label="Portal Oficial A-SUB",
                details="Página oficial de download de perfis ICC A-SUB.",
            )
            for m in ["EcoTank ET-2720", "EcoTank ET-2800", "EcoTank ET-15000", "EcoTank L805", "EcoTank L1800", "EcoTank L3250"]
        ]
    if brand_id == "cosmos":
        return [
            ProfileEntry(
                printer_brand=pb,
                printer_model=pm,
                ink_brand="Cosmos Ink",
                profile_name=f"Cosmos Ink — {pb} {pm}",
                download_url="https://cosmos-ink.com/products/color-profiles-cosmos-ink%C2%AE",
                source_page="https://cosmos-ink.com/",
                delivery_type="official_portal",
                hosting_label="Portal Cosmos Ink",
                details="Portal oficial Cosmos Ink.",
            )
            for pb, pm in [("Epson", "EcoTank ET-2800"), ("Epson", "EcoTank ET-8550"), ("Epson", "EcoTank ET-15000"), ("Sawgrass", "Virtuoso SG500"), ("Sawgrass", "Virtuoso SG1000")]
        ]
    return [
        ProfileEntry(
            printer_brand="Sawgrass",
            printer_model=m,
            ink_brand="Sawgrass (SubliJet UHD)",
            profile_name=f"Sawgrass Print Utility — {m}",
            download_url="https://www.sawgrassink.com/products/software/",
            source_page="https://www.sawgrassink.com/",
            delivery_type="software_spm",
            hosting_label="Sawgrass Print Utility",
            details="Software oficial de gerenciamento de cores Sawgrass.",
        )
        for m in ["Virtuoso SG400", "Virtuoso SG500", "Virtuoso SG800", "Virtuoso SG1000"]
    ]


# ---------------------------------------------------------------------------
# Coordenador concorrente de varredura + Índice Hierárquico
# ---------------------------------------------------------------------------

def scan_all_brands(
    progress_cb: Optional[Callable[[int, int, str], None]] = None
) -> Tuple[List[ProfileEntry], List[BrandScanReport]]:
    """Varre concorrentemente as 10 marcas na internet e retorna (entradas, relatórios)."""
    now_str = datetime.now().strftime("%d/%m/%Y %H:%M")
    all_entries: List[ProfileEntry] = []
    reports_by_id: Dict[str, BrandScanReport] = {}

    meta_by_id = {b["id"]: b for b in TOP_10_INK_BRANDS}

    tasks = [
        ("jetink", "JetInk", _crawl_jetink),
        ("proink_inkit", "Proink & Ink It", _crawl_inkit_and_proink),
        ("sulink", "Sulink", _crawl_sulink),
        ("colormake", "Color Make", _crawl_colormake),
        ("genesis", "Gênesis (Sublidesk)", _crawl_genesis),
        ("hiipoo", "Hiipoo", _crawl_hiipoo),
        ("asub", "A-SUB", _crawl_asub),
        ("cosmos", "Cosmos Ink", _crawl_cosmos),
        ("sawgrass", "Sawgrass (SubliJet UHD)", _crawl_sawgrass),
    ]

    completed_brands = 0
    total_brands = 10

    def _notify(msg: str):
        if progress_cb:
            try:
                progress_cb(completed_brands, total_brands, msg)
            except Exception:
                pass

    _notify("Iniciando varredura ao vivo das 10 principais marcas...")

    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as executor:
        future_map = {executor.submit(fn): (tid, label) for tid, label, fn in tasks}

        for fut in concurrent.futures.as_completed(future_map):
            tid, label = future_map[fut]
            if tid == "proink_inkit":
                try:
                    dual = fut.result()
                    for sub_id in ("inkit", "proink"):
                        b_entries, repo_url, msg = dual[sub_id]
                        if not b_entries:
                            raise RuntimeError("Lista vazia retornada")
                        meta = meta_by_id[sub_id]
                        all_entries.extend(b_entries)
                        printers_n = len({(e.printer_brand, e.printer_model) for e in b_entries})
                        reports_by_id[sub_id] = BrandScanReport(
                            ink_brand=meta["name"],
                            origin=meta["origin"],
                            official_url=meta["official_url"],
                            discovered_repo_url=repo_url,
                            hosting_summary=meta["hosting"],
                            status="online",
                            profiles_count=len(b_entries),
                            printers_count=printers_n,
                            scanned_at=now_str,
                            message=msg,
                        )
                except Exception as exc:
                    for sub_id in ("inkit", "proink"):
                        meta = meta_by_id[sub_id]
                        fb = _fallback_entries_for_brand(sub_id)
                        all_entries.extend(fb)
                        reports_by_id[sub_id] = BrandScanReport(
                            ink_brand=meta["name"],
                            origin=meta["origin"],
                            official_url=meta["official_url"],
                            discovered_repo_url=meta["official_url"],
                            hosting_summary=meta["hosting"],
                            status="fallback",
                            profiles_count=len(fb),
                            printers_count=len({(e.printer_brand, e.printer_model) for e in fb}),
                            scanned_at=now_str,
                            message=f"Usando índice local ({type(exc).__name__})",
                        )
                completed_brands += 2
                _notify("Varredura concluída: Proink & Ink It (NanoSub)")
            else:
                meta = meta_by_id[tid]
                try:
                    b_entries, repo_url, msg = fut.result()
                    if not b_entries:
                        raise RuntimeError("Nenhum perfil retornado")
                    all_entries.extend(b_entries)
                    printers_n = len({(e.printer_brand, e.printer_model) for e in b_entries})
                    reports_by_id[tid] = BrandScanReport(
                        ink_brand=meta["name"],
                        origin=meta["origin"],
                        official_url=meta["official_url"],
                        discovered_repo_url=repo_url,
                        hosting_summary=meta["hosting"],
                        status="online",
                        profiles_count=len(b_entries),
                        printers_count=printers_n,
                        scanned_at=now_str,
                        message=msg,
                    )
                except Exception as exc:
                    fb = _fallback_entries_for_brand(tid)
                    all_entries.extend(fb)
                    reports_by_id[tid] = BrandScanReport(
                        ink_brand=meta["name"],
                        origin=meta["origin"],
                        official_url=meta["official_url"],
                        discovered_repo_url=meta["official_url"],
                        hosting_summary=meta["hosting"],
                        status="fallback",
                        profiles_count=len(fb),
                        printers_count=len({(e.printer_brand, e.printer_model) for e in fb}),
                        scanned_at=now_str,
                        message=f"Usando índice local ({type(exc).__name__})",
                    )
                completed_brands += 1
                _notify(f"Varredura concluída: {label}")

    ordered_reports = [reports_by_id[b["id"]] for b in TOP_10_INK_BRANDS if b["id"] in reports_by_id]
    save_cache(all_entries, ordered_reports)
    return all_entries, ordered_reports


def save_cache(entries: List[ProfileEntry], reports: List[BrandScanReport]) -> None:
    payload = {
        "updated_at": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
        "reports": [asdict(r) for r in reports],
        "entries": [asdict(e) for e in entries],
    }
    try:
        with open(CACHE_PATH, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)
    except Exception:
        pass


def load_cache() -> Optional[Tuple[List[ProfileEntry], List[BrandScanReport], str]]:
    if not os.path.exists(CACHE_PATH):
        return None
    try:
        with open(CACHE_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        entries = [ProfileEntry(**item) for item in data.get("entries", [])]
        reports = [BrandScanReport(**item) for item in data.get("reports", [])]
        updated_at = data.get("updated_at", "")
        if entries:
            return entries, reports, updated_at
    except Exception:
        pass
    return None


def build_seed_catalog() -> Tuple[List[ProfileEntry], List[BrandScanReport]]:
    """Gera catálogo base imediato enquanto a primeira varredura ao vivo roda em segundo plano."""
    entries: List[ProfileEntry] = []
    reports: List[BrandScanReport] = []
    for meta in TOP_10_INK_BRANDS:
        fb = _fallback_entries_for_brand(meta["id"])
        entries.extend(fb)
        reports.append(BrandScanReport(
            ink_brand=meta["name"],
            origin=meta["origin"],
            official_url=meta["official_url"],
            discovered_repo_url=meta["official_url"],
            hosting_summary=meta["hosting"],
            status="fallback",
            profiles_count=len(fb),
            printers_count=len({(e.printer_brand, e.printer_model) for e in fb}),
            scanned_at="Aguardando varredura",
            message="Pronto para varrer na internet",
        ))
    return entries, reports


class CatalogIndex:
    """Estrutura de consulta rápida na hierarquia:
    Marca de Impressora > Modelo de Impressora > Marca de Tinta
    """

    BRAND_PRIORITY = {"Epson": 0, "Sawgrass": 1, "Canon": 2, "HP": 3, "Brother": 4}

    def __init__(self, entries: List[ProfileEntry]):
        self.tree: Dict[str, Dict[str, Dict[str, List[ProfileEntry]]]] = {}
        self.total_entries = len(entries)
        for e in entries:
            models_map = self.tree.setdefault(e.printer_brand, {})
            inks_map = models_map.setdefault(e.printer_model, {})
            bucket = inks_map.setdefault(e.ink_brand, [])
            if not any(x.profile_name == e.profile_name and x.download_url == e.download_url for x in bucket):
                bucket.append(e)

    def get_printer_brands(self) -> List[str]:
        return sorted(
            self.tree.keys(),
            key=lambda b: (self.BRAND_PRIORITY.get(b, 99), b.lower()),
        )

    def get_printer_models(self, printer_brand: str) -> List[str]:
        models_map = self.tree.get(printer_brand, {})
        return sorted(models_map.keys(), key=model_sort_key)

    def get_ink_brands(self, printer_brand: str, printer_model: str) -> List[str]:
        inks_map = self.tree.get(printer_brand, {}).get(printer_model, {})
        order = {b["name"]: idx for idx, b in enumerate(TOP_10_INK_BRANDS)}
        return sorted(inks_map.keys(), key=lambda k: (order.get(k, 99), k.lower()))

    def get_profiles(self, printer_brand: str, printer_model: str, ink_brand: str) -> List[ProfileEntry]:
        return list(self.tree.get(printer_brand, {}).get(printer_model, {}).get(ink_brand, []))

    def count_models(self) -> int:
        return sum(len(m) for m in self.tree.values())


# ---------------------------------------------------------------------------
# Download direto e validação de cabeçalho ICC/ICM ('acsp')
# ---------------------------------------------------------------------------

def _sanitize_filename(name: str) -> str:
    cleaned = re.sub(r'[<>:"/\\|?*]+', "_", name).strip()
    return cleaned or f"perfil_{int(time.time())}.icc"


def is_valid_icc_bytes(data: bytes) -> bool:
    """Todo perfil ICC/ICM válido possui a assinatura ASCII 'acsp' nos bytes 36..40 (ISO 15076-1)."""
    return len(data) >= 128 and data[36:40] == b"acsp"


def download_profile_file(entry: ProfileEntry, dest_root: str = DOWNLOADS_DIR) -> Tuple[bool, str, List[str]]:
    """Baixa um arquivo .icc/.icm/.zip/.rar direto para `downloads/<MarcaTinta>/<Impressora>/`.

    Retorna: (sucesso, mensagem, lista_de_arquivos_salvos)
    """
    if entry.delivery_type not in ("direct_icc", "direct_archive"):
        return False, "Este item aponta para um portal/pasta na nuvem — abra a fonte oficial.", []

    brand_folder = _sanitize_filename(entry.ink_brand)
    model_folder = _sanitize_filename(f"{entry.printer_brand}_{entry.printer_model}")
    target_dir = os.path.join(dest_root, brand_folder, model_folder)
    os.makedirs(target_dir, exist_ok=True)

    req = urllib.request.Request(entry.download_url, headers=HTTP_HEADERS)
    with urllib.request.urlopen(req, timeout=25) as resp:
        content_disp = resp.headers.get("Content-Disposition", "")
        raw_bytes = resp.read()

    # Caso o Google Drive retorne página HTML de confirmação em arquivos grandes
    if raw_bytes[:200].lstrip().lower().startswith((b"<!doctype html", b"<html")):
        return (
            False,
            "O servidor solicitou confirmação pelo navegador. Abrindo ou acesse pela Fonte Oficial.",
            [],
        )

    fname = entry.profile_name
    m_cd = re.search(r'filename\*?=(?:UTF-8\'\')?["\']?([^"\';\r\n]+)', content_disp, re.I)
    if m_cd:
        fname = urllib.parse.unquote(m_cd.group(1)).strip()
    fname = _sanitize_filename(fname)

    saved_files: List[str] = []

    # Se for arquivo ZIP, extrai automaticamente os .icc/.icm de dentro dele!
    if fname.lower().endswith(".zip") or raw_bytes[:4] == b"PK\x03\x04":
        zip_path = os.path.join(target_dir, fname if fname.lower().endswith(".zip") else f"{fname}.zip")
        with open(zip_path, "wb") as f:
            f.write(raw_bytes)
        saved_files.append(zip_path)

        extracted_icc = []
        try:
            with zipfile.ZipFile(io.BytesIO(raw_bytes)) as zf:
                for member in zf.infolist():
                    if member.is_dir():
                        continue
                    base_member = _sanitize_filename(os.path.basename(member.filename))
                    if base_member.lower().endswith((".icc", ".icm")):
                        out_path = os.path.join(target_dir, base_member)
                        with open(out_path, "wb") as out_f:
                            out_f.write(zf.read(member))
                        extracted_icc.append(out_path)
        except Exception:
            pass

        if extracted_icc:
            return (
                True,
                f"Pacote ZIP baixado e {len(extracted_icc)} perfil(is) .icc/.icm extraído(s) com sucesso!",
                extracted_icc,
            )
        return True, f"Pacote salvo em: {zip_path}", saved_files

    out_path = os.path.join(target_dir, fname)
    with open(out_path, "wb") as f:
        f.write(raw_bytes)
    saved_files.append(out_path)

    if out_path.lower().endswith((".icc", ".icm")) and is_valid_icc_bytes(raw_bytes):
        return True, f"Perfil ICC autêntico verificado (assinatura 'acsp') e salvo: {fname}", saved_files

    return True, f"Arquivo salvo com sucesso: {fname}", saved_files
