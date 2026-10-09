import os
import sys
import customtkinter as ctk
from tkinter import filedialog, messagebox
from PIL import Image

from core.config_manager import ConfigManager
from core.image_processor import ImageProcessor
from gui.preview_window import PreviewWindow

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("OpenMug Studio")
        try:
            self.iconbitmap(resource_path("OpenMug Studio.ico"))
        except:
            pass
        self.geometry("850x700")
        self.resizable(True, True)
        self.configure(fg_color="#0F172A")

        self.config_manager = ConfigManager()
        self.image_processor = ImageProcessor()
        
        # Armazena os dados das 3 imagens
        self.images_data = [
            {"path": "", "mode": "Redimensionar", "label_ref": None, "thumb_ref": None, "actions_frame_ref": None, "combo_mode_ref": None},
            {"path": "", "mode": "Redimensionar", "label_ref": None, "thumb_ref": None, "actions_frame_ref": None, "combo_mode_ref": None},
            {"path": "", "mode": "Redimensionar", "label_ref": None, "thumb_ref": None, "actions_frame_ref": None, "combo_mode_ref": None}
        ]

        self._build_ui()
        
        # Iniciar maximizado no Windows
        if os.name == 'nt':
            self.after(0, lambda: self.state('zoomed'))

    def _build_ui(self):
        """Constrói a interface gráfica do aplicativo com Card Design (Midnight CMYK)."""
        
        # --- TÍTULO DO APP ---
        img_icon = None
        try:
            icon_img = Image.open(resource_path("OpenMug Studio.ico"))
            img_icon = ctk.CTkImage(light_image=icon_img, dark_image=icon_img, size=(32, 32))
        except Exception:
            pass

        if img_icon:
            self.lbl_main_title = ctk.CTkLabel(self, text=" OpenMug Studio", font=ctk.CTkFont(size=28, weight="bold"), 
                                               text_color="#F8FAFC", image=img_icon, compound="left")
        else:
            self.lbl_main_title = ctk.CTkLabel(self, text="☕ OpenMug Studio", font=ctk.CTkFont(size=28, weight="bold"), 
                                               text_color="#F8FAFC")
            
        self.lbl_main_title.pack(pady=15)

        # --- SEÇÃO DE PERFIS ICC (Topo) ---
        self.icc_card = ctk.CTkFrame(self, fg_color="#1E293B", corner_radius=10)
        self.icc_card.pack(pady=(0, 10), padx=20, fill="x")

        self.btn_icc = ctk.CTkButton(self.icc_card, text="Procurar Perfil ICC", command=self.select_icc, 
                                     fg_color="#06B6D4", hover_color="#0891B2", text_color="black", font=ctk.CTkFont(weight="bold"))
        self.btn_icc.pack(side="left", padx=15, pady=15)

        icc_display = self.config_manager.icc_profile_path if self.config_manager.icc_profile_path else "Nenhum perfil selecionado"
        self.lbl_icc = ctk.CTkLabel(self.icc_card, text=icc_display, text_color="#94A3B8", wraplength=500)
        self.lbl_icc.pack(side="left", padx=10, pady=15)

        self.btn_clear_icc = ctk.CTkButton(self.icc_card, text="✖", width=30, height=30, fg_color="transparent", 
                                           hover_color="#B71C1C", text_color="#94A3B8", command=self.clear_icc)
        if self.config_manager.icc_profile_path:
            self.btn_clear_icc.pack(side="right", padx=15, pady=15)

        # --- SEÇÃO DE IMAGENS (Meio) ---
        self.images_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.images_frame.pack(pady=5, padx=20, fill="both", expand=True)

        for i in range(3):
            # Cria um "Card" para cada arte
            card_frame = ctk.CTkFrame(self.images_frame, fg_color="#1E293B", corner_radius=10)
            card_frame.pack(pady=10, padx=0, fill="x")

            # 1. Miniatura (Extrema Esquerda)
            lbl_thumb = ctk.CTkLabel(card_frame, text="Sem Imagem", width=210, height=95, fg_color="#0F172A", text_color="#94A3B8", corner_radius=8)
            lbl_thumb.pack(side="left", padx=15, pady=15)

            # 2. Controles Principais (Centro - Expandido)
            middle_frame = ctk.CTkFrame(card_frame, fg_color="transparent")
            middle_frame.pack(side="left", fill="x", expand=True, padx=10, pady=10)

            lbl_title = ctk.CTkLabel(middle_frame, text=f"Arte {i+1}", font=ctk.CTkFont(size=16, weight="bold"), text_color="#F8FAFC")
            lbl_title.pack(anchor="w", pady=(0, 5))

            btn_img = ctk.CTkButton(middle_frame, text="Escolher Imagem", command=lambda idx=i: self.select_image(idx), 
                                    fg_color="#334155", hover_color="#475569", text_color="#F8FAFC")
            btn_img.pack(anchor="w", pady=5)

            lbl_path = ctk.CTkLabel(middle_frame, text="Nenhuma imagem selecionada", text_color="#94A3B8", anchor="w")
            lbl_path.pack(anchor="w", pady=(5, 0))

            # 3. Configurações da Arte (Extrema Direita)
            right_frame = ctk.CTkFrame(card_frame, fg_color="transparent")
            right_frame.pack(side="right", padx=20, pady=10)

            lbl_mode = ctk.CTkLabel(right_frame, text="Modo de Encaixe:", text_color="#94A3B8")
            lbl_mode.pack(anchor="e", pady=(0, 2))

            combo_mode = ctk.CTkComboBox(right_frame, values=["Cortar", "Redimensionar"], 
                                         command=lambda val, idx=i: self.set_image_mode(val, idx),
                                         fg_color="#334155", border_color="#475569", button_color="#334155", text_color="#F8FAFC")
            combo_mode.set(self.images_data[i]["mode"])
            combo_mode.pack(anchor="e", pady=(0, 10))

            actions_frame = ctk.CTkFrame(right_frame, fg_color="transparent")
            
            btn_duplicate = ctk.CTkButton(actions_frame, text="⧉ Duplicar", width=80, 
                                          fg_color="#005b9f", hover_color="#003f6f",
                                          command=lambda idx=i: self.duplicate_image(idx))
            btn_duplicate.pack(side="left", padx=(0, 5))

            btn_clear = ctk.CTkButton(actions_frame, text="✖ Limpar", width=80, 
                                      fg_color="#B71C1C", hover_color="#8B0000",
                                      command=lambda idx=i: self.remove_image(idx))
            btn_clear.pack(side="left")

            self.images_data[i]["label_ref"] = lbl_path
            self.images_data[i]["thumb_ref"] = lbl_thumb
            self.images_data[i]["actions_frame_ref"] = actions_frame
            self.images_data[i]["combo_mode_ref"] = combo_mode

        # --- SEÇÃO DE AÇÃO E PRÉVIA (Base) ---
        self.bottom_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.bottom_frame.pack(pady=(10, 20), padx=20, fill="x")

        # Container para centralizar os botões
        buttons_frame = ctk.CTkFrame(self.bottom_frame, fg_color="transparent")
        buttons_frame.pack(pady=5)

        self.btn_preview = ctk.CTkButton(buttons_frame, text="Gerar Prévia", 
                                         command=self.generate_preview, height=50, width=300, corner_radius=8,
                                         fg_color="#06B6D4", hover_color="#0891B2", text_color="black",
                                         font=ctk.CTkFont(size=18, weight="bold"))
        self.btn_preview.pack(side="left", padx=10)

        self.btn_clear_all = ctk.CTkButton(buttons_frame, text="🗑 Limpar Tudo", 
                                           command=self.clear_all_images, height=50, width=150, corner_radius=8,
                                           fg_color="#333333", hover_color="#555555", state="disabled", text_color="#F8FAFC",
                                           font=ctk.CTkFont(size=14, weight="bold"))
        self.btn_clear_all.pack(side="left", padx=10)

    def select_icc(self):
        filepath = filedialog.askopenfilename(
            title="Selecione o Perfil ICC",
            filetypes=[("Perfis ICC", "*.icc *.icm"), ("Todos os arquivos", "*.*")]
        )
        if filepath:
            self.config_manager.save_config(filepath)
            self.lbl_icc.configure(text=filepath)
            self.btn_clear_icc.pack(side="right", padx=15, pady=15)

    def clear_icc(self):
        self.config_manager.save_config("")
        self.lbl_icc.configure(text="Nenhum perfil selecionado")
        self.btn_clear_icc.pack_forget()

    def select_image(self, index):
        filepath = filedialog.askopenfilename(
            title=f"Selecione a Arte {index+1}",
            filetypes=[("Imagens", "*.png *.jpg *.jpeg *.tif *.tiff *.bmp"), ("Todos os arquivos", "*.*")]
        )
        if filepath:
            self.images_data[index]["path"] = filepath
            filename = os.path.basename(filepath)
            self.images_data[index]["label_ref"].configure(text=filename)
            
            # Força o reset para "Redimensionar" ao escolher/substituir a imagem
            self.images_data[index]["mode"] = "Redimensionar"
            if self.images_data[index]["combo_mode_ref"]:
                self.images_data[index]["combo_mode_ref"].set("Redimensionar")

            # Gera a miniatura (Thumbnail)
            try:
                with Image.open(filepath) as img:
                    img_copy = img.copy()
                    img_copy.thumbnail((210, 95), Image.Resampling.LANCZOS)
                    # CTkImage garante uma renderização bonita e fácil de atualizar
                    thumb_tk = ctk.CTkImage(light_image=img_copy, dark_image=img_copy, size=(img_copy.width, img_copy.height))
                    self.images_data[index]["thumb_ref"].configure(image=thumb_tk, text="")
                    
                    # Exibe os botões de ação da imagem (Limpar e Duplicar)
                    self.images_data[index]["actions_frame_ref"].pack(anchor="e")
                    
                    self.update_clear_all_state()
            except Exception as e:
                print(f"Erro ao carregar miniatura: {e}")

    def remove_image(self, index):
        """Remove a imagem do bloco selecionado e esconde os botões de ação."""
        self.images_data[index]["path"] = ""
        self.images_data[index]["label_ref"].configure(text="Nenhuma imagem selecionada")
        self.images_data[index]["thumb_ref"].configure(image="", text="Sem Imagem")
        self.images_data[index]["actions_frame_ref"].pack_forget()
        
        # Reseta o modo para "Redimensionar" ao limpar
        self.images_data[index]["mode"] = "Redimensionar"
        if self.images_data[index]["combo_mode_ref"]:
            self.images_data[index]["combo_mode_ref"].set("Redimensionar")
            
        self.update_clear_all_state()

    def duplicate_image(self, index):
        """Duplica a imagem para um slot livre, ou para o slot logo abaixo caso não haja livres."""
        current_data = self.images_data[index]
        if not current_data["path"]:
            return

        # Verifica slot livre
        target_index = -1
        for i in range(3):
            if not self.images_data[i]["path"]:
                target_index = i
                break
        
        # Sem slot livre, copia para o slot abaixo
        if target_index == -1:
            target_index = (index + 1) % 3

        # Executa a duplicação
        target_path = current_data["path"]
        self.images_data[target_index]["path"] = target_path
        self.images_data[target_index]["label_ref"].configure(text=os.path.basename(target_path))
        
        # Duplica também o modo de encaixe
        target_mode = current_data["mode"]
        self.images_data[target_index]["mode"] = target_mode
        if self.images_data[target_index]["combo_mode_ref"]:
            self.images_data[target_index]["combo_mode_ref"].set(target_mode)

        try:
            with Image.open(target_path) as img:
                img_copy = img.copy()
                img_copy.thumbnail((210, 95), Image.Resampling.LANCZOS)
                thumb_tk = ctk.CTkImage(light_image=img_copy, dark_image=img_copy, size=(img_copy.width, img_copy.height))
                self.images_data[target_index]["thumb_ref"].configure(image=thumb_tk, text="")
                self.images_data[target_index]["actions_frame_ref"].pack(anchor="e")
                self.update_clear_all_state()
        except Exception as e:
            print(f"Erro ao duplicar miniatura: {e}")

    def update_clear_all_state(self):
        """Ativa ou desativa o botão de limpar tudo com base nas imagens."""
        has_image = any(item["path"] != "" for item in self.images_data)
        if has_image:
            self.btn_clear_all.configure(state="normal", fg_color="#8B0000") # Vermelho Escuro Discreto
        else:
            self.btn_clear_all.configure(state="disabled", fg_color="#333333") # Cinza

    def clear_all_images(self):
        """Remove todas as imagens de uma só vez."""
        for i in range(3):
            self.remove_image(i)

    def set_image_mode(self, value, index):
        self.images_data[index]["mode"] = value

    def generate_preview(self):
        # Validações antes de processar

        has_image = any(item["path"] for item in self.images_data)
        if not has_image:
            messagebox.showwarning("Aviso", "Por favor, selecione pelo menos uma imagem para montagem.")
            return

        try:
            # Chama o core para montar e aplicar o perfil
            a4_final = self.image_processor.process_and_assemble(
                self.images_data, 
                self.config_manager.icc_profile_path
            )
            
            # 4. Exibe a janela de prévia
            PreviewWindow(
                self, 
                a4_final, 
                self.config_manager.temp_dir, 
                self.image_processor.a4_width, 
                self.image_processor.a4_height
            )

        except Exception as e:
            messagebox.showerror("Erro no Processamento", f"Ocorreu um erro ao montar a arte:\n{str(e)}")
