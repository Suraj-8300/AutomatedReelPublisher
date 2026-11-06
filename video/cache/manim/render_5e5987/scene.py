from manim import *

config.frame_width = 6
config.frame_height = 10.67

class AutoReelScene(Scene):
    def construct(self):
        self.camera.background_color = "#0a0a0f"

        title = Text("How a jet engine works", font_size=42, color=WHITE, weight=BOLD)
        title.set_width(5.5)
        title.move_to(UP * 3)

        line = Line(LEFT * 2.5, RIGHT * 2.5, color=BLUE, stroke_width=3)
        line.next_to(title, DOWN, buff=0.3)

        body = Text(
            "Exploring the science\nand mechanics behind\nthis fascinating topic.",
            font_size=32, color=LIGHT_GRAY, line_spacing=1.4
        )
        body.set_width(5.0)
        body.move_to(ORIGIN)

        footer = Text("AutoReelStudio", font_size=24, color=BLUE_D)
        footer.move_to(DOWN * 4)

        self.play(FadeIn(title, shift=DOWN * 0.3), run_time=1.2)
        self.play(Create(line), run_time=0.8)
        self.play(Write(body), run_time=2.5)
        self.wait(1)
        self.play(FadeIn(footer), run_time=0.8)
        self.wait(2)
        self.play(FadeOut(VGroup(title, line, body, footer)), run_time=1.2)
