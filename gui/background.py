"""Papel de parede dinâmico para janelas CustomTkinter.

O CustomTkinter não tem transparência alfa entre widgets. A técnica usada aqui é:
  1. Um CTkLabel (sem texto) ocupa a janela inteira (place relwidth/relheight=1) e fica na base do z-index.
  2. A imagem é recortada/redimensionada com Pillow (ImageOps.fit + LANCZOS) a cada mudança de tamanho
     (evento <Configure> com debounce) e exibida via CTkImage.
  3. Os cards são CTkFrame SÓLIDOS e escuros, empilhados diretamente na janela (sem contêineres "transparentes",
     que no CustomTkinter pintariam a cor da janela por cima da imagem).
  4. Os cantos arredondados dos cards são pintados com `bg_color`. Para não aparecerem "quinas" sobre o
     gradiente, cada card registrado recebe como `bg_color` a cor média do papel de parede sob os seus cantos.
"""
import customtkinter as ctk
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageOps


def generate_wallpaper(width=1600, height=1000):
    """Gera um papel de parede abstrato (gradiente suave desfocado, tons escuros azul/violeta/ciano)."""
    small = (320, 200)
    img = Image.new("RGB", small, (14, 18, 26))
    draw = ImageDraw.Draw(img)
    blobs = [
        ((60, 40), 90, (28, 58, 110)),
        ((270, 55), 80, (70, 38, 112)),
        ((205, 170), 110, (16, 86, 98)),
        ((25, 185), 70, (42, 52, 122)),
    ]
    for (cx, cy), r, color in blobs:
        draw.ellipse((cx - r, cy - r, cx + r, cy + r), fill=color)
    img = img.filter(ImageFilter.GaussianBlur(45))
    return img.resize((width, height), Image.Resampling.LANCZOS)


def _hex(rgb):
    return "#%02x%02x%02x" % tuple(int(c) for c in rgb)


def _window_scaling(window):
    """Fator de escala de DPI usado pelo CustomTkinter (CTkImage multiplica o tamanho por ele)."""
    try:
        return ctk.ScalingTracker.get_window_scaling(window)
    except Exception:
        return 1.0


