import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
import urllib.error
import urllib.request

from core.version import VERSION, GITHUB_REPO

API_URL = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"
RELEASES_PAGE = f"https://github.com/{GITHUB_REPO}/releases/latest"
_HEADERS = {"User-Agent": "OpenMug-Studio-Updater", "Accept": "application/vnd.github+json"}


class UpdateError(Exception):
    pass


def parse_version(text):
    """Converte 'v1.2.3' em (1, 2, 3). Retorna None se não for uma versão válida."""
    match = re.search(r"(\d+(?:\.\d+)*)", text or "")
    if not match:
        return None
    return tuple(int(p) for p in match.group(1).split("."))


def markdown_to_text(md):
    """Converte o Markdown das release notes em texto simples legível (para caixas de diálogo)."""
    lines = []
    for raw in (md or "").replace("\r\n", "\n").split("\n"):
        line = raw.rstrip()
        # Títulos: '## Novidades' -> 'NOVIDADES'
        heading = re.match(r"^\s{0,3}#{1,6}\s+(.*?)\s*#*\s*$", line)
        if heading:
            if lines and lines[-1] != "":
                lines.append("")
            lines.append(heading.group(1).upper())
            continue
        # Listas: '- item' / '* item' -> '• item'
        line = re.sub(r"^(\s*)[-*+]\s+", lambda m: m.group(1) + "• ", line)
        # Links, imagens e formatação inline
        line = re.sub(r"!?\[([^\]]*)\]\([^)]*\)", r"\1", line)
        line = re.sub(r"(\*\*|__)(.+?)\1", r"\2", line)
        line = re.sub(r"(?<![\w*])[*_](?!\s)(.+?)(?<!\s)[*_](?![\w*])", r"\1", line)
        line = re.sub(r"`([^`]*)`", r"\1", line)
        lines.append(line)
    text = "\n".join(lines)
    return re.sub(r"\n{3,}", "\n\n", text).strip()


def fetch_release_notes(version=VERSION, timeout=10):
    """Busca as notas da release da versão informada. Retorna o texto ou None se não houver release/notas."""
    for tag in (f"v{version}", version):
        url = f"https://api.github.com/repos/{GITHUB_REPO}/releases/tags/{tag}"
        try:
            req = urllib.request.Request(url, headers=_HEADERS)
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                data = json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            if e.code == 404:
                continue
            raise UpdateError(f"Não foi possível consultar o GitHub (erro HTTP {e.code}).")
        except Exception as e:
            raise UpdateError(f"Não foi possível consultar o GitHub. Verifique sua conexão com a internet.\n{e}")
        text = markdown_to_text(data.get("body"))
        return text or None
    return None


def is_frozen():
    """True quando rodando como executável (PyInstaller)."""
    return bool(getattr(sys, "frozen", False))


def check_for_update(timeout=10):
    """Consulta a última release. Retorna um dict com os dados se houver versão nova, senão None."""
    try:
        req = urllib.request.Request(API_URL, headers=_HEADERS)
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        if e.code == 404:
            # Repositório sem nenhuma release publicada: não há atualização disponível
            return None
        raise UpdateError(f"Não foi possível consultar o GitHub (erro HTTP {e.code}).")
    except Exception as e:
        raise UpdateError(f"Não foi possível consultar o GitHub. Verifique sua conexão com a internet.\n{e}")

    latest = parse_version(data.get("tag_name", ""))
    current = parse_version(VERSION)
    if latest is None or current is None or latest <= current:
        return None

    asset = next((a for a in data.get("assets", []) if a.get("name", "").lower().endswith(".exe")), None)
    return {
        "version": data["tag_name"].lstrip("vV"),
        "notes": markdown_to_text(data.get("body")),
        "url": asset["browser_download_url"] if asset else None,
        "size": asset.get("size") if asset else None,
        "digest": asset.get("digest") if asset else None,
    }


def download_update(info, progress_callback=None):
    """Baixa o novo executável ao lado do atual e retorna o caminho do arquivo baixado."""
    if not info.get("url"):
        raise UpdateError("A release não possui um arquivo .exe anexado.")

    target_dir = os.path.dirname(sys.executable) if is_frozen() else tempfile.gettempdir()
    new_path = os.path.join(target_dir, "OpenMug Studio.exe.new")

    try:
        req = urllib.request.Request(info["url"], headers=_HEADERS)
        sha = hashlib.sha256()
        with urllib.request.urlopen(req, timeout=30) as resp, open(new_path, "wb") as out:
            total = int(resp.headers.get("Content-Length") or info.get("size") or 0)
            done = 0
            while True:
                chunk = resp.read(1024 * 256)
                if not chunk:
                    break
                out.write(chunk)
                sha.update(chunk)
                done += len(chunk)
                if progress_callback and total:
                    progress_callback(done / total)
    except Exception as e:
        _remove(new_path)
        raise UpdateError(f"Falha ao baixar a atualização.\n{e}")

    # Validações de integridade
    expected_size = info.get("size")
    if expected_size and os.path.getsize(new_path) != expected_size:
        _remove(new_path)
        raise UpdateError("O arquivo baixado está incompleto.")
    with open(new_path, "rb") as f:
        if f.read(2) != b"MZ":
            _remove(new_path)
            raise UpdateError("O arquivo baixado não é um executável válido.")
    digest = info.get("digest") or ""
    if digest.startswith("sha256:") and digest.split(":", 1)[1].lower() != sha.hexdigest():
        _remove(new_path)
        raise UpdateError("A verificação de integridade (SHA-256) falhou.")

    return new_path


def apply_update(new_path):
    """Cria um script que espera o app fechar, troca o executável e o reabre. O app deve fechar logo depois."""
    if not is_frozen():
        raise UpdateError("A atualização automática só funciona no executável.")

    exe_path = os.path.abspath(sys.executable)
    bat_path = os.path.join(tempfile.gettempdir(), "openmug_update.bat")
    script = (
        "@echo off\r\n"
        "set tries=0\r\n"
        ":retry\r\n"
        "timeout /t 1 /nobreak >nul\r\n"
        f'move /y "{new_path}" "{exe_path}" >nul 2>&1\r\n'
        "if errorlevel 1 (\r\n"
        "  set /a tries+=1\r\n"
        "  if %tries% lss 30 goto retry\r\n"
        "  exit /b 1\r\n"
        ")\r\n"
        "timeout /t 2 /nobreak >nul\r\n"
        f'start "" "{exe_path}"\r\n'
        '(goto) 2>nul & del "%~f0"\r\n'
    )
    with open(bat_path, "w", encoding="mbcs") as f:
        f.write(script)

    # Remove variáveis do PyInstaller para o novo executável extrair seus próprios arquivos
    env = {k: v for k, v in os.environ.items() if not (k.startswith("_PYI") or k.startswith("_MEIPASS"))}
    subprocess.Popen(
        ["cmd", "/c", bat_path],
        env=env,
        creationflags=subprocess.CREATE_NO_WINDOW | subprocess.DETACHED_PROCESS,
        close_fds=True,
    )


def _remove(path):
    try:
        os.remove(path)
    except OSError:
        pass

