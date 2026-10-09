import os
import json

class ConfigManager:
    def __init__(self):
        self.config_file = "config.json"
        self.temp_dir = "temp"
        self.icc_profile_path = ""
        self._create_directories()
        self._load_config()

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
