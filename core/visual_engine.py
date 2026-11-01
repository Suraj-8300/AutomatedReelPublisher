import math
import random
from pathlib import Path
from typing import Dict, Any, List, Optional
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from .config import WIDTH, HEIGHT, FPS, FONTS, PALETTES, CACHE_DIR

class VisualEngine:
    """
    Renders high-retention 9:16 vertical motion cards, diagrams,
    and Ken Burns scene sequences optimized for CPU rendering on laptop hardware.
    """

    @staticmethod
    def _get_font(size: int, bold: bool = True):
        font_path = FONTS["bold"] if bold else FONTS["regular"]
        try:
            return ImageFont.truetype(font_path, size)
        except Exception:
            return ImageFont.load_default()

    @staticmethod
    def create_scene_frame(
        scene_info: Dict[str, Any],
        palette_key: str = "cyber_blue",
        output_file: Optional[Path] = None
    ) -> str:
        """
        Renders a single ultra-crisp 1080x1920 frame for a scene.
        """
        palette = PALETTES.get(palette_key, PALETTES["cyber_blue"])
        img = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 255))
        draw = ImageDraw.Draw(img)

        # 1. Subtle Radial / Linear Dark Gradient Background
        bg_top = palette["bg_top"]
        bg_bot = palette["bg_bottom"]
        for y in range(HEIGHT):
            ratio = y / HEIGHT
            r = int(bg_top[0] * (1 - ratio) + bg_bot[0] * ratio)
            g = int(bg_top[1] * (1 - ratio) + bg_bot[1] * ratio)
            b = int(bg_top[2] * (1 - ratio) + bg_bot[2] * ratio)
            draw.line([(0, y), (WIDTH, y)], fill=(r, g, b, 255))

        # 2. Tech Grid Lines & Ambient Star Dust
        random.seed(hash(scene_info.get("title", "")) % 10000)
        # Background Grid
        grid_alpha = 25
        grid_step = 120
        for gx in range(0, WIDTH, grid_step):
            draw.line([(gx, 0), (gx, HEIGHT)], fill=(255, 255, 255, grid_alpha), width=1)
        for gy in range(0, HEIGHT, grid_step):
            draw.line([(0, gy), (WIDTH, gy)], fill=(255, 255, 255, grid_alpha), width=1)

        # Ambient Particle Stars
        for _ in range(60):
            px = random.randint(30, WIDTH - 30)
            py = random.randint(50, HEIGHT - 100)
            p_radius = random.randint(1, 3)
            p_alpha = random.randint(50, 180)
            draw.ellipse([px - p_radius, py - p_radius, px + p_radius, py + p_radius], fill=(255, 255, 255, p_alpha))

        # 3. Top Branding Pill: "🔬 IS IT PLAUSIBLE?"
        badge_y = 130
        badge_w = 460
        badge_h = 64
        badge_x0 = (WIDTH - badge_w) // 2
        badge_y0 = badge_y
        badge_x1 = badge_x0 + badge_w
        badge_y1 = badge_y0 + badge_h

        # Rounded badge background
        draw.rounded_rectangle([badge_x0, badge_y0, badge_x1, badge_y1], radius=32, fill=palette["badge_bg"], outline=palette["border"], width=2)
        font_badge = VisualEngine._get_font(28, bold=True)
        draw.text((WIDTH // 2, badge_y0 + badge_h // 2), "🔬  IS IT PLAUSIBLE?", font=font_badge, fill=palette["accent"], anchor="mm")

        # 4. Category & Scene Title Header
        scene_title = scene_info.get("title", "ANALYSIS").upper()
        font_title = VisualEngine._get_font(46, bold=True)
        draw.text((WIDTH // 2, 250), scene_title, font=font_title, fill=(255, 255, 255, 240), anchor="mm")

        # 5. Central Hero Visual Card (Y: 330 to 1180)
        card_x0, card_y0 = 70, 330
        card_x1, card_y1 = WIDTH - 70, 1180
        draw.rounded_rectangle([card_x0, card_y0, card_x1, card_y1], radius=36, fill=palette["card_bg"], outline=palette["border"], width=3)

        # Thematic Diagram inside Card
        graphic_type = scene_info.get("graphic_type", "default")
        card_center = ((card_x0 + card_x1) // 2, (card_y0 + card_y1) // 2)
        VisualEngine._draw_thematic_graphic(draw, card_center, graphic_type, palette, scene_info)

        # 6. Secondary Accent Glow under card
        glow_bar_y = 1220
        draw.line([(WIDTH // 2 - 120, glow_bar_y), (WIDTH // 2 + 120, glow_bar_y)], fill=palette["accent"], width=3)

        # 7. Subtitle Safe Zone Indicator (Y: 1300 - 1550) - purely aesthetic subtle corner bracket
        draw.line([(90, 1320), (90, 1340)], fill=(255, 255, 255, 60), width=2)
        draw.line([(90, 1320), (110, 1320)], fill=(255, 255, 255, 60), width=2)
        draw.line([(WIDTH - 90, 1320), (WIDTH - 90, 1340)], fill=(255, 255, 255, 60), width=2)
        draw.line([(WIDTH - 90, 1320), (WIDTH - 110, 1320)], fill=(255, 255, 255, 60), width=2)

        # 8. Save Frame
        if output_file is None:
            output_file = CACHE_DIR / f"frame_{uuid.uuid4().hex[:6]}.png"
        img.save(str(output_file), "PNG")
        return str(output_file)

    @staticmethod
    def _draw_thematic_graphic(draw: ImageDraw.ImageDraw, center: tuple, graphic_type: str, palette: dict, info: dict):
        cx, cy = center
        accent = palette["accent"]
        highlight = palette["highlight"]

        # Universal outer analysis ring
        draw.arc([cx - 240, cy - 240, cx + 240, cy + 240], start=0, end=360, fill=(255, 255, 255, 40), width=2)
        draw.arc([cx - 210, cy - 210, cx + 210, cy + 210], start=-30, end=210, fill=accent, width=4)
        draw.arc([cx - 180, cy - 180, cx + 180, cy + 180], start=120, end=300, fill=highlight, width=3)

        # Specialized graphics
        if "verdict" in info.get("title", "").lower() or graphic_type == "verdict":
            # Massive High-Impact Verdict Badge
            verdict_text = info.get("text", "PLAUSIBLE").upper()
            is_busted = "bust" in verdict_text.lower() or "0%" in verdict_text
            stamp_color = "#FF3366" if is_busted else "#00FFA3"
            draw.rounded_rectangle([cx - 320, cy - 100, cx + 320, cy + 100], radius=24, outline=stamp_color, width=6)
            font_v = VisualEngine._get_font(52, bold=True)
            draw.text((cx, cy - 15), verdict_text[:18], font=font_v, fill=stamp_color, anchor="mm")
            font_sub = VisualEngine._get_font(26, bold=True)
            draw.text((cx, cy + 50), "OFFICIAL SCIENTIFIC VERDICT", font=font_sub, fill=(255, 255, 255, 200), anchor="mm")
            return

        if graphic_type == "elevator":
            # Elevator Shaft & Physics Vectors
            draw.rectangle([cx - 120, cy - 160, cx + 120, cy + 160], outline=accent, width=4)
            # Falling cable
            draw.line([(cx, cy - 220), (cx, cy - 160)], fill="#FF3366", width=4)
            # Downward velocity vectors
            for vy in [-40, 0, 40]:
                draw.line([(cx - 60, cy + vy), (cx - 60, cy + vy + 40)], fill=highlight, width=4)
                draw.polygon([(cx - 66, cy + vy + 40), (cx - 54, cy + vy + 40), (cx - 60, cy + vy + 55)], fill=highlight)
            font_metric = VisualEngine._get_font(32, bold=True)
            draw.text((cx + 30, cy - 20), "80 MPH ↓", font=font_metric, fill="#FF3366")
            draw.text((cx + 30, cy + 30), "+5 MPH ↑", font=font_metric, fill="#00FFA3")

        elif graphic_type == "ocean_shark":
            # Sonar Waves & Molecule Dispersal
            for r in [60, 110, 160, 210]:
                draw.arc([cx - r, cy - r, cx + r, cy + r], start=180, end=360, fill=accent, width=3)
            draw.ellipse([cx - 20, cy - 20, cx + 20, cy + 20], fill="#FF3366")
            font_metric = VisualEngine._get_font(30, bold=True)
            draw.text((cx, cy + 80), "1 PART PER BILLION", font=font_metric, fill=highlight, anchor="mm")
            draw.text((cx, cy + 130), "CURRENT DEPENDENT", font=VisualEngine._get_font(24), fill=(255, 255, 255, 180), anchor="mm")

        elif graphic_type == "cloud_scale":
            # Cloud & Scale Schematic
            draw.ellipse([cx - 140, cy - 100, cx + 20, cy + 20], fill=(255, 255, 255, 160))
            draw.ellipse([cx - 60, cy - 140, cx + 100, cy - 10], fill=(255, 255, 255, 200))
            draw.ellipse([cx - 10, cy - 90, cx + 150, cy + 30], fill=(255, 255, 255, 170))
            font_metric = VisualEngine._get_font(36, bold=True)
            draw.text((cx, cy + 90), "500,000 KG", font=font_metric, fill=highlight, anchor="mm")
            draw.text((cx, cy + 140), "≈ 100 ELEPHANTS", font=VisualEngine._get_font(28, bold=True), fill=accent, anchor="mm")

        elif graphic_type == "time_relativity":
            # Relativistic Velocity Clocks
            draw.arc([cx - 100, cy - 100, cx + 100, cy + 100], start=0, end=360, fill=accent, width=5)
            draw.line([(cx, cy), (cx, cy - 70)], fill=highlight, width=4)
            draw.line([(cx, cy), (cx + 50, cy + 20)], fill=accent, width=4)
            font_metric = VisualEngine._get_font(34, bold=True)
            draw.text((cx, cy + 120), "17,500 MPH", font=font_metric, fill=highlight, anchor="mm")
            draw.text((cx, cy + 165), "-0.005s TIME DILATION", font=VisualEngine._get_font(26, bold=True), fill=accent, anchor="mm")

        else:
            # High-Tech Cyber Target / Orbit System
            draw.line([(cx - 160, cy), (cx + 160, cy)], fill=(255, 255, 255, 70), width=2)
            draw.line([(cx, cy - 160), (cx, cy + 160)], fill=(255, 255, 255, 70), width=2)
            draw.ellipse([cx - 30, cy - 30, cx + 30, cy + 30], fill=accent)
            for angle in [45, 135, 225, 315]:
                rad = math.radians(angle)
                px = int(cx + 140 * math.cos(rad))
                py = int(cy + 140 * math.sin(rad))
                draw.ellipse([px - 8, py - 8, px + 8, py + 8], fill=highlight)
            font_metric = VisualEngine._get_font(28, bold=True)
            draw.text((cx, cy + 130), "DATA ANALYSIS ACTIVE", font=font_metric, fill=highlight, anchor="mm")
