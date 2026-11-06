"""Componentes visuais autônomos do Buscador de Perfis ICC (Dark Glassmorphism).

Totalmente independente de alterações no aplicativo principal, mantendo a mesma identidade
visual (Segoe UI, vidro escuro translúcido, pílulas arredondadas e suporte a Touchpad no Tk 9).
"""
import customtkinter as ctk
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageOps

FONT_FAMILY = "Segoe UI"

BG_MAIN = "#11141A"
BG_MODAL_KEY = "#010203"

CARD_BG = "#161B22"
CARD_BG_HOVER = "#1C222B"
CARD_BORDER = "#2D3748"
GLASS_ALPHA = 0.84
INNER_CARD_BG = "#121720"
INNER_CARD_BORDER = "#253041"

TEXT_TITLE = "#F8FAFC"
TEXT_BODY = "#CBD5E1"
TEXT_MUTED = "#94A3B8"
TEXT_DISABLED = "#5B6678"
TEXT_ON_SECONDARY = "#E2E8F0"

ACCENT = "#0A84FF"
ACCENT_HOVER = "#0071E3"

SUCCESS_BG = "#122B22"
SUCCESS_BORDER = "#1E4D3B"
SUCCESS_TEXT = "#34D399"

BADGE_CLOUD_BG = "#17253B"
BADGE_CLOUD_TEXT = "#60A5FA"

BADGE_PORTAL_BG = "#252136"
BADGE_PORTAL_TEXT = "#C084FC"

SECONDARY = "#262E3B"
SECONDARY_HOVER = "#323D4D"

PILL_UTILITY = "#1E2633"
PILL_UTILITY_HOVER = "#2B3648"
PILL_BUTTON = "#283342"
PILL_BUTTON_HOVER = "#364457"

MENU_BG = "#1E2633"
MENU_BG_DISABLED = "#161C26"
MENU_HOVER = "#283546"
MENU_BORDER = "#2E3A4B"
MENU_TEXT = "#F1F5F9"
MENU_ARROW = "#94A3B8"
DROPDOWN_BG = "#161D27"
DROPDOWN_HOVER = "#243142"
DROPDOWN_TEXT = "#E2E8F0"
DROPDOWN_BORDER = "#2B3748"

MODAL_BG = "#141A24"
MODAL_BORDER = "#2E3A4B"
MODAL_CARD_BG = "#181F2B"
MODAL_CARD_BORDER = "#283445"

RADIUS_CARD = 16
RADIUS_MODAL = 18
RADIUS_PILL = 16
RADIUS_PILL_LG = 22


def font(size: int = 13, weight: str = "normal", underline: bool = False) -> ctk.CTkFont:
    return ctk.CTkFont(family=FONT_FAMILY, size=size, weight=weight, underline=underline)


def _hex(rgb) -> str:
    return "#%02x%02x%02x" % tuple(int(c) for c in rgb)


def window_scaling(widget) -> float:
    try:
        return ctk.ScalingTracker.get_window_scaling(widget) or 1.0
    except Exception:
        return 1.0


def generate_wallpaper(width: int = 1600, height: int = 1000) -> Image.Image:
    """Papel de parede abstrato escuro (azul/violeta/ciano) em harmonia com o OpenMug Studio."""
    small = (320, 200)
    img = Image.new("RGB", small, (14, 18, 26))
    draw = ImageDraw.Draw(img)
    blobs = [
        ((55, 42), 92, (24, 62, 118)),
        ((268, 50), 82, (66, 36, 110)),
        ((200, 168), 112, (16, 88, 102)),
        ((30, 180), 72, (40, 50, 120)),
    ]
    for (cx, cy), r, color in blobs:
        draw.ellipse((cx - r, cy - r, cx + r, cy + r), fill=color)
    img = img.filter(ImageFilter.GaussianBlur(45))
    return img.resize((width, height), Image.Resampling.LANCZOS)


def make_radar_icon(color=(148, 163, 184, 255), size: int = 14) -> ctk.CTkImage:
    """Ícone minimalista de globo/radar para o mapa das 10 marcas."""
    s = 64
    img = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.ellipse((10, 10, 54, 54), outline=color, width=4)
    d.ellipse((23, 10, 41, 54), outline=color, width=3)
    d.line([(11, 32), (53, 32)], fill=color, width=3)
    return ctk.CTkImage(light_image=img, dark_image=img, size=(size, size))


