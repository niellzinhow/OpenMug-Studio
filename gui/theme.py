"""Sistema de design do OpenMug Studio (dark glassmorphism minimalista).

Centraliza cores, raios de borda e fontes para que todas as telas usem o mesmo padrão visual.
"""
import customtkinter as ctk
from PIL import Image, ImageDraw

# --- Fontes ---------------------------------------------------------------
FONT_FAMILY = "Segoe UI"


def font(size=13, weight="normal", underline=False):
    return ctk.CTkFont(family=FONT_FAMILY, size=size, weight=weight, underline=underline)


# --- Cores ----------------------------------------------------------------
BG_MAIN = "#11141A"          # fundo da janela principal
BG_PREVIEW = "#0E1117"       # fundo da prévia
BG_MODAL_KEY = "#010203"     # cor-chave de transparência (cantos arredondados do modal)

CARD_BG = "#161B22"
CARD_BG_HOVER = "#1C222B"
CARD_BORDER = "#2D3748"
GLASS_ALPHA = 0.84           # opacidade dos cards (1.0 = sólido; menor = mais transparente)
THUMB_BG = "#13171F"

TEXT_TITLE = "#F8FAFC"
TEXT_BODY = "#CBD5E1"
TEXT_MUTED = "#94A3B8"
TEXT_DISABLED = "#5B6678"
TEXT_ON_SECONDARY = "#E2E8F0"

ACCENT = "#0A84FF"
ACCENT_HOVER = "#0071E3"

SECONDARY = "#262E3B"
SECONDARY_HOVER = "#323D4D"

PILL_UTILITY = "#1E2633"      # ICC / atualização
PILL_UTILITY_HOVER = "#2B3648"
PILL_BUTTON = "#283342"       # "Escolher imagem"
PILL_BUTTON_HOVER = "#364457"
CLEAR_ALL = "#232B37"
CLEAR_ALL_HOVER = "#2F3A4B"

DANGER_BG = "#2A1B1E"
DANGER_HOVER = "#3A2226"
DANGER_TEXT = "#FF453A"

MENU_BG = "#1E2633"
MENU_HOVER = "#283546"
MENU_BORDER = "#2E3A4B"
MENU_TEXT = "#F1F5F9"
MENU_ARROW = "#94A3B8"
DROPDOWN_BG = "#161D27"
DROPDOWN_HOVER = "#243142"
DROPDOWN_TEXT = "#E2E8F0"
DROPDOWN_BORDER = "#2B3748"

# Prévia
PAPER_BORDER = "#262F3D"
PAPER_SHADOW = "#080A0E"
CAPSULE_BG = "#161C26"
CAPSULE_BORDER = "#2A3445"
CAPSULE_BACK = "#242D3B"
CAPSULE_SECONDARY = "#262F3E"

# Modal de notas
MODAL_BG = "#141A24"
MODAL_BORDER = "#2E3A4B"
MODAL_CARD_BG = "#181F2B"
MODAL_CARD_BORDER = "#283445"
MODAL_SECTION = "#8291A5"

# --- Raios ----------------------------------------------------------------
RADIUS_CARD = 16
RADIUS_MODAL = 18
RADIUS_PILL = 16
RADIUS_PILL_LG = 22
RADIUS_THUMB = 10
RADIUS_MENU = 14

# --- Miniatura (16:9) -----------------------------------------------------
THUMB_SIZE = (169, 95)


def rounded_image(img, radius=RADIUS_THUMB):
    """Retorna uma cópia RGBA da imagem com cantos arredondados."""
    img = img.convert("RGBA")
    scale = 4  # supersampling para bordas suaves
    mask = Image.new("L", (img.width * scale, img.height * scale), 0)
    ImageDraw.Draw(mask).rounded_rectangle(
        (0, 0, img.width * scale - 1, img.height * scale - 1), radius=radius * scale, fill=255)
    mask = mask.resize(img.size, Image.Resampling.LANCZOS)
    img.putalpha(mask)
    return img


def make_notes_icon(color=(148, 163, 184, 255), size=14):
    """Desenha um ícone minimalista de documento/folha com supersampling e retorna um CTkImage."""
    s = 64
    img = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    # Contorno da folha com canto superior direito dobrado
    pts = [(14, 8), (38, 8), (50, 20), (50, 56), (14, 56), (14, 8)]
    d.line(pts, fill=color, width=4, joint="curve")
    d.line([(38, 8), (38, 20), (50, 20)], fill=color, width=3)
    # Linhas internas de texto
    d.line([(22, 30), (42, 30)], fill=color, width=3)
    d.line([(22, 39), (42, 39)], fill=color, width=3)
    d.line([(22, 48), (34, 48)], fill=color, width=3)
    return ctk.CTkImage(light_image=img, dark_image=img, size=(size, size))


class CircleIconButton(ctk.CTkButton):
    """Botão circular perfeito no CustomTkinter (zera o minsize lateral imposto pelo corner_radius)."""

    def _create_grid(self):
        super()._create_grid()
        self.grid_columnconfigure(0, minsize=0)
        self.grid_columnconfigure(4, minsize=0)


