import os
import sys
import json
import shutil
import atexit

class ConfigManager:
    def __init__(self):
        # Usa a pasta do executável (quando compilado) ou a raiz do projeto para evitar caminhos relativos soltos
        base_dir = os.path.dirname(sys.executable) if getattr(sys, "frozen", False) else os.path.abspath(".")
        self.config_file = os.path.join(base_dir, "config.json")
        self.temp_dir = os.path.join(base_dir, "temp")
        self.icc_profile_path = ""
        self._create_directories()
        self._load_config()
        atexit.register(self.cleanup_temp)

    def _create_directories(self):
        """Cria a pasta temporária e tenta ocultá-la no Windows."""
        if not os.path.exists(self.temp_dir):
            try:
                os.makedirs(self.temp_dir)
                if os.name == 'nt':
                    import ctypes
                    FILE_ATTRIBUTE_HIDDEN = 0x02
                    ctypes.windll.kernel32.SetFileAttributesW(self.temp_dir, FILE_ATTRIBUTE_HIDDEN)
            except Exception as e:
                print(f"Erro ao criar/ocultar pasta temp: {e}")

    def _load_config(self):
        """Lê as preferências salvas no config.json."""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, "r", encoding="utf-8") as f:
                    config = json.load(f)
                    self.icc_profile_path = config.get("icc_profile", "")
            except Exception as e:
                print(f"Erro ao ler config.json: {e}")

    def save_config(self, new_icc_path):
        """Salva as preferências no config.json."""
        self.icc_profile_path = new_icc_path
        config = {"icc_profile": self.icc_profile_path}
        try:
            with open(self.config_file, "w", encoding="utf-8") as f:
                json.dump(config, f, ensure_ascii=False, indent=4)
        except Exception as e:
            print(f"Erro ao salvar config.json: {e}")

    def cleanup_temp(self):
        """Limpa todos os arquivos e subpastas dentro da pasta temp ao fechar o programa."""
        if not os.path.isdir(self.temp_dir):
            return
        for entry in os.listdir(self.temp_dir):
            full_path = os.path.join(self.temp_dir, entry)
            try:
                if os.path.isfile(full_path) or os.path.islink(full_path):
                    os.remove(full_path)
                elif os.path.isdir(full_path):
                    shutil.rmtree(full_path, ignore_errors=True)
            except OSError:
                # Caso algum PDF ainda esteja aberto no leitor no instante do fechamento, ignora sem travar
                pass