def make_chevron_icon(color=(148, 163, 184, 255), size: int = 12) -> ctk.CTkImage:
    s = 64
    img = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.line([(16, 24), (32, 40), (48, 24)], fill=color, width=5, joint="curve")
    return ctk.CTkImage(light_image=img, dark_image=img, size=(size, size))


class CircleIconButton(ctk.CTkButton):
    """Botão circular sem minsize lateral extra do CustomTkinter."""

    def _create_grid(self):
        super()._create_grid()
        self.grid_columnconfigure(0, minsize=0)
        self.grid_columnconfigure(4, minsize=0)


class Wallpaper:
    """Camada de fundo responsiva com composição alfa de cabeçalho e vidro nos cards."""

    MIN_SIZE = 100
    DEBOUNCE_MS = 60

    def __init__(self, window, image=None):
        self.window = window
        self._base = image or generate_wallpaper()
        self._cards = []
        self._overlays = []
        self._job = None
        self._last_size = (0, 0)
        self._current = None

        self._label = ctk.CTkLabel(window, text="", corner_radius=0)
        self._label.place(x=0, y=0, relwidth=1, relheight=1)
        self._label.lower()

        window.bind("<Configure>", self._on_configure, add="+")
        window.after(100, self.refresh)

    def add_header_overlay(self, title_text: str, icon_img=None, subtitle_text: str = None, anchor_btn=None):
        self._overlays.append({
            "title": title_text,
            "icon": icon_img.convert("RGBA") if icon_img is not None else None,
            "subtitle": subtitle_text,
            "anchor_btn": anchor_btn,
        })

    def _draw_overlays(self, img: Image.Image) -> Image.Image:
        if not self._overlays:
            return img
        scale = window_scaling(self.window)
        canvas = img.convert("RGBA")
        draw = ImageDraw.Draw(canvas)
        w, _ = canvas.size

        for ov in self._overlays:
            center_y = int(32 * scale)
            anchor_btn = ov.get("anchor_btn")
            if anchor_btn is not None and anchor_btn.winfo_exists() and anchor_btn.winfo_ismapped():
                center_y = anchor_btn.winfo_y() + anchor_btn.winfo_height() // 2

            title = ov.get("title") or ""
            icon = ov.get("icon")
            font_size = max(12, round(18 * scale))
            try:
                title_font = ImageFont.truetype("segoeuib.ttf", font_size)
            except Exception:
                title_font = ImageFont.load_default()

            bbox = draw.textbbox((0, 0), title, font=title_font)
            tw = bbox[2] - bbox[0]
            th = bbox[3] - bbox[1]

            start_x = int(28 * scale)
            if icon is not None:
                icon_px = max(16, round(26 * scale))
                gap = round(10 * scale)
                icon_resized = icon.resize((icon_px, icon_px), Image.Resampling.LANCZOS)
                icon_y = center_y - icon_px // 2
                canvas.alpha_composite(icon_resized, (start_x, icon_y))
                text_x = start_x + icon_px + gap
            else:
                text_x = start_x

            text_y = center_y - th // 2 - bbox[1]
            draw.text((text_x, text_y), title, font=title_font, fill=(248, 250, 252, 255))

            sub = ov.get("subtitle")
            if sub:
                s_size = max(10, round(11 * scale))
                try:
                    sub_font = ImageFont.truetype("segoeui.ttf", s_size)
                except Exception:
                    sub_font = ImageFont.load_default()
                s_bbox = draw.textbbox((0, 0), sub, font=sub_font)
                sh = s_bbox[3] - s_bbox[1]
                sx = text_x + tw + round(12 * scale)
                sy = center_y - sh // 2 - s_bbox[1]
                max_right = anchor_btn.winfo_x() - round(14 * scale) if (anchor_btn and anchor_btn.winfo_ismapped()) else w
                if sx + (s_bbox[2] - s_bbox[0]) < max_right:
                    draw.text((sx, sy), sub, font=sub_font, fill=(148, 163, 184, 255))

        return canvas.convert("RGB")

    def register(self, widget, attr: str = "bg_color", glass=None):
        self._cards.append((widget, attr, glass))

    def glass(self, card, base: str, alpha: float) -> str:
        mean = self._region_mean(card)
        if mean is None:
            return base
        base_rgb = tuple(int(base[i:i + 2], 16) for i in (1, 3, 5))
        return _hex([alpha * bc + (1 - alpha) * mc for bc, mc in zip(base_rgb, mean)])

    def _region_mean(self, widget):
        if self._current is None:
            return None
        w, h = self._current.size
        x0 = widget.winfo_rootx() - self.window.winfo_rootx()
        y0 = widget.winfo_rooty() - self.window.winfo_rooty()
        box = (
            min(max(x0, 0), w - 1),
            min(max(y0, 0), h - 1),
            min(max(x0 + widget.winfo_width(), 1), w),
            min(max(y0 + widget.winfo_height(), 1), h),
        )
        if box[2] <= box[0] or box[3] <= box[1]:
            return None
        return self._current.crop(box).resize((1, 1), Image.Resampling.BOX).getpixel((0, 0))

    def _on_configure(self, event):
        if event.widget is not self.window:
            return
        if self._job is not None:
            self.window.after_cancel(self._job)
        self._job = self.window.after(self.DEBOUNCE_MS, self.refresh)

    def refresh(self):
        self._job = None
        if not self.window.winfo_exists():
            return
        w, h = self.window.winfo_width(), self.window.winfo_height()
        if w < self.MIN_SIZE or h < self.MIN_SIZE or (w, h) == self._last_size:
            return
        self._last_size = (w, h)

        raw = ImageOps.fit(self._base, (w, h), method=Image.Resampling.LANCZOS, centering=(0.5, 0.5))
        self._current = self._draw_overlays(raw)
        scale = window_scaling(self.window)
        photo = ctk.CTkImage(light_image=self._current, dark_image=self._current, size=(w / scale, h / scale))
        self._label.configure(image=photo)
        self._label._wallpaper_ref = photo
        self._label.lower()
        self.window.after_idle(self._tint_cards)

    def _tint_cards(self):
        if self._current is None or not self.window.winfo_exists():
            return
        w, h = self._current.size
        ox, oy = self.window.winfo_rootx(), self.window.winfo_rooty()
        for card, attr, glass in self._cards:
            try:
                if not card.winfo_exists() or not card.winfo_ismapped():
                    continue
                x0, y0 = card.winfo_rootx() - ox, card.winfo_rooty() - oy
                x1, y1 = x0 + card.winfo_width(), y0 + card.winfo_height()
                pts = [(x0, y0), (x1, y0), (x0, y1), (x1, y1)]
                px = [self._current.getpixel((min(max(x, 0), w - 1), min(max(y, 0), h - 1))) for x, y in pts]
                avg = [sum(p[i] for p in px) / 4 for i in range(3)]
                colors = {attr: _hex(avg)}
                if glass:
                    colors["fg_color"] = self.glass(card, glass[0], glass[1])
                card.configure(**colors)
            except Exception:
                pass


