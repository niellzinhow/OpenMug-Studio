import os
import sys
import customtkinter as ctk
from tkinter import filedialog, messagebox
from PIL import Image

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

class PreviewWindow(ctk.CTkToplevel):
    def __init__(self, master, a4_final_image, temp_dir, a4_width, a4_height):
        super().__init__(master)
        
        self.title("Layout de Impressão (Prévia)")
        self.a4_final_image = a4_final_image
        self.temp_dir = temp_dir
        self.a4_width = a4_width
        self.a4_height = a4_height

        try:
            self.iconbitmap(resource_path("OpenMug Studio.ico"))
        except:
            pass
        
        # Maximizando a Janela e forçando ancoragem em 0,0 para evitar bugs do Windows
        if os.name == 'nt':
            self.geometry(f"{self.winfo_screenwidth()}x{self.winfo_screenheight()}+0+0")
            self.after(200, lambda: self.state('zoomed'))
        else:
            self.geometry(f"{self.winfo_screenwidth()}x{self.winfo_screenheight()}+0+0")
            
        self.grab_set() 

        # Define Fundo da janela (CMYK Midnight)
        self.configure(fg_color="#0F172A")

        self._build_ui()

    def _build_ui(self):
        # Container para centralizar a "Folha de Papel"
        preview_frame = ctk.CTkFrame(self, fg_color="transparent")
        preview_frame.pack(expand=True, fill="both", padx=20, pady=20)

        # Calcula a altura máxima da folha na tela (~80% da altura do monitor)
        screen_height = self.winfo_screenheight()
        target_height = int(screen_height * 0.8)
        
        preview_ratio = target_height / self.a4_height
        preview_width = int(self.a4_width * preview_ratio)

        # Redimensiona a imagem montada apenas para a visualização na tela
        img_resized = self.a4_final_image.copy()
        img_resized.thumbnail((preview_width, target_height), Image.Resampling.LANCZOS)
        
        tk_image = ctk.CTkImage(light_image=img_resized, dark_image=img_resized, size=(img_resized.width, img_resized.height))

        # O CTkLabel com cor de fundo branca funciona visualmente como o papel físico A4 no centro
        lbl_paper = ctk.CTkLabel(preview_frame, image=tk_image, text="", fg_color="white")
        lbl_paper.pack(expand=True)

        # --- Painel Inferior de Botões (Voltar / Confirmar) ---
        actions_frame = ctk.CTkFrame(self, fg_color="#1E293B", height=80, corner_radius=0)
        actions_frame.pack(side="bottom", fill="x")

        # Botão Voltar (Retorna intacto para a tela inicial)
        btn_voltar = ctk.CTkButton(actions_frame, text="Voltar", width=150, height=50, corner_radius=8,
                                   fg_color="transparent", border_width=2, border_color="#94A3B8", 
                                   text_color="#94A3B8", hover_color="#334155",
                                   font=ctk.CTkFont(size=16, weight="bold"),
                                   command=self.destroy)
        btn_voltar.pack(side="left", padx=30, pady=15)

        # Botão Salvar PDF (Lado direito, abre diálogo do sistema)
        btn_save = ctk.CTkButton(actions_frame, text="Salvar PDF", width=180, height=50, corner_radius=8,
                                 fg_color="#06B6D4", hover_color="#0891B2", text_color="black",
                                 font=ctk.CTkFont(size=16, weight="bold"), 
                                 command=self.save_pdf_dialog)
        btn_save.pack(side="right", padx=(10, 30), pady=15)

        # Botão Gerar PDF (Antigo Confirmar e Imprimir - Gera temp e abre)
        btn_generate = ctk.CTkButton(actions_frame, text="Gerar PDF", width=180, height=50, corner_radius=8,
                                     fg_color="#06B6D4", hover_color="#0891B2", text_color="black",
                                     font=ctk.CTkFont(size=16, weight="bold"), 
                                     command=self.print_image)
        btn_generate.pack(side="right", padx=(30, 10), pady=15)

    def save_pdf_dialog(self):
        try:
            output_path = filedialog.asksaveasfilename(
                defaultextension=".pdf",
                initialfile="impressao_canecas.pdf",
                title="Salvar PDF como",
                filetypes=[("Arquivos PDF", "*.pdf"), ("Todos os arquivos", "*.*")]
            )
            if output_path:
                try:
                    self.a4_final_image.save(output_path, "PDF", resolution=300.0, save_all=True)
                    self.destroy()
                    messagebox.showinfo("Sucesso", f"PDF salvo com sucesso em:\n{output_path}")
                except PermissionError:
                    messagebox.showerror("Arquivo em Uso", "Não foi possível salvar! O arquivo PDF já está aberto em outro programa. Por favor, feche-o e tente novamente.")
        except Exception as e:
            messagebox.showerror("Erro ao Salvar", f"Ocorreu um erro ao salvar o PDF:\n{str(e)}")

    def print_image(self):
        try:
            output_path = os.path.join(self.temp_dir, "impressao_canecas.pdf")
            
            try:
                # Salva o arquivo final em formato PDF com a resolução correta para escala física
                self.a4_final_image.save(output_path, "PDF", resolution=300.0, save_all=True)
            except PermissionError:
                messagebox.showerror("Aviso: PDF em Uso", "O PDF anterior ainda está aberto no seu leitor (Acrobat, Edge, etc).\n\nPor favor, feche a aba do PDF antigo e clique em 'Gerar PDF' novamente.")
                return

            self.destroy()

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
