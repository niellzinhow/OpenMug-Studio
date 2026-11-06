import os
import sys
import threading
import webbrowser
import tkinter
import customtkinter as ctk
from tkinter import filedialog, messagebox
from PIL import Image

from core.config_manager import ConfigManager
from core import updater
from core.version import VERSION, GITHUB_REPO
from core.image_processor import ImageProcessor
from gui.preview_window import PreviewWindow
from gui import theme as T
from gui.background import Wallpaper

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
        self.configure(fg_color=T.BG_MAIN)

        self.config_manager = ConfigManager()
        self.image_processor = ImageProcessor()
        
        # Armazena os dados das 3 imagens
        self.images_data = [
            {"path": "", "mode": "Centralizar", "label_ref": None, "thumb_ref": None, "actions_frame_ref": None, "combo_mode_ref": None},
            {"path": "", "mode": "Centralizar", "label_ref": None, "thumb_ref": None, "actions_frame_ref": None, "combo_mode_ref": None},
            {"path": "", "mode": "Centralizar", "label_ref": None, "thumb_ref": None, "actions_frame_ref": None, "combo_mode_ref": None}
        ]

        # Papel de parede dinâmico (camada de fundo; deve existir antes dos demais widgets)
        self.wallpaper = Wallpaper(self)

        self._build_ui()
        
        # Iniciar maximizado no Windows
        if os.name == 'nt':
            self.after(0, lambda: self.state('zoomed'))

        # Verificação silenciosa de atualização ao abrir
        self.after(1500, lambda: self.check_updates(silent=True))

    def _build_ui(self):
        """Constrói a interface gráfica do aplicativo (dark glassmorphism minimalista)."""
        
        # Todos os blocos são CTkFrame SÓLIDOS empilhados diretamente na janela, sobre o papel de parede.
        # (Contêineres "transparentes" do CTk pintariam a cor da janela por cima da imagem.)

        # --- TÍTULO E CONTROLES DE TOPO (fora de qualquer card, direto sobre o papel de parede) ---
        icon_pil = None
        try:
            icon_pil = Image.open(resource_path("OpenMug Studio.ico"))
        except Exception:
            pass

        # Botões pílula posicionados direto na janela (sem frame intermediário, ajustando cantos ao fundo)
        try:
            scale = ctk.ScalingTracker.get_window_scaling(self) or 1.0
        except Exception:
            scale = 1.0

        notes_icon = T.make_notes_icon()
        self.btn_notes = T.CircleIconButton(self, text="", image=notes_icon, width=28, height=28,
                                            corner_radius=14, fg_color=T.PILL_UTILITY, hover_color=T.PILL_UTILITY_HOVER,
                                            command=self.show_release_notes)
        self.btn_notes.place(relx=1.0, x=round(-28 * scale), y=round(18 * scale), anchor="ne")
        self.wallpaper.register(self.btn_notes)

        self.btn_update = ctk.CTkButton(self, text="Buscar atualizações", width=140, height=28,
                                        corner_radius=14, font=T.font(11),
                                        fg_color=T.PILL_UTILITY, hover_color=T.PILL_UTILITY_HOVER,
                                        text_color=T.TEXT_MUTED,
                                        command=lambda: self.check_updates(silent=False))
        # Posicionado à esquerda de btn_notes com 8px de folga (28 margem + 28 botão + 8 espaço = 64)
        self.btn_update.place(relx=1.0, x=round(-64 * scale), y=round(18 * scale), anchor="ne")
        self.wallpaper.register(self.btn_update)

        # Desenha ícone RGBA + "OpenMug Studio" + "Versão X" diretamente nos pixels do papel de parede
        # (transparência real por pixel, sem nenhuma caixa retangular de widget)
        self.wallpaper.add_header_overlay(
            title_text="OpenMug Studio",
            icon_img=icon_pil,
            version_text=f"Versão {VERSION}",
            anchor_btn=self.btn_update,
        )

        # --- CARD DO PERFIL ICC ---
        self.icc_card = ctk.CTkFrame(self, fg_color=T.CARD_BG, corner_radius=T.RADIUS_CARD,
                                     border_width=1, border_color=T.CARD_BORDER)
        self.icc_card.pack(fill="x", padx=28, pady=(64, 8))
        self.wallpaper.register(self.icc_card, glass=(T.CARD_BG, T.GLASS_ALPHA))

        self.btn_icc = ctk.CTkButton(self.icc_card, text="🔍  Procurar Perfil ICC", command=self.select_icc,
                                     height=32, corner_radius=T.RADIUS_PILL,
                                     fg_color=T.PILL_UTILITY, hover_color=T.PILL_UTILITY_HOVER,
                                     text_color=T.TEXT_ON_SECONDARY, font=T.font(12, "bold"))
        self.btn_icc.pack(side="left", padx=(16, 12), pady=12)

        icc_display = self.config_manager.icc_profile_path if self.config_manager.icc_profile_path else "Nenhum perfil selecionado"
        self.lbl_icc = ctk.CTkLabel(self.icc_card, text=icc_display, text_color=T.TEXT_MUTED,
                                    font=T.font(12), wraplength=500)
        self.lbl_icc.pack(side="left", pady=12)

        self.btn_clear_icc = T.CircleIconButton(self.icc_card, text="✕", width=28, height=28, corner_radius=14,
                                                fg_color="transparent", hover_color=T.DANGER_HOVER,
                                                text_color=T.TEXT_MUTED, font=T.font(12, "bold"),
                                                command=self.clear_icc)
        if self.config_manager.icc_profile_path:
            self.btn_clear_icc.pack(side="right", padx=(0, 16), pady=12)

        # --- BARRA INFERIOR (cápsula): empacotada antes dos cards para sempre reservar espaço ---
        self.bottom_frame = ctk.CTkFrame(self, fg_color=T.CAPSULE_BG, corner_radius=T.RADIUS_PILL_LG,
                                         border_width=1, border_color=T.CAPSULE_BORDER)
        self.bottom_frame.pack(side="bottom", pady=(8, 24))
        self.wallpaper.register(self.bottom_frame, glass=(T.CAPSULE_BG, T.GLASS_ALPHA))

        self.btn_preview = ctk.CTkButton(self.bottom_frame, text="Gerar Prévia",
                                         command=self.generate_preview, height=44, width=220,
                                         corner_radius=T.RADIUS_PILL_LG,
                                         fg_color=T.ACCENT, hover_color=T.ACCENT_HOVER, text_color="#FFFFFF",
                                         font=T.font(15, "bold"))
        self.btn_preview.pack(side="left", padx=(12, 6), pady=12)

        self.btn_clear_all = ctk.CTkButton(self.bottom_frame, text="🗑  Limpar Tudo",
                                           command=self.clear_all_images, height=44, width=150,
                                           corner_radius=T.RADIUS_PILL_LG,
                                           fg_color=T.CLEAR_ALL, hover_color=T.CLEAR_ALL_HOVER,
                                           state="disabled", text_color=T.TEXT_BODY,
                                           text_color_disabled=T.TEXT_DISABLED,
                                           font=T.font(13, "bold"))
        self.btn_clear_all.pack(side="left", padx=(6, 12), pady=12)

        # --- CARDS DAS ARTES (Meio) ---
        for i in range(3):
            card_frame = ctk.CTkFrame(self, fg_color=T.CARD_BG, corner_radius=T.RADIUS_CARD,
                                      border_width=1, border_color=T.CARD_BORDER)
            card_frame.pack(pady=8, padx=28, fill="x")
            self.wallpaper.register(card_frame, glass=(T.CARD_BG, T.GLASS_ALPHA))
            self._bind_card_hover(card_frame)

            # 1. Miniatura (Extrema Esquerda, proporção 16:9)
            lbl_thumb = ctk.CTkLabel(card_frame, text="🖼", font=T.font(30), width=T.THUMB_SIZE[0], height=T.THUMB_SIZE[1],
                                     fg_color=T.THUMB_BG, text_color=T.TEXT_DISABLED, corner_radius=T.RADIUS_THUMB)
            lbl_thumb.pack(side="left", padx=18, pady=16)

            # 2. Controles Principais (Centro - Expandido)
            middle_frame = ctk.CTkFrame(card_frame, fg_color="transparent")
            middle_frame.pack(side="left", fill="x", expand=True, padx=10, pady=12)

            lbl_title = ctk.CTkLabel(middle_frame, text=f"Arte {i+1}", font=T.font(15, "bold"), text_color=T.TEXT_TITLE)
            lbl_title.pack(anchor="w", pady=(0, 6))

            btn_img = ctk.CTkButton(middle_frame, text="Escolher Imagem", command=lambda idx=i: self.select_image(idx),
                                    height=32, corner_radius=T.RADIUS_PILL, font=T.font(12, "bold"),
                                    fg_color=T.PILL_BUTTON, hover_color=T.PILL_BUTTON_HOVER, text_color="#FFFFFF")
            btn_img.pack(anchor="w", pady=4)

            lbl_path = ctk.CTkLabel(middle_frame, text="Nenhuma imagem selecionada", text_color=T.TEXT_MUTED,
                                    font=T.font(12), anchor="w")
            lbl_path.pack(anchor="w", pady=(6, 0))

            # 3. Configurações da Arte (Extrema Direita)
            right_frame = ctk.CTkFrame(card_frame, fg_color="transparent")
            right_frame.pack(side="right", padx=22, pady=12)

            lbl_mode = ctk.CTkLabel(right_frame, text="Modo de Encaixe:", text_color=T.TEXT_MUTED, font=T.font(11))
            lbl_mode.pack(anchor="e", pady=(0, 4))

            combo_mode = T.PillOptionMenu(
                right_frame,
                values=["Centralizar", "Cortar", "Redimensionar"],
                command=lambda val, idx=i: self.set_image_mode(val, idx),
                width=142,
                height=33,
                corner_radius=16,
                dynamic_resizing=False,
                fg_color=T.MENU_BG,
                button_color=T.MENU_BG,
                button_hover_color=T.MENU_HOVER,
                hover_color=T.MENU_HOVER,
                text_color=T.MENU_TEXT,
                arrow_color=T.MENU_ARROW,
                dropdown_fg_color=T.DROPDOWN_BG,
                dropdown_hover_color=T.DROPDOWN_HOVER,
                dropdown_text_color=T.DROPDOWN_TEXT,
                dropdown_border_color=T.DROPDOWN_BORDER,
                font_obj=T.font(12),
                dropdown_font_obj=T.font(12),
            )
            combo_mode.set(self.images_data[i]["mode"])
            combo_mode.pack(anchor="e", pady=(0, 10))

            actions_frame = ctk.CTkFrame(right_frame, fg_color="transparent")
            
            btn_duplicate = ctk.CTkButton(actions_frame, text="⧉ Duplicar", width=80, height=28,
                                          corner_radius=T.RADIUS_PILL, font=T.font(11, "bold"),
                                          fg_color=T.SECONDARY, hover_color=T.SECONDARY_HOVER,
                                          text_color=T.TEXT_ON_SECONDARY,
                                          command=lambda idx=i: self.duplicate_image(idx))
            btn_duplicate.pack(side="left", padx=(0, 6))

            btn_clear = ctk.CTkButton(actions_frame, text="✕ Limpar", width=80, height=28,
                                      corner_radius=T.RADIUS_PILL, font=T.font(11, "bold"),
                                      fg_color=T.DANGER_BG, hover_color=T.DANGER_HOVER,
                                      text_color=T.DANGER_TEXT,
                                      command=lambda idx=i: self.remove_image(idx))
            btn_clear.pack(side="left")

            self.images_data[i]["label_ref"] = lbl_path
            self.images_data[i]["thumb_ref"] = lbl_thumb
            self.images_data[i]["actions_frame_ref"] = actions_frame
            self.images_data[i]["combo_mode_ref"] = combo_mode

    def _bind_card_hover(self, card):
        """Realce sutil do card ao passar o mouse (mantém o realce enquanto o cursor estiver sobre os filhos)."""
        def inside():
            x, y = card.winfo_pointerxy()
            return (card.winfo_rootx() <= x < card.winfo_rootx() + card.winfo_width()
                    and card.winfo_rooty() <= y < card.winfo_rooty() + card.winfo_height())

        def tone(base):
            return self.wallpaper.glass(card, base, T.GLASS_ALPHA)

        card.bind("<Enter>", lambda e: card.configure(fg_color=tone(T.CARD_BG_HOVER)), add="+")
        card.bind("<Leave>", lambda e: None if inside() else card.configure(fg_color=tone(T.CARD_BG)), add="+")

    # --- NOTAS DA VERSÃO ---
    def show_release_notes(self):
        """Abre instantaneamente as notas da versão atual e sincroniza com o GitHub em segundo plano."""
        # Evita instâncias duplicadas: se já estiver aberta, apenas traz para a frente
        existing = getattr(self, "_notes_holder", None)
        if existing and existing["win"].winfo_exists():
            w = existing["win"]
            w.deiconify()
            w.attributes("-topmost", True)
            w.lift()
            w.focus_force()
            return

        embedded = updater.get_embedded_notes(VERSION)
        if embedded:
            # Abre na hora (0ms de espera!) com as notas embutidas e atualiza se o GitHub tiver texto diferente
            holder = self._open_notes_window(embedded, None)
            self._notes_holder = holder

            def sync_worker():
                try:
                    remote = updater.fetch_release_notes(VERSION)
                    if remote and remote.strip() != embedded.strip():
                        self.after(0, lambda: holder["render"](remote))
                except updater.UpdateError:
                    pass

            threading.Thread(target=sync_worker, daemon=True).start()
            return

        self.btn_notes.configure(state="disabled")

        def worker():
            try:
                text, error = updater.fetch_release_notes(VERSION), None
            except updater.UpdateError as e:
                text, error = None, str(e)
            self.after(0, lambda: self._open_notes_window(text, error))

        threading.Thread(target=worker, daemon=True).start()

    def _open_notes_window(self, text, error):
        self.btn_notes.configure(state="normal")
        if error:
            body = error
        elif text:
            body = text
        else:
            body = "Não há notas publicadas para esta versão."

        width, height = 560, 500
        try:
            scale = ctk.ScalingTracker.get_window_scaling(self) or 1.0
        except Exception:
            scale = 1.0

        win = ctk.CTkToplevel(self)
        win.withdraw()
        win.overrideredirect(True)  # sem moldura nativa: o contorno é desenhado pelo próprio modal
        win.attributes("-topmost", True)  # garante que nunca abra atrás da janela principal
        win.configure(fg_color=T.BG_MODAL_KEY)
        try:
            win.attributes("-transparentcolor", T.BG_MODAL_KEY)  # cantos arredondados reais (Windows)
        except tkinter.TclError:
            pass
        px_w, px_h = round(width * scale), round(height * scale)
        x = self.winfo_rootx() + max(0, (self.winfo_width() - px_w) // 2)
        y = self.winfo_rooty() + max(0, (self.winfo_height() - px_h) // 3)
        win.geometry(f"{width}x{height}+{x}+{y}")

        shell = ctk.CTkFrame(win, fg_color=T.MODAL_BG, corner_radius=T.RADIUS_MODAL,
                             border_width=1, border_color=T.MODAL_BORDER, bg_color=T.BG_MODAL_KEY)
        shell.pack(fill="both", expand=True)

        # Cabeçalho (também serve para arrastar a janela)
        header = ctk.CTkFrame(shell, fg_color="transparent")
        header.pack(fill="x", padx=22, pady=(16, 6))
        lbl_header = ctk.CTkLabel(header, text=f"Notas da versão {VERSION}", font=T.font(14, "bold"),
                                  text_color=T.TEXT_TITLE)
        lbl_header.pack(side="left")
        btn_close = T.CircleIconButton(header, text="✕", width=28, height=28, corner_radius=14, font=T.font(12, "bold"),
                                       fg_color=T.PILL_UTILITY, hover_color=T.PILL_UTILITY_HOVER,
                                       text_color=T.TEXT_MUTED, command=win.destroy)
        btn_close.pack(side="right")

        drag = {}
        def start_drag(e):
            drag["dx"], drag["dy"] = e.x_root - win.winfo_x(), e.y_root - win.winfo_y()
        def do_drag(e):
            win.geometry(f"+{e.x_root - drag['dx']}+{e.y_root - drag['dy']}")
        for w in (header, lbl_header):
            w.bind("<ButtonPress-1>", start_drag)
            w.bind("<B1-Motion>", do_drag)

        # Card de conteúdo
        card = ctk.CTkScrollableFrame(shell, fg_color=T.MODAL_CARD_BG, corner_radius=14,
                                      border_width=1, border_color=T.MODAL_CARD_BORDER,
                                      scrollbar_button_color=T.SECONDARY,
                                      scrollbar_button_hover_color=T.SECONDARY_HOVER)
        card.pack(fill="both", expand=True, padx=22, pady=6)

        def render_body(content):
            if not win.winfo_exists() or not card.winfo_exists():
                return
            for child in card.winfo_children():
                child.destroy()
            ctk.CTkLabel(card, text=f"OpenMug Studio {VERSION}", font=T.font(16, "bold"),
                         text_color=T.TEXT_TITLE, anchor="w").pack(fill="x", padx=12, pady=(10, 4))

            for line in content.split("\n"):
                stripped = line.strip()
                if not stripped:
                    ctk.CTkFrame(card, fg_color="transparent", height=4).pack()
                elif stripped.startswith("•"):
                    ctk.CTkLabel(card, text=stripped, font=T.font(13), text_color=T.TEXT_ON_SECONDARY,
                                 anchor="w", justify="left", wraplength=440).pack(fill="x", padx=(18, 12), pady=2)
                elif stripped == stripped.upper() and any(c.isalpha() for c in stripped) and len(stripped) < 60:
                    ctk.CTkLabel(card, text=stripped, font=T.font(11, "bold"), text_color=T.MODAL_SECTION,
                                 anchor="w").pack(fill="x", padx=12, pady=(12, 2))
                else:
                    ctk.CTkLabel(card, text=stripped, font=T.font(13), text_color=T.TEXT_ON_SECONDARY,
                                 anchor="w", justify="left", wraplength=450).pack(fill="x", padx=12, pady=2)

        render_body(body)

        # Rodapé: link do repositório
        link = ctk.CTkLabel(shell, text=f"github.com/{GITHUB_REPO}", text_color=T.ACCENT, cursor="hand2",
                            font=T.font(12))
        link.pack(pady=(8, 16))
        link.bind("<Button-1>", lambda e: webbrowser.open(f"https://github.com/{GITHUB_REPO}"))
        link.bind("<Enter>", lambda e: link.configure(font=T.font(12, underline=True), text_color=T.ACCENT_HOVER))
        link.bind("<Leave>", lambda e: link.configure(font=T.font(12), text_color=T.ACCENT))

        # Suporte completo a MouseWheel E Precision Touchpad (<TouchpadScroll> introduzido no Tk 9 / Python 3.14,
        # que o CustomTkinter não trata nativamente e onde dy vem empacotado em int16 nos 16 bits inferiores).
        scroll_acc = [0.0]

        active = [True]

        def _scroll_pixels(dy_delta):
            if not active[0] or not win.winfo_exists() or not card.winfo_exists():
                return
            if card._parent_canvas.yview() == (0.0, 1.0):
                return
            scroll_acc[0] += -dy_delta * 1.5
            steps = int(scroll_acc[0])
            if steps != 0:
                scroll_acc[0] -= steps
                card._parent_canvas.yview("scroll", steps, "units")

        def _on_notes_wheel(event):
            if not active[0] or not win.winfo_exists() or not card.winfo_exists():
                return
            # Modal tem apenas este container rolável; se o próprio CTkScrollableFrame ainda não rolou, rola aqui
            if not card._check_if_valid_scroll(event.widget):
                if card._parent_canvas.yview() != (0.0, 1.0):
                    card._parent_canvas.yview("scroll", -int(event.delta / 6), "units")

        def _on_notes_touchpad(event):
            if not active[0]:
                return
            raw_dy = event.delta & 0xFFFF
            if raw_dy >= 0x8000:
                raw_dy -= 0x10000
            if raw_dy != 0:
                _scroll_pixels(raw_dy)

        win.bind_all("<MouseWheel>", _on_notes_wheel, add="+")
        try:
            win.bind_all("<TouchpadScroll>", _on_notes_touchpad, add="+")
        except tkinter.TclError:
            pass
        esc_id = self.bind("<Escape>", lambda e: _close_notes(), add="+")

        def _close_notes():
            active[0] = False
            self._notes_holder = None
            for w, seq, fid in ((self, "<FocusIn>", focus_in_id),
                                (self, "<FocusOut>", focus_out_id),
                                (self, "<Unmap>", unmap_id),
                                (self, "<Escape>", esc_id)):
                try:
                    if fid and w.winfo_exists():
                        w.unbind(seq, fid)
                except Exception:
                    pass
            if win.winfo_exists():
                win.destroy()

        def _on_app_focus_out(e):
            if not win.winfo_exists():
                return
            self.after(60, lambda: win.winfo_exists() and self.focus_displayof() is None and win.attributes("-topmost", False))

        def _on_app_focus_in(e):
            if win.winfo_exists():
                win.deiconify()
                win.attributes("-topmost", True)
                win.lift()

        focus_in_id = self.bind("<FocusIn>", _on_app_focus_in, add="+")
        focus_out_id = self.bind("<FocusOut>", _on_app_focus_out, add="+")
        unmap_id = self.bind("<Unmap>", lambda e: e.widget is self and win.winfo_exists() and win.withdraw(), add="+")

        btn_close.configure(command=_close_notes)
        win.bind("<Escape>", lambda e: _close_notes())
        win.protocol("WM_DELETE_WINDOW", _close_notes)

        def _bring_to_front():
            if not win.winfo_exists():
                return
            win.deiconify()
            win.attributes("-topmost", True)
            win.lift()
            win.focus_force()

        win.update_idletasks()
        _bring_to_front()
        # Reforça o z-order após o ciclo interno de inicialização de 200ms do CTkToplevel
        win.after(60, _bring_to_front)
        win.after(220, lambda: (_bring_to_front(), win.winfo_exists() and win.grab_set()))
        return {"win": win, "render": render_body}

    # --- ATUALIZAÇÃO (GitHub Releases) ---
    def check_updates(self, silent=True):
        """Consulta a última release em segundo plano. Se silent=True, só avisa quando houver versão nova."""
        self.btn_update.configure(state="disabled", text="Verificando...")

        def worker():
            try:
                info, error = updater.check_for_update(), None
            except updater.UpdateError as e:
                info, error = None, str(e)
            self.after(0, lambda: self._on_update_checked(info, error, silent))

        threading.Thread(target=worker, daemon=True).start()

    def _on_update_checked(self, info, error, silent):
        self.btn_update.configure(state="normal", text="Buscar atualizações")
        if error:
            if not silent:
                messagebox.showerror("Atualização", error)
            return
        if not info:
            if not silent:
                messagebox.showinfo("Atualização", f"Você já está na versão mais recente ({VERSION}).")
            return

        self._open_update_prompt(info)

    def _open_update_prompt(self, info):
        """Modal estilizado com texto completo rolável das notas da nova versão."""
        existing = getattr(self, "_update_prompt_win", None)
        if existing and existing.winfo_exists():
            existing.deiconify()
            existing.attributes("-topmost", True)
            existing.lift()
            existing.focus_force()
            return

        can_auto_install = updater.is_frozen() and bool(info.get("url"))
        notes = (info.get("notes") or "").strip() or "Sem notas detalhadas para esta versão."

        width, height = 580, 520
        try:
            scale = ctk.ScalingTracker.get_window_scaling(self) or 1.0
        except Exception:
            scale = 1.0

        win = ctk.CTkToplevel(self)
        self._update_prompt_win = win
        win.withdraw()
        win.overrideredirect(True)
        win.attributes("-topmost", True)
        win.configure(fg_color=T.BG_MODAL_KEY)
        try:
            win.attributes("-transparentcolor", T.BG_MODAL_KEY)
        except tkinter.TclError:
            pass

        px_w, px_h = round(width * scale), round(height * scale)
        x = self.winfo_rootx() + max(0, (self.winfo_width() - px_w) // 2)
        y = self.winfo_rooty() + max(0, (self.winfo_height() - px_h) // 3)
        win.geometry(f"{width}x{height}+{x}+{y}")

        shell = ctk.CTkFrame(win, fg_color=T.MODAL_BG, corner_radius=T.RADIUS_MODAL,
                             border_width=1, border_color=T.MODAL_BORDER, bg_color=T.BG_MODAL_KEY)
        shell.pack(fill="both", expand=True)

        # Cabeçalho
        header = ctk.CTkFrame(shell, fg_color="transparent")
        header.pack(fill="x", padx=22, pady=(16, 4))
        lbl_header = ctk.CTkLabel(header, text="Atualização disponível", font=T.font(14, "bold"),
                                  text_color=T.TEXT_TITLE)
        lbl_header.pack(side="left")
        btn_close = T.CircleIconButton(header, text="✕", width=28, height=28, corner_radius=14, font=T.font(12, "bold"),
                                       fg_color=T.PILL_UTILITY, hover_color=T.PILL_UTILITY_HOVER,
                                       text_color=T.TEXT_MUTED)
        btn_close.pack(side="right")

        sub = ctk.CTkLabel(
            shell,
            text=f"Nova versão {info['version']} disponível  •  versão instalada: {VERSION}",
            font=T.font(12),
            text_color=T.TEXT_MUTED,
            anchor="w",
        )
        sub.pack(fill="x", padx=22, pady=(0, 6))

        drag = {}
        def start_drag(e):
            drag["dx"], drag["dy"] = e.x_root - win.winfo_x(), e.y_root - win.winfo_y()
        def do_drag(e):
            win.geometry(f"+{e.x_root - drag['dx']}+{e.y_root - drag['dy']}")
        for w in (header, lbl_header, sub):
            w.bind("<ButtonPress-1>", start_drag)
            w.bind("<B1-Motion>", do_drag)

        # Rodapé de botões (empacotado antes do card para reservar altura)
        footer = ctk.CTkFrame(shell, fg_color="transparent")
        footer.pack(side="bottom", fill="x", padx=22, pady=(8, 18))

        # Card rolável com TODAS as notas (sem corte de caracteres)
        card = ctk.CTkScrollableFrame(shell, fg_color=T.MODAL_CARD_BG, corner_radius=14,
                                      border_width=1, border_color=T.MODAL_CARD_BORDER,
                                      scrollbar_button_color=T.SECONDARY,
                                      scrollbar_button_hover_color=T.SECONDARY_HOVER)
        card.pack(fill="both", expand=True, padx=22, pady=6)

        ctk.CTkLabel(card, text=f"O que há de novo na v{info['version']}", font=T.font(15, "bold"),
                     text_color=T.TEXT_TITLE, anchor="w").pack(fill="x", padx=12, pady=(10, 4))

        for line in notes.split("\n"):
            stripped = line.strip()
            if not stripped:
                ctk.CTkFrame(card, fg_color="transparent", height=4).pack()
            elif stripped.startswith("•"):
                ctk.CTkLabel(card, text=stripped, font=T.font(13), text_color=T.TEXT_ON_SECONDARY,
                             anchor="w", justify="left", wraplength=460).pack(fill="x", padx=(18, 12), pady=2)
            elif stripped == stripped.upper() and any(c.isalpha() for c in stripped) and len(stripped) < 60:
                ctk.CTkLabel(card, text=stripped, font=T.font(11, "bold"), text_color=T.MODAL_SECTION,
                             anchor="w").pack(fill="x", padx=12, pady=(12, 2))
            else:
                ctk.CTkLabel(card, text=stripped, font=T.font(13), text_color=T.TEXT_ON_SECONDARY,
                             anchor="w", justify="left", wraplength=470).pack(fill="x", padx=12, pady=2)

        # Suporte a roda do mouse e Precision Touchpad
        scroll_acc = [0.0]
        active = [True]

        def _scroll_pixels(dy_delta):
            if not active[0] or not win.winfo_exists() or not card.winfo_exists():
                return
            if card._parent_canvas.yview() == (0.0, 1.0):
                return
            scroll_acc[0] += -dy_delta * 1.5
            steps = int(scroll_acc[0])
            if steps != 0:
                scroll_acc[0] -= steps
                card._parent_canvas.yview("scroll", steps, "units")

        def _on_wheel(event):
            if not active[0] or not win.winfo_exists() or not card.winfo_exists():
                return
            if not card._check_if_valid_scroll(event.widget):
                if card._parent_canvas.yview() != (0.0, 1.0):
                    card._parent_canvas.yview("scroll", -int(event.delta / 6), "units")

        def _on_touchpad(event):
            if not active[0]:
                return
            raw_dy = event.delta & 0xFFFF
            if raw_dy >= 0x8000:
                raw_dy -= 0x10000
            if raw_dy != 0:
                _scroll_pixels(raw_dy)

        win.bind_all("<MouseWheel>", _on_wheel, add="+")
        try:
            win.bind_all("<TouchpadScroll>", _on_touchpad, add="+")
        except tkinter.TclError:
            pass

        def _on_app_focus_out(e):
            if win.winfo_exists():
                self.after(60, lambda: win.winfo_exists() and self.focus_displayof() is None and win.attributes("-topmost", False))

        def _on_app_focus_in(e):
            if win.winfo_exists():
                win.deiconify()
                win.attributes("-topmost", True)
                win.lift()

        focus_in_id = self.bind("<FocusIn>", _on_app_focus_in, add="+")
        focus_out_id = self.bind("<FocusOut>", _on_app_focus_out, add="+")
        unmap_id = self.bind("<Unmap>", lambda e: e.widget is self and win.winfo_exists() and win.withdraw(), add="+")
        esc_id = self.bind("<Escape>", lambda e: _close(), add="+")

        def _close():
            active[0] = False
            self._update_prompt_win = None
            for w, seq, fid in ((self, "<FocusIn>", focus_in_id),
                                (self, "<FocusOut>", focus_out_id),
                                (self, "<Unmap>", unmap_id),
                                (self, "<Escape>", esc_id)):
                try:
                    if fid and w.winfo_exists():
                        w.unbind(seq, fid)
                except Exception:
                    pass
            if win.winfo_exists():
                win.destroy()

        def _confirm():
            _close()
            if can_auto_install:
                self._start_download(info)
            else:
                webbrowser.open(updater.RELEASES_PAGE)

        btn_later = ctk.CTkButton(footer, text="Agora não", width=120, height=38, corner_radius=19,
                                  fg_color=T.SECONDARY, hover_color=T.SECONDARY_HOVER,
                                  text_color=T.TEXT_ON_SECONDARY, font=T.font(13, "bold"),
                                  command=_close)
        btn_later.pack(side="left")

        primary_label = "Baixar e instalar" if can_auto_install else "Abrir página de download"
        btn_install = ctk.CTkButton(footer, text=primary_label, width=190, height=38, corner_radius=19,
                                    fg_color=T.ACCENT, hover_color=T.ACCENT_HOVER,
                                    text_color="#FFFFFF", font=T.font(13, "bold"),
                                    command=_confirm)
        btn_install.pack(side="right")

        btn_close.configure(command=_close)
        win.bind("<Escape>", lambda e: _close())
        win.protocol("WM_DELETE_WINDOW", _close)

        def _bring_to_front():
            if not win.winfo_exists():
                return
            win.deiconify()
            win.attributes("-topmost", True)
            win.lift()
            win.focus_force()

        win.update_idletasks()
        _bring_to_front()
        win.after(60, _bring_to_front)
        win.after(220, lambda: (_bring_to_front(), win.winfo_exists() and win.grab_set()))

    def _start_download(self, info):
        win = ctk.CTkToplevel(self)
        win.title("Atualizando")
        win.geometry("360x110")
        win.resizable(False, False)
        win.configure(fg_color=T.BG_MAIN)
        win.transient(self)
        win.grab_set()
        win.protocol("WM_DELETE_WINDOW", lambda: None)
        ctk.CTkLabel(win, text=f"Baixando versão {info['version']}...", text_color=T.TEXT_TITLE,
                     font=T.font(13)).pack(pady=(20, 10))
        bar = ctk.CTkProgressBar(win, width=300, progress_color=T.ACCENT, fg_color=T.SECONDARY)
        bar.set(0)
        bar.pack()

        def worker():
            try:
                path = updater.download_update(info, lambda p: self.after(0, lambda: bar.set(p)))
                self.after(0, lambda: self._finish_update(win, path, None))
            except updater.UpdateError as e:
                self.after(0, lambda: self._finish_update(win, None, str(e)))

        threading.Thread(target=worker, daemon=True).start()

    def _finish_update(self, win, path, error):
        win.destroy()
        if error:
            messagebox.showerror("Atualização", error)
            return
        try:
            updater.apply_update(path)
        except Exception as e:
            messagebox.showerror("Atualização", f"Não foi possível aplicar a atualização:\n{e}")
            return
        self.destroy()
        sys.exit(0)

    def select_icc(self):
        filepath = filedialog.askopenfilename(
            title="Selecione o Perfil ICC",
            filetypes=[("Perfis ICC", "*.icc *.icm"), ("Todos os arquivos", "*.*")]
        )
        if filepath:
            self.config_manager.save_config(filepath)
            self.lbl_icc.configure(text=filepath)
            self.btn_clear_icc.pack(side="right", padx=(0, 16), pady=12)

    def clear_icc(self):
        self.config_manager.save_config("")
        self.lbl_icc.configure(text="Nenhum perfil selecionado")
        self.btn_clear_icc.pack_forget()

    def _set_thumbnail(self, index, filepath):
        """Gera a miniatura com cantos arredondados e a exibe no card."""
        with Image.open(filepath) as img:
            img_copy = img.copy()
            img_copy.thumbnail(T.THUMB_SIZE, Image.Resampling.LANCZOS)
            img_copy = T.rounded_image(img_copy)
            # CTkImage garante uma renderização bonita e fácil de atualizar
            thumb_tk = ctk.CTkImage(light_image=img_copy, dark_image=img_copy, size=(img_copy.width, img_copy.height))
            self.images_data[index]["thumb_ref"].configure(image=thumb_tk, text="")

    def select_image(self, index):
        filepath = filedialog.askopenfilename(
            title=f"Selecione a Arte {index+1}",
            filetypes=[("Imagens", "*.png *.jpg *.jpeg *.tif *.tiff *.bmp"), ("Todos os arquivos", "*.*")]
        )
        if filepath:
            self.images_data[index]["path"] = filepath
            filename = os.path.basename(filepath)
            self.images_data[index]["label_ref"].configure(text=filename)
            
            # Força o reset para "Centralizar" ao escolher/substituir a imagem
            self.images_data[index]["mode"] = "Centralizar"
            if self.images_data[index]["combo_mode_ref"]:
                self.images_data[index]["combo_mode_ref"].set("Centralizar")

            # Gera a miniatura (Thumbnail)
            try:
                self._set_thumbnail(index, filepath)
                
                # Exibe os botões de ação da imagem (Limpar e Duplicar)
                self.images_data[index]["actions_frame_ref"].pack(anchor="e")
                
                self.update_clear_all_state()
            except Exception as e:
                print(f"Erro ao carregar miniatura: {e}")

    def remove_image(self, index):
        """Remove a imagem do bloco selecionado e esconde os botões de ação."""
        self.images_data[index]["path"] = ""
        self.images_data[index]["label_ref"].configure(text="Nenhuma imagem selecionada")
        self.images_data[index]["thumb_ref"].configure(image="", text="🖼")
        self.images_data[index]["actions_frame_ref"].pack_forget()
        
        # Reseta o modo para "Centralizar" ao limpar
        self.images_data[index]["mode"] = "Centralizar"
        if self.images_data[index]["combo_mode_ref"]:
            self.images_data[index]["combo_mode_ref"].set("Centralizar")
            
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
            self._set_thumbnail(target_index, target_path)
            self.images_data[target_index]["actions_frame_ref"].pack(anchor="e")
            self.update_clear_all_state()
        except Exception as e:
            print(f"Erro ao duplicar miniatura: {e}")

    def update_clear_all_state(self):
        """Ativa ou desativa o botão de limpar tudo com base nas imagens."""
        has_image = any(item["path"] != "" for item in self.images_data)
        self.btn_clear_all.configure(state="normal" if has_image else "disabled")

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