def attach_smooth_scroll(host_window, scrollable_frame: ctk.CTkScrollableFrame):
    """Habilita rolagem suave tanto por MouseWheel quanto por Precision Touchpad (<TouchpadScroll> no Tk 9)."""
    scroll_acc = [0.0]

    def _widget_inside(target_widget) -> bool:
        try:
            w = target_widget
            while w is not None:
                if w is scrollable_frame:
                    return True
                w = getattr(w, "master", None)
        except Exception:
            pass
        return False

    def _on_wheel(event):
        if not host_window.winfo_exists() or not scrollable_frame.winfo_exists():
            return
        if not _widget_inside(event.widget):
            return
        if not scrollable_frame._check_if_valid_scroll(event.widget):
            if scrollable_frame._parent_canvas.yview() != (0.0, 1.0):
                scrollable_frame._parent_canvas.yview("scroll", -int(event.delta / 6), "units")

    def _on_touchpad(event):
        if not host_window.winfo_exists() or not scrollable_frame.winfo_exists():
            return
        if not _widget_inside(event.widget):
            return
        if scrollable_frame._parent_canvas.yview() == (0.0, 1.0):
            return
        raw_dy = event.delta & 0xFFFF
        if raw_dy >= 0x8000:
            raw_dy -= 0x10000
        if raw_dy != 0:
            scroll_acc[0] += -raw_dy * 1.5
            steps = int(scroll_acc[0])
            if steps != 0:
                scroll_acc[0] -= steps
                scrollable_frame._parent_canvas.yview("scroll", steps, "units")

    host_window.bind_all("<MouseWheel>", _on_wheel, add="+")
    try:
        host_window.bind_all("<TouchpadScroll>", _on_touchpad, add="+")
    except Exception:
        pass


