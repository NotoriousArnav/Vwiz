from manim import *
import numpy as np

# Color palette
BG = "#1C1C1C"
PRIMARY = "#58C4DD"
SECONDARY = "#83C167"
ACCENT = "#FFFF00"

class ManimScene(Scene):
    def construct(self):
        self.camera.background_color = BG

        # ---------- Segment 1 ----------
        title1 = Text("Matrix", font_size=48, color=PRIMARY).to_edge(UP, buff=0.5)
        grid = Matrix(
            [[1, 2, 3],
             [4, 5, 6],
             [7, 8, 9]],
            h_buff=0.8,
            v_buff=0.8,
        ).scale(0.8).next_to(title1, DOWN, buff=0.5)
        seg1 = VGroup(title1, grid)
        self.play(FadeIn(seg1, shift=UP), run_time=1.5)
        self.wait(2.5)

        # ---------- Segment 2 ----------
        self.play(FadeOut(seg1), run_time=1)
        axes2 = Axes(
            x_range=[-4, 4, 1],
            y_range=[-4, 4, 1],
            axis_config={"color": SECONDARY},
        ).add_coordinates()
        square2 = Square(side_length=2, color=PRIMARY).move_to(ORIGIN)
        label2 = Text(
            "Linear Transformation", font_size=36, color=ACCENT
        ).to_edge(UP, buff=0.5)
        seg2 = VGroup(axes2, square2, label2)
        self.play(Create(axes2), run_time=1)
        self.play(FadeIn(square2, shift=UP), run_time=1)
        self.play(FadeIn(label2, shift=DOWN), run_time=1)
        self.wait(4)

        # ---------- Segment 3 ----------
        self.play(FadeOut(seg2), run_time=1)
        axes3 = Axes(
            x_range=[-4, 4, 1],
            y_range=[-4, 4, 1],
            axis_config={"color": SECONDARY},
        )
        square3 = Square(side_length=2, color=PRIMARY).move_to(ORIGIN)
        title3 = Text(
            "Rotation by 90°", font_size=36, color=ACCENT
        ).to_edge(UP, buff=0.5)
        seg3 = VGroup(axes3, square3, title3)
        self.play(Create(axes3), run_time=1)
        self.play(FadeIn(square3, shift=UP), run_time=1)
        self.play(FadeIn(title3, shift=DOWN), run_time=1)
        self.wait(0.5)
        self.play(Rotate(square3, angle=PI / 2, about_point=ORIGIN), run_time=2)
        self.wait(2)

        # ---------- Segment 4 ----------
        self.play(FadeOut(seg3), run_time=1)
        axes4 = Axes(
            x_range=[-5, 5, 1],
            y_range=[-4, 4, 1],
            axis_config={"color": SECONDARY},
        )
        square4 = Square(side_length=2, color=PRIMARY).move_to(ORIGIN)
        title4 = Text(
            "Horizontal Stretch", font_size=36, color=ACCENT
        ).to_edge(UP, buff=0.5)
        seg4 = VGroup(axes4, square4, title4)
        self.play(Create(axes4), run_time=1)
        self.play(FadeIn(square4, shift=UP), run_time=1)
        self.play(FadeIn(title4, shift=DOWN), run_time=1)
        self.wait(0.5)
        stretch = np.array([[2, 0], [0, 1]])  # stretch x‑direction by 2
        self.play(square4.animate.apply_matrix(stretch), run_time=2)
        self.wait(2)

        # ---------- Segment 5 ----------
        self.play(FadeOut(seg4), run_time=1)
        axes5 = Axes(
            x_range=[-6, 6, 1],
            y_range=[-6, 6, 1],
            axis_config={"color": SECONDARY},
        )
        square5 = Square(side_length=2, color=PRIMARY).move_to(ORIGIN)
        title5 = Text(
            "Combined: Rotation + Stretch", font_size=36, color=ACCENT
        ).to_edge(UP, buff=0.5)
        seg5 = VGroup(axes5, square5, title5)
        self.play(Create(axes5), run_time=1)
        self.play(FadeIn(square5, shift=UP), run_time=1)
        self.play(FadeIn(title5, shift=DOWN), run_time=1)
        self.wait(0.5)
        rotation = np.array([[0, -1], [1, 0]])  # 90° rotation
        combined = stretch @ rotation
        self.play(square5.animate.apply_matrix(combined), run_time=2.5)
        self.wait(2)

        # ---------- Segment 6 ----------
        self.play(FadeOut(seg5), run_time=1)
        title6 = Text(
            "Matrix as a Spreadsheet", font_size=36, color=ACCENT
        ).to_edge(UP, buff=0.5)
        table6 = Matrix(
            [[r"p_{1}", r"p_{2}", r"p_{3}"],
             [r"q_{1}", r"q_{2}", r"q_{3}"]],
            h_buff=0.8,
            v_buff=0.8,
        ).scale(0.8).next_to(title6, DOWN, buff=0.5)
        seg6 = VGroup(title6, table6)
        self.play(FadeIn(seg6, shift=UP), run_time=1.5)
        self.wait(4)

        # ---------- Segment 7 ----------
        self.play(FadeOut(seg6), run_time=1)
        title7 = Text(
            "Production Data (3×2)", font_size=36, color=ACCENT
        ).to_edge(UP, buff=0.5)
        prod7 = Matrix(
            [[12, 15],
             [9, 14],
             [20, 18]],
            h_buff=0.8,
            v_buff=0.8,
        ).scale(0.8).next_to(title7, DOWN, buff=0.5)
        seg7 = VGroup(title7, prod7)
        self.play(FadeIn(seg7, shift=UP), run_time=1.5)
        self.wait(2)

        # ---------- Segment 8 ----------
        self.play(FadeOut(seg7), run_time=1)
        title8 = Text(
            "Row Totals", font_size=36, color=ACCENT
        ).to_edge(UP, buff=0.5)
        rows8 = Matrix(
            [[12, 15, 27],
             [9, 14, 23],
             [20, 18, 38]],
            h_buff=0.8,
            v_buff=0.8,
        ).scale(0.8).next_to(title8, DOWN, buff=0.5)
        seg8 = VGroup(title8, rows8)
        self.play(FadeIn(seg8, shift=UP), run_time=1.5)
        self.wait(2)