class Wallpaper:
    """Camada de fundo responsiva. Crie ANTES dos demais widgets da janela."""

    MIN_SIZE = 100       # ignora tamanhos transitórios durante a criação da janela
    DEBOUNCE_MS = 60     # evita re-renderizar a cada pixel durante o redimensionamento

    def __init__(self, window, image=None):
        self.window = window
        self._base = image or generate_wallpaper()
        self._cards = []
        self._overlays = []
        self._job = None
        self._last_size = (0, 0)
        self._current = None  # PIL da versão renderizada (usada para amostrar cores)

        self._label = ctk.CTkLabel(window, text="", corner_radius=0)
        self._label.place(x=0, y=0, relwidth=1, relheight=1)
        self._label.lower()

        window.bind("<Configure>", self._on_configure, add="+")
        window.after(100, self.refresh)

    def add_header_overlay(self, title_text, icon_img=None, version_text=None, anchor_btn=None):
        """Desenha o título (com ícone RGBA) e o texto de versão diretamente nos pixels do papel de parede.
        
        Isso elimina 100% qualquer caixa/retângulo sólido de widget sob o ícone ou texto.
        """
        self._overlays.append({
            "title": title_text,
            "icon": icon_img.convert("RGBA") if icon_img is not None else None,
            "version": version_text,
            "anchor_btn": anchor_btn,
        })

    def _draw_overlays(self, img):
        if not self._overlays:
            return img
        scale = _window_scaling(self.window) or 1.0
        canvas = img.convert("RGBA")
        draw = ImageDraw.Draw(canvas)
        w, _ = canvas.size

        for ov in self._overlays:
            center_y = int(34 * scale)
            anchor_btn = ov.get("anchor_btn")
            if anchor_btn is not None and anchor_btn.winfo_exists() and anchor_btn.winfo_ismapped():
                center_y = anchor_btn.winfo_y() + anchor_btn.winfo_height() // 2

            # 1. Título centralizado com ícone transparente (alpha_composite real)
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

            if icon is not None:
                icon_px = max(16, round(26 * scale))
                gap = round(10 * scale)
                icon_resized = icon.resize((icon_px, icon_px), Image.Resampling.LANCZOS)
                total_w = icon_px + gap + tw
                start_x = (w - total_w) // 2
                icon_y = center_y - icon_px // 2
                canvas.alpha_composite(icon_resized, (start_x, icon_y))
                text_x = start_x + icon_px + gap
            else:
                text_x = (w - tw) // 2

            text_y = center_y - th // 2 - bbox[1]
            draw.text((text_x, text_y), title, font=title_font, fill=(248, 250, 252, 255))

            # 2. Texto de versão alinhado à esquerda do botão de atualização (sem frame intermediário)
            ver = ov.get("version")
            if ver and anchor_btn is not None and anchor_btn.winfo_exists() and anchor_btn.winfo_ismapped():
                v_size = max(10, round(11 * scale))
                try:
                    ver_font = ImageFont.truetype("segoeui.ttf", v_size)
                except Exception:
                    ver_font = ImageFont.load_default()
                v_bbox = draw.textbbox((0, 0), ver, font=ver_font)
                vw = v_bbox[2] - v_bbox[0]
                vh = v_bbox[3] - v_bbox[1]
                vx = anchor_btn.winfo_x() - vw - round(12 * scale)
                vy = center_y - vh // 2 - v_bbox[1]
                if vx > text_x + tw + round(16 * scale):
                    draw.text((vx, vy), ver, font=ver_font, fill=(148, 163, 184, 255))

        return canvas.convert("RGB")

    def register(self, widget, attr="bg_color", glass=None):
        """Registra um widget para ajustar uma de suas cores à do fundo sob ele.

        attr="bg_color": cards arredondados (cor pintada nos cantos).
        attr="fg_color": rótulos/blocos escritos direto sobre o papel de parede (sem card).
        glass=(cor_base, opacidade): efeito de "vidro". O preenchimento do card passa a ser a mistura
            da cor_base com a cor média do papel de parede sob ele (opacidade 1.0 = sólido).
        """
        self._cards.append((widget, attr, glass))

    def glass(self, card, base, alpha):
        """Cor de preenchimento 'vidro' de um card (base misturada ao fundo). Usada também no hover."""
        mean = self._region_mean(card)
        if mean is None:
            return base
        base_rgb = tuple(int(base[i:i + 2], 16) for i in (1, 3, 5))
        return _hex([alpha * bc + (1 - alpha) * mc for bc, mc in zip(base_rgb, mean)])

    def _region_mean(self, widget):
        """Cor média do papel de parede sob o widget (None se ainda não renderizado)."""
        if self._current is None:
            return None
        w, h = self._current.size
        x0 = widget.winfo_rootx() - self.window.winfo_rootx()
        y0 = widget.winfo_rooty() - self.window.winfo_rooty()
        box = (min(max(x0, 0), w - 1), min(max(y0, 0), h - 1),
               min(max(x0 + widget.winfo_width(), 1), w), min(max(y0 + widget.winfo_height(), 1), h))
        if box[2] <= box[0] or box[3] <= box[1]:
            return None
        return self._current.crop(box).resize((1, 1), Image.Resampling.BOX).getpixel((0, 0))

    # ------------------------------------------------------------------
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

        # Recorta e redimensiona proporcionalmente (sem distorção)
        raw = ImageOps.fit(self._base, (w, h), method=Image.Resampling.LANCZOS, centering=(0.5, 0.5))
        self._current = self._draw_overlays(raw)
        scale = _window_scaling(self.window) or 1.0
        photo = ctk.CTkImage(light_image=self._current, dark_image=self._current, size=(w / scale, h / scale))
        self._label.configure(image=photo)
        self._label._wallpaper_ref = photo  # evita coleta de lixo
        self._label.lower()
        self.window.after_idle(self._tint_cards)

    def _tint_cards(self):
        """Ajusta o bg_color dos cantos de cada card para a cor do fundo naquela região."""
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

