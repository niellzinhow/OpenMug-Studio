"""Interface gráfica independente do Buscador de Perfis ICC para Sublimação.

Execução direta sem tocar em nenhum arquivo do OpenMug Studio:
    python -m icc_finder
    python icc_finder/app.py
"""
import os
import subprocess
import sys
import threading
import webbrowser
from tkinter import messagebox
from typing import List, Optional

import customtkinter as ctk
from PIL import Image

# Permite execução tanto via `python -m icc_finder` quanto via `python icc_finder/app.py`
if __package__ in (None, ""):
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from icc_finder import MODULE_VERSION
from icc_finder.crawler import (
    DOWNLOADS_DIR,
    TOP_10_INK_BRANDS,
    BrandScanReport,
    CatalogIndex,
    ProfileEntry,
    build_seed_catalog,
    download_profile_file,
    load_cache,
    scan_all_brands,
)
from icc_finder import ui_components as U


def _find_project_icon() -> Optional[str]:
    here = os.path.dirname(os.path.abspath(__file__))
    parent_ico = os.path.join(os.path.dirname(here), "OpenMug Studio.ico")
    if os.path.exists(parent_ico):
        return parent_ico
    return None


class ICCFinderApp(ctk.CTk):
    """Aplicativo independente para varredura web e seleção em cascata de Perfis ICC."""

    ALL_BRANDS_Prefix = "✦ Todas disponíveis"

    def __init__(self):
        ctk.set_appearance_mode("dark")
        super().__init__()

        self.title("OpenMug ICC Finder — Perfis de Cor Sublimáticos")
        ico_path = _find_project_icon()
        self._icon_pil = None
        if ico_path:
            try:
                self.iconbitmap(ico_path)
                self._icon_pil = Image.open(ico_path)
            except Exception:
                pass

        self.geometry("980x720")
        self.minsize(820, 600)
        self.configure(fg_color=U.BG_MAIN)

        self._scanning = False
        self._entries: List[ProfileEntry] = []
        self._reports: List[BrandScanReport] = []
        self._last_scan_str = ""
        self._index = CatalogIndex([])

        # Carrega cache local se existir; caso contrário carrega semente e inicia varredura ao vivo
        cached = load_cache()
        self._needs_initial_scan = cached is None
        if cached:
            self._entries, self._reports, self._last_scan_str = cached
        else:
            self._entries, self._reports = build_seed_catalog()
            self._last_scan_str = "Varredura inicial pendente"
        self._index = CatalogIndex(self._entries)

        self.wallpaper = U.Wallpaper(self)
        self._build_ui()
        self._populate_printer_brands(preserve=False)

        # Garante abertura sempre na frente no Windows
        self.after(50, self._bring_to_front)

        if self._needs_initial_scan:
            self.after(500, self.start_internet_scan)

    def _bring_to_front(self):
        if os.name == "nt":
            try:
                self.state("zoomed")
            except Exception:
                pass
        try:
            self.lift()
            self.attributes("-topmost", True)
            self.focus_force()
            self.after(250, lambda: self.attributes("-topmost", False))
        except Exception:
            pass

    # ------------------------------------------------------------------
    # Construção da Interface
    # ------------------------------------------------------------------
    def _build_ui(self):
        scale = U.window_scaling(self)

        # --- Botões utilitários no topo direito (direto sobre o papel de parede) ---
        radar_icon = U.make_radar_icon()
        self.btn_map = ctk.CTkButton(
            self,
            text="Onde estão as 10 marcas",
            image=radar_icon,
            compound="left",
            width=185,
            height=30,
            corner_radius=15,
            font=U.font(11, "bold"),
            fg_color=U.PILL_UTILITY,
            hover_color=U.PILL_UTILITY_HOVER,
            text_color=U.TEXT_ON_SECONDARY,
            command=self.show_brands_radar_modal,
        )
        self.btn_map.place(relx=1.0, x=round(-28 * scale), y=round(18 * scale), anchor="ne")
        self.wallpaper.register(self.btn_map)

        self.btn_scan = ctk.CTkButton(
            self,
            text="🔄  Varrer Internet Agora",
            width=176,
            height=30,
            corner_radius=15,
            font=U.font(11, "bold"),
            fg_color=U.ACCENT,
            hover_color=U.ACCENT_HOVER,
            text_color="#FFFFFF",
            command=self.start_internet_scan,
        )
        self.btn_scan.place(relx=1.0, x=round(-221 * scale), y=round(18 * scale), anchor="ne")
        self.wallpaper.register(self.btn_scan)

        self.btn_downloads = ctk.CTkButton(
            self,
            text="📂 Downloads",
            width=112,
            height=30,
            corner_radius=15,
            font=U.font(11),
            fg_color=U.PILL_UTILITY,
            hover_color=U.PILL_UTILITY_HOVER,
            text_color=U.TEXT_MUTED,
            command=self.open_downloads_folder,
        )
        self.btn_downloads.place(relx=1.0, x=round(-405 * scale), y=round(18 * scale), anchor="ne")
        self.wallpaper.register(self.btn_downloads)

        self.wallpaper.add_header_overlay(
            title_text="Buscador de Perfis ICC",
            icon_img=self._icon_pil,
            subtitle_text=f"Módulo Autônomo v{MODULE_VERSION} • Top 10 Tintas Sublimáticas",
            anchor_btn=self.btn_downloads,
        )

        # --- Barra de Status / Progresso da Varredura ---
        self.status_card = ctk.CTkFrame(
            self,
            fg_color=U.CARD_BG,
            corner_radius=U.RADIUS_CARD,
            border_width=1,
            border_color=U.CARD_BORDER,
        )
        self.status_card.pack(fill="x", padx=28, pady=(62, 8))
        self.wallpaper.register(self.status_card, glass=(U.CARD_BG, U.GLASS_ALPHA))

        status_row = ctk.CTkFrame(self.status_card, fg_color="transparent")
        status_row.pack(fill="x", padx=18, pady=(10, 8))

        self.lbl_status = ctk.CTkLabel(
            status_row,
            text=self._summary_status_text(),
            font=U.font(12),
            text_color=U.TEXT_BODY,
            anchor="w",
        )
        self.lbl_status.pack(side="left", fill="x", expand=True)

        self.lbl_color_dir = ctk.CTkLabel(
            status_row,
            text="Pasta de Cores do Windows ↗",
            font=U.font(11),
            text_color=U.ACCENT,
            cursor="hand2",
        )
        self.lbl_color_dir.pack(side="right")
        self.lbl_color_dir.bind("<Button-1>", lambda _e: self.open_windows_color_folder())

        self.progress = ctk.CTkProgressBar(
            self.status_card,
            height=5,
            corner_radius=3,
            fg_color="#1E2633",
            progress_color=U.ACCENT,
        )
        self.progress.set(1.0)
        self.progress.pack(fill="x", padx=18, pady=(0, 10))

        # --- Card Principal de Seleção em Cascata ---
        # Hierarquia estrita: Marca de impressora > Modelo de impressora > Marca de tinta
        self.filter_card = ctk.CTkFrame(
            self,
            fg_color=U.CARD_BG,
            corner_radius=U.RADIUS_CARD,
            border_width=1,
            border_color=U.CARD_BORDER,
        )
        self.filter_card.pack(fill="x", padx=28, pady=6)
        self.wallpaper.register(self.filter_card, glass=(U.CARD_BG, U.GLASS_ALPHA))

        header_filter = ctk.CTkFrame(self.filter_card, fg_color="transparent")
        header_filter.pack(fill="x", padx=18, pady=(12, 4))

        ctk.CTkLabel(
            header_filter,
            text="Seleção de Perfil em 3 Etapas  (Marca de Impressora  ›  Modelo de Impressora  ›  Marca de Tinta)",
            font=U.font(13, "bold"),
            text_color=U.TEXT_TITLE,
            anchor="w",
        ).pack(side="left")

        self.btn_reset_filters = ctk.CTkButton(
            header_filter,
            text="Limpar seleção",
            width=104,
            height=24,
            corner_radius=12,
            font=U.font(11),
            fg_color="transparent",
            hover_color=U.PILL_UTILITY_HOVER,
            text_color=U.TEXT_MUTED,
            command=self._reset_selection,
        )
        self.btn_reset_filters.pack(side="right")

        grid_row = ctk.CTkFrame(self.filter_card, fg_color="transparent")
        grid_row.pack(fill="x", padx=18, pady=(4, 16))
        grid_row.grid_columnconfigure(0, weight=1, uniform="cascade")
        grid_row.grid_columnconfigure(1, weight=0)
        grid_row.grid_columnconfigure(2, weight=1, uniform="cascade")
        grid_row.grid_columnconfigure(3, weight=0)
        grid_row.grid_columnconfigure(4, weight=1, uniform="cascade")

        # Coluna 1: Marca de Impressora
        col1 = ctk.CTkFrame(grid_row, fg_color="transparent")
        col1.grid(row=0, column=0, sticky="ew")
        ctk.CTkLabel(
            col1, text="1. Marca de Impressora", font=U.font(12, "bold"), text_color=U.TEXT_MUTED, anchor="w"
        ).pack(fill="x", pady=(0, 5))
        self.sel_printer_brand = U.CascadingPillSelect(
            col1,
            placeholder="Selecione a marca...",
            command=self._on_printer_brand_selected,
        )
        self.sel_printer_brand.pack(fill="x")

        ctk.CTkLabel(grid_row, text="›", font=U.font(20, "bold"), text_color=U.TEXT_DISABLED).grid(
            row=0, column=1, padx=10, pady=(20, 0)
        )

        # Coluna 2: Modelo de Impressora
        col2 = ctk.CTkFrame(grid_row, fg_color="transparent")
        col2.grid(row=0, column=2, sticky="ew")
        ctk.CTkLabel(
            col2, text="2. Modelo de Impressora", font=U.font(12, "bold"), text_color=U.TEXT_MUTED, anchor="w"
        ).pack(fill="x", pady=(0, 5))
        self.sel_printer_model = U.CascadingPillSelect(
            col2,
            placeholder="Escolha a marca antes...",
            state="disabled",
            command=self._on_printer_model_selected,
        )
        self.sel_printer_model.pack(fill="x")

        ctk.CTkLabel(grid_row, text="›", font=U.font(20, "bold"), text_color=U.TEXT_DISABLED).grid(
            row=0, column=3, padx=10, pady=(20, 0)
        )

        # Coluna 3: Marca de Tinta
        col3 = ctk.CTkFrame(grid_row, fg_color="transparent")
        col3.grid(row=0, column=4, sticky="ew")
        ctk.CTkLabel(
            col3, text="3. Marca de Tinta Sublimática", font=U.font(12, "bold"), text_color=U.TEXT_MUTED, anchor="w"
        ).pack(fill="x", pady=(0, 5))
        self.sel_ink_brand = U.CascadingPillSelect(
            col3,
            placeholder="Escolha o modelo antes...",
            state="disabled",
            command=self._on_ink_brand_selected,
        )
        self.sel_ink_brand.pack(fill="x")

        # --- Área Rolável de Resultados ---
        self.results_card = ctk.CTkFrame(
            self,
            fg_color=U.CARD_BG,
            corner_radius=U.RADIUS_CARD,
            border_width=1,
            border_color=U.CARD_BORDER,
        )
        self.results_card.pack(fill="both", expand=True, padx=28, pady=(6, 22))
        self.wallpaper.register(self.results_card, glass=(U.CARD_BG, U.GLASS_ALPHA))

        res_header = ctk.CTkFrame(self.results_card, fg_color="transparent")
        res_header.pack(fill="x", padx=18, pady=(12, 4))

        self.lbl_results_title = ctk.CTkLabel(
            res_header,
            text="Perfis de Cor Encontrados",
            font=U.font(14, "bold"),
            text_color=U.TEXT_TITLE,
            anchor="w",
        )
        self.lbl_results_title.pack(side="left")

        self.lbl_results_count = ctk.CTkLabel(
            res_header,
            text="",
            font=U.font(12),
            text_color=U.TEXT_MUTED,
            anchor="e",
        )
        self.lbl_results_count.pack(side="right")

        self.scroll_results = ctk.CTkScrollableFrame(
            self.results_card,
            fg_color="transparent",
            corner_radius=12,
            scrollbar_button_color=U.SECONDARY,
            scrollbar_button_hover_color=U.SECONDARY_HOVER,
        )
        self.scroll_results.pack(fill="both", expand=True, padx=12, pady=(2, 12))
        U.attach_smooth_scroll(self, self.scroll_results)

    # ------------------------------------------------------------------
    # Lógica de Seleção em Cascata (Marca Impressora > Modelo > Tinta)
    # ------------------------------------------------------------------
    def _summary_status_text(self) -> str:
        online_n = sum(1 for r in self._reports if r.status == "online")
        p_brands = len(self._index.get_printer_brands())
        models_n = self._index.count_models()
        if online_n > 0:
            return (
                f"✓ {online_n}/10 marcas varridas online  •  {self._index.total_entries} perfis mapeados "
                f"em {models_n} modelos ({p_brands} marcas de impressora)  •  Atualizado: {self._last_scan_str}"
            )
        return (
            f"Catálogo base carregado ({models_n} modelos de impressora)  •  "
            f"Clique em 'Varrer Internet Agora' para buscar atualizações ao vivo nas 10 marcas."
        )

    def _populate_printer_brands(self, preserve: bool = True):
        prev_pb = self.sel_printer_brand.get() if preserve else ""
        prev_pm = self.sel_printer_model.get() if preserve else ""
        prev_ib = self.sel_ink_brand.get() if preserve else ""

        p_brands = self._index.get_printer_brands()
        if prev_pb and prev_pb in p_brands:
            self.sel_printer_brand.configure_options(
                p_brands, selected=prev_pb, state="normal", placeholder="Selecione a marca..."
            )
            models = self._index.get_printer_models(prev_pb)
            if prev_pm and prev_pm in models:
                self.sel_printer_model.configure_options(
                    models, selected=prev_pm, state="normal", placeholder=f"Escolha o modelo ({len(models)})..."
                )
                inks = self._build_ink_options(prev_pb, prev_pm)
                sel_ink = prev_ib if prev_ib in inks else ""
                self.sel_ink_brand.configure_options(
                    inks, selected=sel_ink, state="normal", placeholder="Selecione a marca de tinta..."
                )
                self._render_results()
                return
            self._on_printer_brand_selected(prev_pb)
            return

        self.sel_printer_brand.configure_options(
            p_brands, selected="", state="normal", placeholder="Selecione a marca..."
        )
        self.sel_printer_model.configure_options(
            [], selected="", state="disabled", placeholder="Escolha a marca antes..."
        )
        self.sel_ink_brand.configure_options(
            [], selected="", state="disabled", placeholder="Escolha o modelo antes..."
        )
        self._render_results()

    def _reset_selection(self):
        self._populate_printer_brands(preserve=False)

    def _build_ink_options(self, printer_brand: str, printer_model: str) -> List[str]:
        inks = self._index.get_ink_brands(printer_brand, printer_model)
        if len(inks) > 1:
            return inks + [f"{self.ALL_BRANDS_Prefix} ({len(inks)})"]
        return inks

    def _on_printer_brand_selected(self, printer_brand: str):
        models = self._index.get_printer_models(printer_brand)
        self.sel_printer_model.configure_options(
            models,
            selected=models[0] if len(models) == 1 else "",
            state="normal",
            placeholder=f"Selecione o modelo ({len(models)} disponíveis)...",
        )
        if len(models) == 1:
            self._on_printer_model_selected(models[0])
        else:
            self.sel_ink_brand.configure_options(
                [], selected="", state="disabled", placeholder="Escolha o modelo antes..."
            )
            self._render_results()

    def _on_printer_model_selected(self, printer_model: str):
        printer_brand = self.sel_printer_brand.get()
        inks = self._build_ink_options(printer_brand, printer_model)
        raw_inks = self._index.get_ink_brands(printer_brand, printer_model)
        auto_sel = raw_inks[0] if len(raw_inks) == 1 else ""
        self.sel_ink_brand.configure_options(
            inks,
            selected=auto_sel,
            state="normal",
            placeholder=f"Selecione a tinta ({len(raw_inks)} marca{'s' if len(raw_inks) != 1 else ''})...",
        )
        self._render_results()

    def _on_ink_brand_selected(self, _ink_brand: str):
        self._render_results()

    # ------------------------------------------------------------------
    # Renderização dos Perfis Encontrados
    # ------------------------------------------------------------------
    def _render_results(self):
        for child in self.scroll_results.winfo_children():
            child.destroy()

        pb = self.sel_printer_brand.get()
        pm = self.sel_printer_model.get()
        ib = self.sel_ink_brand.get()

        if not pb:
            self.lbl_results_title.configure(text="Aguardando Seleção")
            self.lbl_results_count.configure(text="Passo 1 de 3")
            self._render_guidance(
                "1. Selecione a Marca de Impressora",
                "Comece escolhendo o fabricante da sua impressora acima (ex.: Epson, Sawgrass, Canon ou HP) "
                "para listar os modelos com perfis sublimáticos mapeados.",
            )
            return

        if not pm:
            models_n = len(self._index.get_printer_models(pb))
            self.lbl_results_title.configure(text=f"{pb}  ›  Escolha o Modelo")
            self.lbl_results_count.configure(text="Passo 2 de 3")
            self._render_guidance(
                f"2. Selecione o Modelo da Impressora {pb}",
                f"Encontramos {models_n} modelos da {pb} com perfis de cor. Clique no seletor central acima "
                f"(você pode digitar para filtrar, ex.: '3250' ou 'F170').",
            )
            return

        available_inks = self._index.get_ink_brands(pb, pm)
        if not ib:
            self.lbl_results_title.configure(text=f"{pb}  ›  {pm}  ›  Escolha a Tinta")
            self.lbl_results_count.configure(text="Passo 3 de 3")
            inks_list = ", ".join(available_inks)
            self._render_guidance(
                f"3. Selecione a Marca de Tinta ({len(available_inks)} encontrada{'s' if len(available_inks) != 1 else ''})",
                f"Para a {pb} {pm}, localizamos perfis nas seguintes marcas:\n{inks_list}\n\n"
                f"Escolha a marca de tinta no 3º seletor acima para ver os arquivos e links oficiais.",
            )
            return

        if ib.startswith(self.ALL_BRANDS_Prefix):
            entries: List[ProfileEntry] = []
            for k in available_inks:
                entries.extend(self._index.get_profiles(pb, pm, k))
            title_ink = f"Todas as marcas ({len(available_inks)})"
        else:
            entries = self._index.get_profiles(pb, pm, ib)
            title_ink = ib

        self.lbl_results_title.configure(text=f"{pb}  ›  {pm}  ›  {title_ink}")
        self.lbl_results_count.configure(
            text=f"{len(entries)} perfil{'s' if len(entries) != 1 else ''} localizado{'s' if len(entries) != 1 else ''}"
        )

        for entry in entries:
            self._create_profile_row(entry)

    def _render_guidance(self, heading: str, description: str):
        box = ctk.CTkFrame(
            self.scroll_results,
            fg_color=U.INNER_CARD_BG,
            corner_radius=14,
            border_width=1,
            border_color=U.INNER_CARD_BORDER,
        )
        box.pack(fill="x", padx=8, pady=18)

        ctk.CTkLabel(
            box, text=heading, font=U.font(15, "bold"), text_color=U.TEXT_TITLE, anchor="w"
        ).pack(fill="x", padx=20, pady=(18, 6))

        ctk.CTkLabel(
            box,
            text=description,
            font=U.font(13),
            text_color=U.TEXT_MUTED,
            anchor="w",
            justify="left",
            wraplength=780,
        ).pack(fill="x", padx=20, pady=(0, 18))

    def _badge_style_for(self, delivery_type: str):
        if delivery_type == "direct_icc":
            return "ARQUIVO .ICC / .ICM DIRETO", U.SUCCESS_BG, U.SUCCESS_TEXT
        if delivery_type == "direct_archive":
            return "PACOTE COMPACTADO DIRETO", U.SUCCESS_BG, U.SUCCESS_TEXT
        if delivery_type == "cloud_folder":
            return "PASTA GOOGLE DRIVE OFICIAL", U.BADGE_CLOUD_BG, U.BADGE_CLOUD_TEXT
        if delivery_type == "software_spm":
            return "GERENCIADOR OFICIAL (SPM)", U.BADGE_PORTAL_BG, U.BADGE_PORTAL_TEXT
        return "PORTAL OFICIAL DA MARCA", U.BADGE_PORTAL_BG, U.BADGE_PORTAL_TEXT

    def _create_profile_row(self, entry: ProfileEntry):
        row = ctk.CTkFrame(
            self.scroll_results,
            fg_color=U.INNER_CARD_BG,
            corner_radius=14,
            border_width=1,
            border_color=U.INNER_CARD_BORDER,
        )
        row.pack(fill="x", padx=6, pady=5)

        left = ctk.CTkFrame(row, fg_color="transparent")
        left.pack(side="left", fill="both", expand=True, padx=(16, 10), pady=12)

        top_line = ctk.CTkFrame(left, fg_color="transparent")
        top_line.pack(fill="x", pady=(0, 4))

        ctk.CTkLabel(
            top_line,
            text=f"{entry.ink_brand}",
            font=U.font(11, "bold"),
            fg_color=U.PILL_UTILITY,
            text_color=U.ACCENT,
            corner_radius=8,
            padx=8,
            pady=2,
        ).pack(side="left", padx=(0, 8))

        badge_txt, badge_bg, badge_fg = self._badge_style_for(entry.delivery_type)
        ctk.CTkLabel(
            top_line,
            text=badge_txt,
            font=U.font(10, "bold"),
            fg_color=badge_bg,
            text_color=badge_fg,
            corner_radius=8,
            padx=8,
            pady=2,
        ).pack(side="left")

        ctk.CTkLabel(
            left,
            text=entry.profile_name,
            font=U.font(14, "bold"),
            text_color=U.TEXT_TITLE,
            anchor="w",
        ).pack(fill="x")

        meta_text = f"Onde está: {entry.hosting_label}"
        if entry.details:
            meta_text += f"  •  {entry.details}"
        ctk.CTkLabel(
            left,
            text=meta_text,
            font=U.font(12),
            text_color=U.TEXT_MUTED,
            anchor="w",
            justify="left",
            wraplength=580,
        ).pack(fill="x", pady=(2, 0))

        # Botões de Ação à direita
        actions = ctk.CTkFrame(row, fg_color="transparent")
        actions.pack(side="right", padx=(6, 16), pady=12)

        if entry.delivery_type in ("direct_icc", "direct_archive"):
            btn_dl = ctk.CTkButton(
                actions,
                text="⬇  Baixar Perfil",
                width=142,
                height=34,
                corner_radius=U.RADIUS_PILL,
                font=U.font(12, "bold"),
                fg_color=U.ACCENT,
                hover_color=U.ACCENT_HOVER,
                text_color="#FFFFFF",
            )
            btn_dl.configure(command=lambda e=entry, b=btn_dl: self._handle_download(e, b))
            btn_dl.pack(side="left", padx=(0, 8))

            ctk.CTkButton(
                actions,
                text="Fonte Oficial ↗",
                width=118,
                height=34,
                corner_radius=U.RADIUS_PILL,
                font=U.font(12),
                fg_color=U.PILL_UTILITY,
                hover_color=U.PILL_UTILITY_HOVER,
                text_color=U.TEXT_ON_SECONDARY,
                command=lambda url=entry.source_page: webbrowser.open(url),
            ).pack(side="left")
        else:
            ctk.CTkButton(
                actions,
                text="🌐  Abrir Fonte Oficial",
                width=180,
                height=34,
                corner_radius=U.RADIUS_PILL,
                font=U.font(12, "bold"),
                fg_color=U.PILL_BUTTON,
                hover_color=U.PILL_BUTTON_HOVER,
                text_color="#FFFFFF",
                command=lambda url=entry.download_url: webbrowser.open(url),
            ).pack(side="left")

    # ------------------------------------------------------------------
    # Varredura ao Vivo & Download de Perfis
    # ------------------------------------------------------------------
    def start_internet_scan(self):
        if self._scanning:
            return
        self._scanning = True
        self.btn_scan.configure(state="disabled", text="⏳ Varrendo 10 marcas...")
        self.progress.set(0.05)
        self.lbl_status.configure(text="Conectando aos repositórios oficiais das 10 principais marcas...")

        def _on_progress(done: int, total: int, msg: str):
            frac = max(0.08, min(1.0, done / max(total, 1)))
            self.after(0, lambda: self._update_scan_ui(frac, f"[{done}/{total}] {msg}"))

        def _worker():
            try:
                entries, reports = scan_all_brands(progress_cb=_on_progress)
                self.after(0, lambda: self._finish_scan(entries, reports))
            except Exception as exc:
                self.after(0, lambda: self._fail_scan(str(exc)))

        threading.Thread(target=_worker, daemon=True).start()

    def _update_scan_ui(self, frac: float, text: str):
        if not self.winfo_exists():
            return
        self.progress.set(frac)
        self.lbl_status.configure(text=text)

    def _finish_scan(self, entries: List[ProfileEntry], reports: List[BrandScanReport]):
        self._scanning = False
        self._entries = entries
        self._reports = reports
        self._last_scan_str = reports[0].scanned_at if reports else "Agora"
        self._index = CatalogIndex(entries)

        self.progress.set(1.0)
        self.btn_scan.configure(state="normal", text="🔄  Varrer Internet Agora")
        self.lbl_status.configure(text=self._summary_status_text())
        self._populate_printer_brands(preserve=True)

    def _fail_scan(self, err_msg: str):
        self._scanning = False
        self.progress.set(1.0)
        self.btn_scan.configure(state="normal", text="🔄  Varrer Internet Agora")
        self.lbl_status.configure(text=f"Aviso na varredura: {err_msg} (mantendo catálogo em cache)")

    def _handle_download(self, entry: ProfileEntry, btn: ctk.CTkButton):
        btn.configure(state="disabled", text="⏳ Baixando...")

        def _worker():
            try:
                ok, msg, saved_paths = download_profile_file(entry)
                self.after(0, lambda: self._after_download(entry, btn, ok, msg, saved_paths))
            except Exception as exc:
                self.after(0, lambda: self._after_download(entry, btn, False, f"Erro ao baixar: {exc}", []))

        threading.Thread(target=_worker, daemon=True).start()

    def _after_download(self, entry: ProfileEntry, btn: ctk.CTkButton, ok: bool, msg: str, saved_paths: List[str]):
        if not self.winfo_exists():
            return
        if ok and saved_paths:
            first_file = saved_paths[0]
            btn.configure(
                state="normal",
                text="📂 Mostrar Arquivo",
                fg_color=U.SUCCESS_BG,
                hover_color="#1A3D30",
                text_color=U.SUCCESS_TEXT,
                command=lambda p=first_file: self._reveal_file(p),
            )
            self.lbl_status.configure(text=f"✓ {msg}")
        else:
            btn.configure(state="normal", text="🌐 Abrir no Navegador", command=lambda: webbrowser.open(entry.download_url))
            webbrowser.open(entry.download_url)
            self.lbl_status.configure(text=msg)

    def _reveal_file(self, file_path: str):
        if os.name == "nt" and os.path.exists(file_path):
            subprocess.Popen(["explorer", "/select,", os.path.normpath(file_path)])
        elif os.path.exists(os.path.dirname(file_path)):
            os.startfile(os.path.dirname(file_path))

    def open_downloads_folder(self):
        os.makedirs(DOWNLOADS_DIR, exist_ok=True)
        if os.name == "nt":
            os.startfile(DOWNLOADS_DIR)
        else:
            webbrowser.open(f"file://{DOWNLOADS_DIR}")

    def open_windows_color_folder(self):
        color_dir = os.path.join(os.environ.get("WINDIR", r"C:\Windows"), "System32", "spool", "drivers", "color")
        if os.path.isdir(color_dir) and os.name == "nt":
            os.startfile(color_dir)
        else:
            messagebox.showinfo("Pasta de Perfis ICC", f"Caminho padrão no Windows:\n{color_dir}")

    # ------------------------------------------------------------------
    # Modal: Mapa de Onde Estão as 10 Principais Marcas
    # ------------------------------------------------------------------
    def show_brands_radar_modal(self):
        if hasattr(self, "_radar_win") and self._radar_win is not None and self._radar_win.winfo_exists():
            self._radar_win.lift()
            self._radar_win.focus_force()
            return

        win = ctk.CTkToplevel(self)
        win.withdraw()
        win.title("Onde estão as 10 Marcas de Tinta Sublimática")
        win.overrideredirect(True)
        win.configure(fg_color=U.BG_MODAL_KEY)
        try:
            win.attributes("-transparentcolor", U.BG_MODAL_KEY)
        except Exception:
            pass

        scale = U.window_scaling(self)
        mw, mh = 760, 560
        px_w, px_h = int(mw * scale), int(mh * scale)
        x = self.winfo_rootx() + (self.winfo_width() - px_w) // 2
        y = self.winfo_rooty() + (self.winfo_height() - px_h) // 2
        win.geometry(f"{mw}x{mh}+{max(20, x)}+{max(20, y)}")
        win.transient(self)
        self._radar_win = win

        shell = ctk.CTkFrame(
            win,
            fg_color=U.MODAL_BG,
            corner_radius=U.RADIUS_MODAL,
            border_width=1,
            border_color=U.MODAL_BORDER,
            bg_color=U.BG_MODAL_KEY,
        )
        shell.pack(fill="both", expand=True)

        header = ctk.CTkFrame(shell, fg_color="transparent")
        header.pack(fill="x", padx=22, pady=(18, 8))

        lbl_h = ctk.CTkLabel(
            header,
            text="Mapa das 10 Principais Marcas de Tinta Sublimática",
            font=U.font(16, "bold"),
            text_color=U.TEXT_TITLE,
        )
        lbl_h.pack(side="left")

        btn_close = U.CircleIconButton(
            header,
            text="✕",
            width=28,
            height=28,
            corner_radius=14,
            font=U.font(12, "bold"),
            fg_color=U.PILL_UTILITY,
            hover_color=U.PILL_UTILITY_HOVER,
            text_color=U.TEXT_MUTED,
            command=win.destroy,
        )
        btn_close.pack(side="right")

        drag = {}
        def _start_drag(e):
            drag["dx"], drag["dy"] = e.x_root - win.winfo_x(), e.y_root - win.winfo_y()
        def _do_drag(e):
            win.geometry(f"+{e.x_root - drag['dx']}+{e.y_root - drag['dy']}")
        for w in (header, lbl_h):
            w.bind("<ButtonPress-1>", _start_drag)
            w.bind("<B1-Motion>", _do_drag)

        ctk.CTkLabel(
            shell,
            text="Veja exatamente onde cada fabricante hospeda seus perfis ICC/ICM na internet e o status da última varredura:",
            font=U.font(12),
            text_color=U.TEXT_MUTED,
            anchor="w",
        ).pack(fill="x", padx=22, pady=(0, 8))

        body = ctk.CTkScrollableFrame(
            shell,
            fg_color=U.MODAL_CARD_BG,
            corner_radius=14,
            border_width=1,
            border_color=U.MODAL_CARD_BORDER,
            scrollbar_button_color=U.SECONDARY,
            scrollbar_button_hover_color=U.SECONDARY_HOVER,
        )
        body.pack(fill="both", expand=True, padx=22, pady=(0, 18))
        U.attach_smooth_scroll(win, body)

        rep_by_name = {r.ink_brand: r for r in self._reports}
        for idx, meta in enumerate(TOP_10_INK_BRANDS, start=1):
            rep = rep_by_name.get(meta["name"])
            item = ctk.CTkFrame(
                body,
                fg_color=U.INNER_CARD_BG,
                corner_radius=12,
                border_width=1,
                border_color=U.INNER_CARD_BORDER,
            )
            item.pack(fill="x", padx=8, pady=5)

            row_top = ctk.CTkFrame(item, fg_color="transparent")
            row_top.pack(fill="x", padx=14, pady=(10, 2))

            ctk.CTkLabel(
                row_top,
                text=f"{idx}. {meta['name']}  ({meta['origin']})",
                font=U.font(14, "bold"),
                text_color=U.TEXT_TITLE,
            ).pack(side="left")

            is_online = rep and rep.status == "online"
            status_lbl = (
                f"ONLINE • {rep.printers_count} modelos" if is_online
                else f"CATÁLOGO • {rep.printers_count if rep else 0} modelos"
            )
            ctk.CTkLabel(
                row_top,
                text=status_lbl,
                font=U.font(10, "bold"),
                fg_color=U.SUCCESS_BG if is_online else U.PILL_UTILITY,
                text_color=U.SUCCESS_TEXT if is_online else U.TEXT_MUTED,
                corner_radius=8,
                padx=8,
                pady=2,
            ).pack(side="right")

            target_url = rep.discovered_repo_url if rep else meta["official_url"]
            ctk.CTkLabel(
                item,
                text=f"Hospedagem: {meta['hosting']}",
                font=U.font(12, "bold"),
                text_color=U.TEXT_BODY,
                anchor="w",
            ).pack(fill="x", padx=14)

            ctk.CTkLabel(
                item,
                text=meta["notes"],
                font=U.font(11),
                text_color=U.TEXT_MUTED,
                anchor="w",
                justify="left",
                wraplength=650,
            ).pack(fill="x", padx=14, pady=(2, 4))

            link_row = ctk.CTkFrame(item, fg_color="transparent")
            link_row.pack(fill="x", padx=14, pady=(0, 10))

            short_url = target_url if len(target_url) <= 68 else target_url[:65] + "..."
            lbl_url = ctk.CTkLabel(
                link_row,
                text=f"🔗 {short_url}",
                font=U.font(11),
                text_color=U.ACCENT,
                cursor="hand2",
                anchor="w",
            )
            lbl_url.pack(side="left")
            lbl_url.bind("<Button-1>", lambda _e, u=target_url: webbrowser.open(u))

            if rep and rep.message:
                ctk.CTkLabel(
                    link_row,
                    text=rep.message,
                    font=U.font(11),
                    text_color=U.TEXT_DISABLED,
                ).pack(side="right")

        win.bind("<Escape>", lambda _e: win.destroy())
        win.deiconify()
        win.lift()
        win.attributes("-topmost", True)
        win.focus_force()
        win.after(200, lambda: win.attributes("-topmost", False) if win.winfo_exists() else None)


def main():
    app = ICCFinderApp()
    app.mainloop()


if __name__ == "__main__":
    main()

