import os
import sys
import json
import customtkinter as ctk
from tkinter import filedialog, messagebox
from PIL import Image, ImageCms, ImageTk, ImageOps

# Configurações do CustomTkinter
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("OpenMug Studio")
        try:
            self.iconbitmap("OpenMug Studio.ico")
        except:
            pass
        self.geometry("850x700")
        self.resizable(True, True)
        self.configure(fg_color="#0F172A")

        self.config_file = "config.json"
        self.temp_dir = "temp"
        self.icc_profile_path = ""
        
        # Armazena os dados das 3 imagens
        self.images_data = [
            {"path": "", "mode": "Redimensionar", "label_ref": None, "thumb_ref": None, "actions_frame_ref": None, "combo_mode_ref": None},
            {"path": "", "mode": "Redimensionar", "label_ref": None, "thumb_ref": None, "actions_frame_ref": None, "combo_mode_ref": None},
            {"path": "", "mode": "Redimensionar", "label_ref": None, "thumb_ref": None, "actions_frame_ref": None, "combo_mode_ref": None}
        ]
        
        # Resoluções Fixas (300 DPI)
        self.a4_width = 2480
        self.a4_height = 3508
        self.mug_width = 2362  # Reduzido para 20cm garantindo margens laterais seguras
        self.mug_height = 1122

        self._create_directories()
        self._load_config()
        self._build_ui()
        
        # Iniciar maximizado no Windows
        if os.name == 'nt':
            self.after(0, lambda: self.state('zoomed'))

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

    def _save_config(self):
        """Salva as preferências no config.json."""
        config = {"icc_profile": self.icc_profile_path}
        try:
            with open(self.config_file, "w", encoding="utf-8") as f:
                json.dump(config, f, ensure_ascii=False, indent=4)
        except Exception as e:
            print(f"Erro ao salvar config.json: {e}")

    def _build_ui(self):
        """Constrói a interface gráfica do aplicativo com Card Design (Midnight CMYK)."""
        
        # --- TÍTULO DO APP ---
        img_icon = None
        try:
            icon_img = Image.open("OpenMug Studio.ico")
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

        icc_display = self.icc_profile_path if self.icc_profile_path else "Nenhum perfil selecionado"
        self.lbl_icc = ctk.CTkLabel(self.icc_card, text=icc_display, text_color="#94A3B8", wraplength=500)
        self.lbl_icc.pack(side="left", padx=10, pady=15)

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
            self.icc_profile_path = filepath
            self.lbl_icc.configure(text=filepath)
            self._save_config()

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
        if not self.icc_profile_path or not os.path.exists(self.icc_profile_path):
            messagebox.showwarning("Aviso", "Por favor, selecione um perfil ICC válido antes de continuar.")
            return

        has_image = any(item["path"] for item in self.images_data)
        if not has_image:
            messagebox.showwarning("Aviso", "Por favor, selecione pelo menos uma imagem para montagem.")
            return

        try:
            # 1. Cria a folha A4 em branco (Fundo Branco Puro, RGB)
            a4_image = Image.new("RGB", (self.a4_width, self.a4_height), "white")
            
            # Espaçamento igual entre as imagens e as bordas
            spacing = (self.a4_height - (3 * self.mug_height)) // 4
            y_offsets = [
                spacing,
                spacing + self.mug_height + spacing,
                spacing + 2 * self.mug_height + 2 * spacing
            ]

            # 2. Processa cada imagem e cola no fundo A4
            x_offset = (self.a4_width - self.mug_width) // 2
            
            for i, data in enumerate(self.images_data):
                img_path = data["path"]
                if img_path and os.path.exists(img_path):
                    with Image.open(img_path) as img:
                        if img.mode != "RGB":
                            img = img.convert("RGB")
                        
                        mode = data["mode"]
                        if mode == "Cortar":
                            # Corta pelo centro preservando a proporção
                            processed_img = ImageOps.fit(img, (self.mug_width, self.mug_height), 
                                                         method=Image.Resampling.LANCZOS, centering=(0.5, 0.5))
                        else:
                            # Estica para forçar o tamanho exato
                            processed_img = img.resize((self.mug_width, self.mug_height), Image.Resampling.LANCZOS)
                        
                        a4_image.paste(processed_img, (x_offset, y_offsets[i]))

            # 3. Aplica o Perfil ICC antes da prévia
            srgb_profile = ImageCms.createProfile("sRGB")
            try:
                target_profile = ImageCms.getOpenProfile(self.icc_profile_path)
                a4_final = ImageCms.profileToProfile(
                    a4_image,
                    srgb_profile,
                    target_profile,
                    renderingIntent=0,
                    outputMode='RGB'
                )
            except Exception as icc_err:
                messagebox.showwarning("Aviso ICC", f"Não foi possível aplicar o perfil ICC. Mostrando imagem sem conversão.\n{str(icc_err)}")
                a4_final = a4_image

            # 4. Exibe a janela de prévia (Já com as cores convertidas)
            self.show_preview_window(a4_final)

        except Exception as e:
            messagebox.showerror("Erro no Processamento", f"Ocorreu um erro ao montar a arte:\n{str(e)}")

    def show_preview_window(self, a4_final_image):
        preview_win = ctk.CTkToplevel(self)
        preview_win.title("Layout de Impressão (Prévia)")
        
        try:
            preview_win.after(200, lambda: preview_win.iconbitmap("OpenMug Studio.ico"))
        except:
            pass
        
        # Maximizando a Janela e forçando ancoragem em 0,0 para evitar bugs do Windows
        if os.name == 'nt':
            preview_win.geometry(f"{self.winfo_screenwidth()}x{self.winfo_screenheight()}+0+0")
            preview_win.after(200, lambda: preview_win.state('zoomed'))
        else:
            preview_win.geometry(f"{self.winfo_screenwidth()}x{self.winfo_screenheight()}+0+0")
            
        preview_win.grab_set() 

        # Define Fundo da janela (CMYK Midnight)
        preview_win.configure(fg_color="#0F172A")

        # Container para centralizar a "Folha de Papel"
        preview_frame = ctk.CTkFrame(preview_win, fg_color="transparent")
        preview_frame.pack(expand=True, fill="both", padx=20, pady=20)

        # Calcula a altura máxima da folha na tela (~80% da altura do monitor)
        screen_height = self.winfo_screenheight()
        target_height = int(screen_height * 0.8)
        
        preview_ratio = target_height / self.a4_height
        preview_width = int(self.a4_width * preview_ratio)

        # Redimensiona a imagem montada apenas para a visualização na tela
        img_resized = a4_final_image.copy()
        img_resized.thumbnail((preview_width, target_height), Image.Resampling.LANCZOS)
        
        tk_image = ctk.CTkImage(light_image=img_resized, dark_image=img_resized, size=(img_resized.width, img_resized.height))

        # O CTkLabel com cor de fundo branca funciona visualmente como o papel físico A4 no centro
        lbl_paper = ctk.CTkLabel(preview_frame, image=tk_image, text="", fg_color="white")
        lbl_paper.pack(expand=True)

        # --- Painel Inferior de Botões (Voltar / Confirmar) ---
        actions_frame = ctk.CTkFrame(preview_win, fg_color="#1E293B", height=80, corner_radius=0)
        actions_frame.pack(side="bottom", fill="x")

        # Botão Voltar (Retorna intacto para a tela inicial)
        btn_voltar = ctk.CTkButton(actions_frame, text="Voltar", width=150, height=50, corner_radius=8,
                                   fg_color="transparent", border_width=2, border_color="#94A3B8", 
                                   text_color="#94A3B8", hover_color="#334155",
                                   font=ctk.CTkFont(size=16, weight="bold"),
                                   command=preview_win.destroy)
        btn_voltar.pack(side="left", padx=30, pady=15)

        # Botão Salvar PDF (Lado direito, abre diálogo do sistema)
        btn_save = ctk.CTkButton(actions_frame, text="Salvar PDF", width=180, height=50, corner_radius=8,
                                 fg_color="#06B6D4", hover_color="#0891B2", text_color="black",
                                 font=ctk.CTkFont(size=16, weight="bold"), 
                                 command=lambda: self.save_pdf_dialog(a4_final_image, preview_win))
        btn_save.pack(side="right", padx=(10, 30), pady=15)

        # Botão Gerar PDF (Antigo Confirmar e Imprimir - Gera temp e abre)
        btn_generate = ctk.CTkButton(actions_frame, text="Gerar PDF", width=180, height=50, corner_radius=8,
                                     fg_color="#06B6D4", hover_color="#0891B2", text_color="black",
                                     font=ctk.CTkFont(size=16, weight="bold"), 
                                     command=lambda: self.print_image(a4_final_image, preview_win))
        btn_generate.pack(side="right", padx=(30, 10), pady=15)

    def save_pdf_dialog(self, final_image, window_to_close):
        try:
            output_path = filedialog.asksaveasfilename(
                defaultextension=".pdf",
                initialfile="impressao_canecas.pdf",
                title="Salvar PDF como",
                filetypes=[("Arquivos PDF", "*.pdf"), ("Todos os arquivos", "*.*")]
            )
            if output_path:
                final_image.save(output_path, "PDF", resolution=300.0, save_all=True)
                window_to_close.destroy()
                messagebox.showinfo("Sucesso", f"PDF salvo com sucesso em:\n{output_path}")
        except Exception as e:
            messagebox.showerror("Erro ao Salvar", f"Ocorreu um erro ao salvar o PDF:\n{str(e)}")

    def print_image(self, final_image, window_to_close):
        try:
            output_path = os.path.join(self.temp_dir, "impressao_canecas.pdf")
            
            # Salva o arquivo final em formato PDF com a resolução correta para escala física
            final_image.save(output_path, "PDF", resolution=300.0, save_all=True)

            window_to_close.destroy()

            # Mostra as instruções essenciais para o usuário
            messagebox.showinfo(
                "Instruções de Impressão",
                "O arquivo PDF foi gerado e será aberto agora! Pressione Ctrl+P no seu leitor de PDF para imprimir. IMPORTANTE: Clique em 'Propriedades da Impressora' ou 'Imprimir usando a caixa de diálogo do sistema' e lembre-se de configurar: Papel Apresentação Premium Fosco, Sem Ajuste de Cor e Espelhar Imagem."
            )

            # Abre o PDF com o leitor padrão do sistema do usuário
            if os.name == 'nt':
                os.startfile(os.path.abspath(output_path))
            else:
                import subprocess
                if sys.platform == "darwin":
                    subprocess.call(["open", output_path])
                else:
                    subprocess.call(["xdg-open", output_path])
            
        except Exception as e:
            messagebox.showerror("Erro ao Gerar PDF", f"Ocorreu um erro ao gerar/abrir o PDF:\n{str(e)}")

if __name__ == "__main__":
    app = App()
    app.mainloop()
