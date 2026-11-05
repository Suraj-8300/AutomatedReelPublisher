import math
import random
import uuid
import subprocess
from pathlib import Path
from typing import Dict, Any, List, Optional
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from .config import WIDTH, HEIGHT, FPS, FONTS, PALETTES, CACHE_DIR

class VisualEngine:
    """
    Instagram-Native Visual & Animation Engine.
    Generates full-screen 1080x1920 9:16 vertical visual scenes, animated cartoon skits,
    motion comic frames, and cinematic camera movements without artificial borders,
    floating boxes, or top title panels.
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
        genre: str = "science",
        theme: str = "cyber_blue",
        output_file: Optional[Path] = None
    ) -> str:
        """
        Renders a full-screen, cinematic 1080x1920 visual frame tailored to the genre.
        Pure full-screen art with NO top badges, NO artificial borders, NO floating boxes.
        """
        if output_file is None:
            output_file = CACHE_DIR / f"frame_{uuid.uuid4().hex[:8]}.png"

        palette = PALETTES.get(theme, PALETTES["cyber_blue"])
        img = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 255))
        draw = ImageDraw.Draw(img)

        # 1. Full-screen dynamic atmospheric background
        bg_top = palette["bg_top"]
        bg_bot = palette["bg_bottom"]

        for y in range(HEIGHT):
            ratio = y / HEIGHT
            r = int(bg_top[0] * (1 - ratio) + bg_bot[0] * ratio)
            g = int(bg_top[1] * (1 - ratio) + bg_bot[1] * ratio)
            b = int(bg_top[2] * (1 - ratio) + bg_bot[2] * ratio)
            draw.line([(0, y), (WIDTH, y)], fill=(r, g, b, 255))

        # 2. Genre-specific native visual motifs (Full-screen composition)
        rng = random.Random(hash(scene_info.get("text", "reel")) % 10000)

        if genre in ["science", "mysteries"]:
            # Cosmic dust & deep atmospheric nebula particles
            for _ in range(120):
                px = rng.randint(0, WIDTH)
                py = rng.randint(0, HEIGHT)
                rad = rng.randint(1, 4)
                alpha = rng.randint(40, 220)
                draw.ellipse([px - rad, py - rad, px + rad, py + rad], fill=(255, 255, 255, alpha))

            # Subtle orbital rings
            cx, cy = WIDTH // 2, HEIGHT // 2 - 80
            accent_hex = palette["accent"]
            for r in [220, 380, 520]:
                draw.arc([cx - r, cy - r, cx + r, cy + r], start=0, end=360, fill=(255, 255, 255, 25), width=2)
            draw.arc([cx - 300, cy - 300, cx + 300, cy + 300], start=45, end=225, fill=accent_hex, width=3)

        elif genre == "animation":
            # 2D Cartoon / Motion Comic Skit Visuals
            cx, cy = WIDTH // 2, HEIGHT // 2 - 100
            # Draw cartoon character
            VisualEngine._draw_cartoon_character(draw, (cx, cy), rng, palette)

        elif genre == "comedy" or genre == "meme":
            # Dynamic vibrant energy bursts
            cx, cy = WIDTH // 2, HEIGHT // 2 - 100
            # Radial comic speed lines
            for angle in range(0, 360, 15):
                rad = math.radians(angle)
                x1 = int(cx + 350 * math.cos(rad))
                y1 = int(cy + 350 * math.sin(rad))
                x2 = int(cx + 900 * math.cos(rad))
                y2 = int(cy + 900 * math.sin(rad))
                draw.line([(x1, y1), (x2, y2)], fill=(255, 255, 255, 30), width=3)

        elif genre == "cinematic":
            # High-contrast anamorphic lens flare & cinematic atmosphere
            flare_y = HEIGHT // 2 - 120
            # Horizontal anamorphic glow lines
            draw.line([(0, flare_y), (WIDTH, flare_y)], fill=palette["accent"], width=2)
            draw.line([(WIDTH // 2 - 300, flare_y - 1), (WIDTH // 2 + 300, flare_y - 1)], fill=(255, 255, 255, 180), width=3)
            # Subtle vertical vignette
            for y in range(0, 240):
                alpha = int((1 - (y / 240)) * 160)
                draw.line([(0, y), (WIDTH, y)], fill=(0, 0, 0, alpha))
            for y in range(HEIGHT - 240, HEIGHT):
                alpha = int(((y - (HEIGHT - 240)) / 240) * 160)
                draw.line([(0, y), (WIDTH, y)], fill=(0, 0, 0, alpha))

        else: # Informative / Emotional
            # Elegant minimalist ambient waves
            for i in range(5):
                y_offset = (HEIGHT // 3) + i * 160
                points = []
                for x in range(0, WIDTH + 40, 40):
                    y_sin = y_offset + int(math.sin((x / 180.0) + i) * 60)
                    points.append((x, y_sin))
                draw.line(points, fill=(255, 255, 255, 35), width=2)

        img.save(str(output_file), "PNG")
        return str(output_file)

    @staticmethod
    def _draw_cartoon_character(draw: ImageDraw.ImageDraw, center: tuple, rng: random.Random, palette: dict):
        """Draws an expressive 2D cartoon character for animation skits."""
        cx, cy = center
        accent = palette["accent"]
        highlight = palette["highlight"]

        # Character Head
        head_rad = 180
        draw.ellipse([cx - head_rad, cy - head_rad, cx + head_rad, cy + head_rad], fill=(255, 220, 180, 255), outline=(30, 30, 30, 255), width=8)

        # Big expressive cartoon eyes
        eye_y = cy - 40
        eye_spacing = 65
        # Left eye
        draw.ellipse([cx - eye_spacing - 45, eye_y - 50, cx - eye_spacing + 45, eye_y + 50], fill=(255, 255, 255, 255), outline=(20, 20, 20), width=6)
        draw.ellipse([cx - eye_spacing - 15, eye_y - 25, cx - eye_spacing + 25, eye_y + 25], fill=(30, 30, 30, 255))
        draw.ellipse([cx - eye_spacing, eye_y - 18, cx - eye_spacing + 12, eye_y - 6], fill=(255, 255, 255, 255)) # Pupil sparkle

        # Right eye
        draw.ellipse([cx + eye_spacing - 45, eye_y - 50, cx + eye_spacing + 45, eye_y + 50], fill=(255, 255, 255, 255), outline=(20, 20, 20), width=6)
        draw.ellipse([cx + eye_spacing - 25, eye_y - 25, cx + eye_spacing + 15, eye_y + 25], fill=(30, 30, 30, 255))
        draw.ellipse([cx + eye_spacing - 10, eye_y - 18, cx + eye_spacing + 2, eye_y - 6], fill=(255, 255, 255, 255)) # Pupil sparkle

        # Eyebrows
        draw.arc([cx - eye_spacing - 45, eye_y - 95, cx - eye_spacing + 45, eye_y - 55], start=200, end=340, fill=(30, 30, 30), width=8)
        draw.arc([cx + eye_spacing - 45, eye_y - 95, cx + eye_spacing + 45, eye_y - 55], start=200, end=340, fill=(30, 30, 30), width=8)

        # Expressive Smile / Open Mouth
        mouth_y = cy + 60
        draw.chord([cx - 70, mouth_y - 20, cx + 70, mouth_y + 70], start=0, end=180, fill=(220, 50, 50, 255), outline=(30, 30, 30), width=6)
        # Tongue
        draw.ellipse([cx - 30, mouth_y + 25, cx + 30, mouth_y + 65], fill=(255, 130, 130, 255))

    @staticmethod
    def render_motion_scene_clip(
        frame_path: str,
        duration: float,
        output_clip: Path,
        motion_type: str = "zoom_in"
    ) -> str:
        """
        Renders a static 1080x1920 frame into a dynamic vertical 9:16 motion clip
        using GPU/CPU Ken Burns camera pan & zoom.
        """
        fps = FPS
        total_frames = int(duration * fps)

        # Zoompan filter: gentle 1.0 to 1.12 zoom or pan
        if motion_type == "zoom_in":
            vf = f"zoompan=z='min(zoom+0.0008,1.15)':d={total_frames}:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s={WIDTH}x{HEIGHT}:fps={fps}"
        elif motion_type == "zoom_out":
            vf = f"zoompan=z='if(lte(zoom,1.0),1.15,max(1.0,zoom-0.0008))':d={total_frames}:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s={WIDTH}x{HEIGHT}:fps={fps}"
        else: # pan
            vf = f"zoompan=z=1.08:x='if(lte(on,-1),(it/{duration})*(iw-iw/zoom),x)':y='ih/2-(ih/zoom/2)':d={total_frames}:s={WIDTH}x{HEIGHT}:fps={fps}"

        cmd = [
            "ffmpeg", "-y",
            "-loop", "1",
            "-i", str(frame_path),
            "-vf", vf,
            "-t", f"{duration:.2f}",
            "-c:v", "libx264",
            "-preset", "ultrafast",
            "-pix_fmt", "yuv420p",
            str(output_clip)
        ]
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        return str(output_clip)