def make_chevron_icon(color=(148, 163, 184, 255), size=12):
    """Desenha um chevron minimalista (˅) suave com supersampling e retorna um CTkImage."""
    s = 64
    img = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    pts = [(16, 24), (32, 40), (48, 24)]
    d.line(pts, fill=color, width=5, joint="curve")
    return ctk.CTkImage(light_image=img, dark_image=img, size=(size, size))


class PillOptionMenu(ctk.CTkOptionMenu):
    """CTkOptionMenu refatorado em formato pílula contínua + menu suspenso flutuante arredondado.

    Resolve duas limitações nativas do CTkOptionMenu no Windows:
      1. Botão gatilho unificado: hover pinta a pílula inteira (sem quadrado isolado na seta) e usa
         uma seta minimalista em cinza suave (#94A3B8).
      2. Menu suspenso sem borda branca: substitui o `tkinter.Menu` clássico do sistema operacional
         (que exibe cantos retos de 90° e moldura branca no Windows) por um popup flutuante leve
         (`CTkToplevel` sem bordas nativas, com cantos arredondados e itens espaçados).
    """

    _active_popup_owner = None

    def __init__(self, master, values=None, command=None, width=142, height=33, corner_radius=16,
                 fg_color=MENU_BG, button_color=MENU_BG, button_hover_color=MENU_HOVER,
                 hover_color=MENU_HOVER, text_color=MENU_TEXT, arrow_color=MENU_ARROW,
                 dropdown_fg_color=DROPDOWN_BG, dropdown_hover_color=DROPDOWN_HOVER,
                 dropdown_text_color=DROPDOWN_TEXT, dropdown_border_color=DROPDOWN_BORDER,
                 font_obj=None, dropdown_font_obj=None, dynamic_resizing=False, **kwargs):
        self._pill_hover_color = hover_color or button_hover_color
        self._arrow_color = arrow_color
        self._popup_fg = dropdown_fg_color
        self._popup_hover = dropdown_hover_color
        self._popup_text = dropdown_text_color
        self._popup_border = dropdown_border_color
        self._popup_font = dropdown_font_obj or font(12)
        self._popup_win = None
        self._outside_bindings = []

        super().__init__(
            master=master,
            values=values or [],
            command=command,
            width=width,
            height=height,
            corner_radius=corner_radius,
            fg_color=fg_color,
            button_color=button_color,
            button_hover_color=self._pill_hover_color,
            text_color=text_color,
            dropdown_fg_color=dropdown_fg_color,
            dropdown_hover_color=dropdown_hover_color,
            dropdown_text_color=dropdown_text_color,
            font=font_obj or font(12),
            dropdown_font=self._popup_font,
            dynamic_resizing=dynamic_resizing,
            **kwargs,
        )

    def _draw(self, no_color_updates=False):
        super()._draw(no_color_updates)
        # Deixa a seta minimalista em tom suave (#94A3B8) em vez do branco intenso padrão
        self._canvas.itemconfig("dropdown_arrow", fill=self._apply_appearance_mode(self._arrow_color))

    def _on_enter(self, event=0):
        # Hover contínuo em toda a pílula (elimina a divisão entre texto e quadrado da seta)
        if self._hover and self._state == "normal" and len(self._values) > 0:
            hc = self._apply_appearance_mode(self._pill_hover_color)
            self._canvas.itemconfig("inner_parts_left", outline=hc, fill=hc)
            self._canvas.itemconfig("inner_parts_right", outline=hc, fill=hc)
            self._text_label.configure(bg=hc)

    def _on_leave(self, event=0):
        fc = self._apply_appearance_mode(self._fg_color)
        bc = self._apply_appearance_mode(self._button_color)
        self._canvas.itemconfig("inner_parts_left", outline=fc, fill=fc)
        self._canvas.itemconfig("inner_parts_right", outline=bc, fill=bc)
        self._text_label.configure(bg=fc)

    def _clicked(self, event=0):
        if self._state == "disabled" or len(self._values) == 0:
            return
        if self._popup_win is not None and self._popup_win.winfo_exists():
            self._close_popup()
        else:
            self._open_dropdown_menu()

    def _open_dropdown_menu(self):
        # Fecha qualquer outro menu pílula que esteja aberto na tela
        prev = PillOptionMenu._active_popup_owner
        if prev is not None and prev is not self:
            prev._close_popup()
        self._close_popup()
        PillOptionMenu._active_popup_owner = self

        try:
            scale = ctk.ScalingTracker.get_window_scaling(self) or 1.0
        except Exception:
            scale = 1.0

        item_h = 34
        pad_y = 6
        logical_w = max(self._desired_width, 142)
        logical_h = len(self._values) * item_h + pad_y * 2 + 4

        px_w = max(self.winfo_width(), round(logical_w * scale))
        px_h = round(logical_h * scale)
        # CTkToplevel aplica window_scaling sobre geometry(WxH), mas NÃO sobre +X+Y
        pos_x = self.winfo_rootx() + (self.winfo_width() - px_w) // 2
        pos_y = self.winfo_rooty() + self.winfo_height() + round(5 * scale)

        popup = ctk.CTkToplevel(self)
        popup.withdraw()
        popup.overrideredirect(True)
        popup.attributes("-topmost", True)
        popup.configure(fg_color=BG_MODAL_KEY)
        try:
            popup.attributes("-transparentcolor", BG_MODAL_KEY)
        except Exception:
            pass
        popup.geometry(f"{logical_w}x{logical_h}+{pos_x}+{pos_y}")

        shell = ctk.CTkFrame(
            popup,
            fg_color=self._popup_fg,
            corner_radius=14,
            border_width=1,
            border_color=self._popup_border,
            bg_color=BG_MODAL_KEY,
        )
        shell.pack(fill="both", expand=True)

        current = self.get()
        for idx, val in enumerate(self._values):
            is_selected = (val == current)
            top_pad = (pad_y, 2) if idx == 0 else (2, pad_y if idx == len(self._values) - 1 else 2)
            btn = ctk.CTkButton(
                shell,
                text=val,
                anchor="w",
                height=item_h - 4,
                corner_radius=10,
                fg_color=self._popup_hover if is_selected else "transparent",
                hover_color=self._popup_hover,
                text_color="#FFFFFF" if is_selected else self._popup_text,
                font=font(12, "bold" if is_selected else "normal"),
                command=lambda v=val: self._select_from_popup(v),
            )
            btn.pack(fill="x", padx=6, pady=top_pad)

        popup.deiconify()
        popup.lift()
        self._popup_win = popup

        # Aguarda o ButtonRelease-1 do clique atual terminar antes de registrar os ouvintes de clique externo
        self.after(60, self._install_outside_listeners)

    def _install_outside_listeners(self):
        if self._popup_win is None or not self._popup_win.winfo_exists():
            return
        top = self.winfo_toplevel()
        self._outside_bindings = [
            (top, "<ButtonPress-1>", top.bind("<ButtonPress-1>", self._on_root_click, add="+")),
            (top, "<Escape>", top.bind("<Escape>", lambda e: self._close_popup(), add="+")),
            (top, "<Configure>", top.bind("<Configure>", self._on_root_configure, add="+")),
            (top, "<FocusOut>", top.bind("<FocusOut>", self._on_root_focus_out, add="+")),
        ]
        self._last_root_pos = (top.winfo_rootx(), top.winfo_rooty(), top.winfo_width(), top.winfo_height())

    def _on_root_click(self, event):
        if self._popup_win is None or not self._popup_win.winfo_exists():
            return
        # Ignora cliques dentro do próprio popup ou no botão gatilho (que já alterna via _clicked)
        px, py = self._popup_win.winfo_rootx(), self._popup_win.winfo_rooty()
        pw, ph = self._popup_win.winfo_width(), self._popup_win.winfo_height()
        if px <= event.x_root <= px + pw and py <= event.y_root <= py + ph:
            return
        bx, by = self.winfo_rootx(), self.winfo_rooty()
        bw, bh = self.winfo_width(), self.winfo_height()
        if bx <= event.x_root <= bx + bw and by <= event.y_root <= by + bh:
            return
        self._close_popup()

    def _on_root_configure(self, event):
        if self._popup_win is None or not self._popup_win.winfo_exists():
            return
        top = self.winfo_toplevel()
        if event.widget is top:
            cur = (top.winfo_rootx(), top.winfo_rooty(), top.winfo_width(), top.winfo_height())
            if cur != getattr(self, "_last_root_pos", cur):
                self._close_popup()

    def _on_root_focus_out(self, event):
        if self._popup_win is None or not self._popup_win.winfo_exists():
            return
        top = self.winfo_toplevel()
        if event.widget is top:
            self.after(80, lambda: self._close_if_app_unfocused(top))

    def _close_if_app_unfocused(self, top):
        if self._popup_win is None or not self._popup_win.winfo_exists():
            return
        try:
            focused = top.focus_displayof()
            if focused is None:
                self._close_popup()
        except Exception:
            self._close_popup()

    def _select_from_popup(self, value):
        self._close_popup()
        self._dropdown_callback(value)

    def _close_popup(self):
        for widget, seq, funcid in self._outside_bindings:
            try:
                if funcid and widget.winfo_exists():
                    widget.unbind(seq, funcid)
            except Exception:
                pass
        self._outside_bindings = []

        if PillOptionMenu._active_popup_owner is self:
            PillOptionMenu._active_popup_owner = None

        if self._popup_win is not None:
            try:
                if self._popup_win.winfo_exists():
                    self._popup_win.destroy()
            except Exception:
                pass
            self._popup_win = None

    def destroy(self):
        self._close_popup()
        super().destroy()