class CascadingPillSelect(ctk.CTkFrame):
    """Seletor pílula arredondado com suporte a estado desabilitado, rolagem e busca rápida."""

    _active_owner = None

    def __init__(
        self,
        master,
        placeholder: str = "Selecione...",
        values=None,
        command=None,
        height: int = 38,
        state: str = "normal",
        **kwargs,
    ):
        super().__init__(
            master,
            fg_color=MENU_BG if state == "normal" else MENU_BG_DISABLED,
            corner_radius=RADIUS_PILL,
            border_width=1,
            border_color=MENU_BORDER,
            height=height,
            **kwargs,
        )
        self.pack_propagate(False)

        self._placeholder = placeholder
        self._values = list(values or [])
        self._value = ""
        self._command = command
        self._state = state
        self._popup_win = None
        self._outside_bindings = []

        self._chevron_normal = make_chevron_icon((148, 163, 184, 255), size=12)
        self._chevron_disabled = make_chevron_icon((91, 102, 120, 255), size=12)

        self._lbl = ctk.CTkLabel(
            self,
            text=placeholder,
            font=font(13),
            text_color=MENU_TEXT if (state == "normal" and self._value) else TEXT_MUTED,
            anchor="w",
        )
        self._lbl.pack(side="left", fill="x", expand=True, padx=(14, 6))

        self._arrow = ctk.CTkLabel(
            self,
            text="",
            image=self._chevron_normal if state == "normal" else self._chevron_disabled,
            width=18,
        )
        self._arrow.pack(side="right", padx=(0, 12))

        for w in (self, self._lbl, self._arrow):
            w.bind("<Button-1>", self._on_click)
            w.bind("<Enter>", self._on_enter)
            w.bind("<Leave>", self._on_leave)
        self._refresh_visuals()

    def get(self) -> str:
        return self._value

    def set(self, value: str):
        self._value = value or ""
        self._refresh_visuals()

    def configure_options(self, values, selected: str = "", state: str = "normal", placeholder: str = None):
        if placeholder is not None:
            self._placeholder = placeholder
        self._values = list(values or [])
        self._value = selected if selected in self._values else ""
        self._state = state if self._values else "disabled"
        self._close_popup()
        self._refresh_visuals()

    def _refresh_visuals(self):
        enabled = self._state == "normal" and len(self._values) > 0
        cursor = "hand2" if enabled else "arrow"
        self.configure(
            fg_color=MENU_BG if enabled else MENU_BG_DISABLED,
            border_color=ACCENT if (self._popup_win and self._popup_win.winfo_exists()) else MENU_BORDER,
            cursor=cursor,
        )
        display_text = self._value if self._value else self._placeholder
        txt_color = MENU_TEXT if (enabled and self._value) else (TEXT_MUTED if enabled else TEXT_DISABLED)
        self._lbl.configure(
            text=display_text,
            text_color=txt_color,
            font=font(13, "bold" if self._value else "normal"),
            cursor=cursor,
        )
        self._arrow.configure(
            image=self._chevron_normal if enabled else self._chevron_disabled,
            cursor=cursor,
        )

    def _on_enter(self, _event=None):
        if self._state == "normal" and self._values:
            self.configure(fg_color=MENU_HOVER)

    def _on_leave(self, _event=None):
        if self._state == "normal" and self._values:
            self.configure(fg_color=MENU_BG)

    def _on_click(self, _event=None):
        if self._state != "normal" or not self._values:
            return
        if self._popup_win is not None and self._popup_win.winfo_exists():
            self._close_popup()
        else:
            self._open_popup()

    def _open_popup(self):
        prev = CascadingPillSelect._active_owner
        if prev is not None and prev is not self:
            prev._close_popup()
        self._close_popup()
        CascadingPillSelect._active_owner = self

        scale = window_scaling(self)
        show_search = len(self._values) > 8
        visible_rows = min(len(self._values), 8)
        row_h = 34
        search_h = 42 if show_search else 0
        pad_y = 8

        logical_w = max(int(self.winfo_width() / scale), 220)
        logical_h = visible_rows * row_h + search_h + pad_y * 2 + (8 if len(self._values) > 8 else 0)

        px_w = round(logical_w * scale)
        px_h = round(logical_h * scale)
        pos_x = self.winfo_rootx()
        pos_y = self.winfo_rooty() + self.winfo_height() + round(5 * scale)

        screen_h = self.winfo_screenheight()
        if pos_y + px_h > screen_h - 40:
            pos_y = max(20, self.winfo_rooty() - px_h - round(5 * scale))

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
            fg_color=DROPDOWN_BG,
            corner_radius=14,
            border_width=1,
            border_color=DROPDOWN_BORDER,
            bg_color=BG_MODAL_KEY,
        )
        shell.pack(fill="both", expand=True)

        search_entry = None
        if show_search:
            search_entry = ctk.CTkEntry(
                shell,
                placeholder_text="Filtrar modelo...",
                height=30,
                corner_radius=10,
                fg_color="#11161F",
                border_color=MENU_BORDER,
                text_color=TEXT_TITLE,
                placeholder_text_color=TEXT_DISABLED,
                font=font(12),
            )
            search_entry.pack(fill="x", padx=8, pady=(8, 4))

        if len(self._values) > 8:
            list_container = ctk.CTkScrollableFrame(
                shell,
                fg_color="transparent",
                corner_radius=0,
                scrollbar_button_color=SECONDARY,
                scrollbar_button_hover_color=SECONDARY_HOVER,
            )
            list_container.pack(fill="both", expand=True, padx=4, pady=(2, 6))
            attach_smooth_scroll(popup, list_container)
        else:
            list_container = ctk.CTkFrame(shell, fg_color="transparent")
            list_container.pack(fill="both", expand=True, padx=4, pady=(4, 6))

        def _populate(query: str = ""):
            for child in list_container.winfo_children():
                child.destroy()
            q = query.strip().lower()
            filtered = [v for v in self._values if q in v.lower()] if q else self._values
            if not filtered:
                ctk.CTkLabel(
                    list_container,
                    text="Nenhum resultado",
                    font=font(12),
                    text_color=TEXT_DISABLED,
                ).pack(pady=10)
                return
            for val in filtered:
                is_sel = val == self._value
                btn = ctk.CTkButton(
                    list_container,
                    text=val,
                    anchor="w",
                    height=30,
                    corner_radius=9,
                    fg_color=DROPDOWN_HOVER if is_sel else "transparent",
                    hover_color=DROPDOWN_HOVER,
                    text_color="#FFFFFF" if is_sel else DROPDOWN_TEXT,
                    font=font(12, "bold" if is_sel else "normal"),
                    command=lambda chosen=val: self._choose(chosen),
                )
                btn.pack(fill="x", padx=4, pady=1)

        _populate()

        if search_entry is not None:
            search_entry.bind("<KeyRelease>", lambda _e: _populate(search_entry.get()))

        popup.deiconify()
        popup.lift()
        self._popup_win = popup
        self._refresh_visuals()

        if search_entry is not None:
            popup.after(40, search_entry.focus_set)

        self.after(60, self._install_outside_listeners)

    def _install_outside_listeners(self):
        if self._popup_win is None or not self._popup_win.winfo_exists():
            return
        top = self.winfo_toplevel()
        self._outside_bindings = [
            (top, "<ButtonPress-1>", top.bind("<ButtonPress-1>", self._on_root_click, add="+")),
            (top, "<Escape>", top.bind("<Escape>", lambda _e: self._close_popup(), add="+")),
            (top, "<Configure>", top.bind("<Configure>", self._on_root_configure, add="+")),
        ]
        self._last_root_rect = (top.winfo_rootx(), top.winfo_rooty(), top.winfo_width(), top.winfo_height())

    def _on_root_click(self, event):
        if self._popup_win is None or not self._popup_win.winfo_exists():
            return
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
            if cur != getattr(self, "_last_root_rect", cur):
                self._close_popup()

    def _choose(self, val: str):
        self._value = val
        self._close_popup()
        self._refresh_visuals()
        if self._command:
            self._command(val)

    def _close_popup(self):
        for widget, seq, funcid in self._outside_bindings:
            try:
                if funcid and widget.winfo_exists():
                    widget.unbind(seq, funcid)
            except Exception:
                pass
        self._outside_bindings = []

        if CascadingPillSelect._active_owner is self:
            CascadingPillSelect._active_owner = None

        if self._popup_win is not None:
            try:
                if self._popup_win.winfo_exists():
                    self._popup_win.destroy()
            except Exception:
                pass
            self._popup_win = None
        if self.winfo_exists():
            self._refresh_visuals()

    def destroy(self):
        self._close_popup()
        super().destroy()

