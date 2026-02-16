import math
import random
import tkinter as tk
from tkinter import messagebox


GRID_ROWS = 4
GRID_COLS = 4
MOLE_VISIBLE_MS = 800
MOLE_INTERVAL_MS = 1000
TARGET_SCORE = 10

# Garden palette
SKY_TOP = "#87CEEB"
SKY_BOTTOM = "#B0E0F6"
GRASS_LIGHT = "#4CAF50"
GRASS_DARK = "#388E3C"
DIRT_COLOR = "#6D4C2E"
FENCE_COLOR = "#DEB887"
FENCE_POST = "#A0825A"
SUN_COLOR = "#FFD700"
SUN_RAY = "#FFF176"
FLOWER_COLORS = ["#FF6F61", "#FF85A1", "#FFD700", "#E040FB", "#FF7043"]
LEAF_COLOR = "#2E7D32"
LABEL_BG = "#E8F5E9"
CANVAS_W = 620
CANVAS_H = 760


class WhackAMoleGame:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("Whack-A-Mole  \U0001F33B")
        self.root.geometry(f"{CANVAS_W}x{CANVAS_H}")
        self.root.resizable(False, False)

        try:
            self.root.configure(cursor="@hammer.cur")
        except tk.TclError:
            self.root.configure(cursor="target")

        self.score = 0
        self.misses = 0
        self.current_mole_index: int | None = None
        self.mole_visible = False
        self.game_over = False

        # -- background canvas --
        self.canvas = tk.Canvas(self.root, width=CANVAS_W, height=CANVAS_H,
                                highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)
        self._draw_garden_background()

        self.hole_image = self._create_hole_image()
        self.mole_image = self._create_mole_image()

        # -- instructions --
        instructions = (
            "\U0001F33F  Click the mole to whack it!  "
            "Misses don't score. Reach 10 hits to win!  \U0001F33F"
        )
        self.instructions_label = tk.Label(
            self.root, text=instructions, font=("Arial", 11, "italic"),
            wraplength=560, justify="center", bg=LABEL_BG, fg="#2E7D32",
            relief="groove", padx=8, pady=4,
        )
        self.canvas.create_window(CANVAS_W // 2, 30, window=self.instructions_label)

        # -- scoreboard --
        self.scoreboard_frame = tk.Frame(self.root, bg=LABEL_BG, relief="ridge", bd=2)
        self.score_label = tk.Label(self.scoreboard_frame, text="\U0001F3AF Score: 0",
                                    font=("Arial", 14, "bold"), bg=LABEL_BG, fg="#1B5E20")
        self.score_label.pack(side=tk.LEFT, padx=10)
        self.miss_label = tk.Label(self.scoreboard_frame, text="\u274C Misses: 0",
                                    font=("Arial", 14, "bold"), bg=LABEL_BG, fg="#B71C1C")
        self.miss_label.pack(side=tk.LEFT, padx=10)
        self.canvas.create_window(CANVAS_W // 2, 70, window=self.scoreboard_frame)

        # -- grid of holes --
        self.grid_frame = tk.Frame(self.root, bg=GRASS_LIGHT)
        self.holes: list[tk.Button] = []
        for r in range(GRID_ROWS):
            for c in range(GRID_COLS):
                index = r * GRID_COLS + c
                btn = tk.Button(
                    self.grid_frame, text="", image=self.hole_image,
                    compound="center", borderwidth=0, highlightthickness=0,
                    bg=GRASS_LIGHT, activebackground=GRASS_DARK,
                    command=lambda i=index: self.handle_click(i),
                )
                btn.grid(row=r, column=c, padx=12, pady=12)
                self.holes.append(btn)
        self.canvas.create_window(CANVAS_W // 2, 380, window=self.grid_frame)

        # -- status --
        self.status_label = tk.Label(
            self.root, text="\U0001F439 Click the mole!",
            font=("Arial", 13, "bold"), bg=LABEL_BG, fg="#33691E",
            relief="groove", padx=8, pady=4,
        )
        self.canvas.create_window(CANVAS_W // 2, 660, window=self.status_label)

        self.root.after(MOLE_INTERVAL_MS, self.spawn_mole)

    # ------------------------------------------------------------------ #
    #  Garden drawing helpers                                              #
    # ------------------------------------------------------------------ #

    def _draw_garden_background(self) -> None:
        """Paint sky gradient, grass, sun, fence, and flowers."""
        c = self.canvas

        # sky gradient
        for y in range(0, CANVAS_H // 2, 2):
            ratio = y / (CANVAS_H // 2)
            r = int(135 + (176 - 135) * ratio)
            g = int(206 + (224 - 206) * ratio)
            b = int(235 + (246 - 235) * ratio)
            color = f"#{r:02x}{g:02x}{b:02x}"
            c.create_line(0, y, CANVAS_W, y, fill=color)

        # grass
        c.create_rectangle(0, CANVAS_H // 2 - 20, CANVAS_W, CANVAS_H,
                            fill=GRASS_LIGHT, outline="")
        # grass stripes
        for y in range(CANVAS_H // 2, CANVAS_H, 18):
            c.create_rectangle(0, y, CANVAS_W, y + 8, fill=GRASS_DARK, outline="")

        # sun
        sx, sy, sr = 80, 70, 40
        for i in range(12):
            angle = math.radians(i * 30)
            x1 = sx + math.cos(angle) * (sr + 8)
            y1 = sy + math.sin(angle) * (sr + 8)
            x2 = sx + math.cos(angle) * (sr + 25)
            y2 = sy + math.sin(angle) * (sr + 25)
            c.create_line(x1, y1, x2, y2, fill=SUN_RAY, width=4)
        c.create_oval(sx - sr, sy - sr, sx + sr, sy + sr,
                        fill=SUN_COLOR, outline="#FFC107", width=2)

        # fence
        fence_y = CANVAS_H // 2 - 50
        c.create_rectangle(0, fence_y, CANVAS_W, fence_y + 8, fill=FENCE_COLOR, outline=FENCE_POST)
        c.create_rectangle(0, fence_y + 30, CANVAS_W, fence_y + 38, fill=FENCE_COLOR, outline=FENCE_POST)
        for x in range(20, CANVAS_W, 50):
            c.create_rectangle(x, fence_y - 15, x + 10, fence_y + 50,
                                fill=FENCE_COLOR, outline=FENCE_POST)
            c.create_polygon(x, fence_y - 15, x + 5, fence_y - 25, x + 10, fence_y - 15,
                            fill=FENCE_COLOR, outline=FENCE_POST)

        # scattered flowers
        random.seed(42)
        for _ in range(18):
            fx = random.randint(10, CANVAS_W - 10)
            fy = random.randint(CANVAS_H // 2 + 10, CANVAS_H - 30)
            self._draw_flower(c, fx, fy)
        random.seed()

        # small clouds
        for cx_, cy_ in [(200, 40), (420, 55), (540, 25)]:
            self._draw_cloud(c, cx_, cy_)

    def _draw_flower(self, c: tk.Canvas, x: int, y: int) -> None:
        petal = random.choice(FLOWER_COLORS)
        ps = random.randint(5, 8)
        c.create_line(x, y, x, y + 18, fill=LEAF_COLOR, width=2)
        for angle in range(0, 360, 72):
            dx = math.cos(math.radians(angle)) * ps
            dy = math.sin(math.radians(angle)) * ps
            c.create_oval(x + dx - 3, y + dy - 3, x + dx + 3, y + dy + 3,
                            fill=petal, outline="")
        c.create_oval(x - 3, y - 3, x + 3, y + 3, fill="#FFF9C4", outline="")

    def _draw_cloud(self, c: tk.Canvas, x: int, y: int) -> None:
        for dx, dy, r in [(-15, 0, 18), (0, -8, 22), (18, 0, 18), (8, 5, 16)]:
            c.create_oval(x + dx - r, y + dy - r, x + dx + r, y + dy + r,
                            fill="white", outline="#E0E0E0")

    # ------------------------------------------------------------------ #
    #  Game logic                                                          #
    # ------------------------------------------------------------------ #

    def handle_click(self, index: int) -> None:
        if self.game_over:
            return

        if self.mole_visible and self.current_mole_index == index:
            self.score += 1
            self.update_score_label()
            self.status_label.config(text="\U0001F389 Hit!")
            self.hide_mole()
            if self.score >= TARGET_SCORE:
                self.end_game()
        else:
            self.misses += 1
            self.status_label.config(text="\U0001F4A8 Miss!")
            self.update_miss_label()

    def update_score_label(self) -> None:
        self.score_label.config(text=f"\U0001F3AF Score: {self.score}")

    def update_miss_label(self) -> None:
        self.miss_label.config(text=f"\u274C Misses: {self.misses}")

    def spawn_mole(self) -> None:
        if self.game_over:
            return

        if self.mole_visible:
            self.hide_mole()

        new_index = random.randrange(GRID_ROWS * GRID_COLS)
        self.current_mole_index = new_index
        self.mole_visible = True

        btn = self.holes[new_index]
        btn.config(bg=GRASS_DARK, image=self.mole_image, compound="center")

        self.root.after(MOLE_VISIBLE_MS, self.on_mole_timeout)
        self.root.after(MOLE_INTERVAL_MS, self.spawn_mole)

    def hide_mole(self) -> None:
        if self.current_mole_index is not None:
            self.holes[self.current_mole_index].config(bg=GRASS_LIGHT, image=self.hole_image, compound="center")
        self.current_mole_index = None
        self.mole_visible = False

    def on_mole_timeout(self) -> None:
        if self.game_over:
            return
        if self.mole_visible:
            self.misses += 1
            self.status_label.config(text="\u23F0 Too slow!")
            self.update_miss_label()
            self.hide_mole()

    # ------------------------------------------------------------------ #
    #  Pixel-art images                                                    #
    # ------------------------------------------------------------------ #

    def _create_hole_image(self) -> tk.PhotoImage:
        size = 100
        img = tk.PhotoImage(width=size, height=size)
        img.put(GRASS_LIGHT, to=(0, 0, size, size))
        cx, cy, r = size // 2, size // 2, size // 2 - 6
        for x in range(size):
            for y in range(size):
                dist_sq = (x - cx) ** 2 + (y - cy) ** 2
                if dist_sq <= r * r:
                    if dist_sq >= (r - 4) ** 2:
                        img.put("#5D4037", (x, y))
                    else:
                        img.put(DIRT_COLOR, (x, y))
        return img

    def _create_mole_image(self) -> tk.PhotoImage:
        size = 100
        img = tk.PhotoImage(width=size, height=size)
        img.put(GRASS_LIGHT, to=(0, 0, size, size))
        cx, cy, r = size // 2, size // 2, size // 2 - 6
        for x in range(size):
            for y in range(size):
                dist_sq = (x - cx) ** 2 + (y - cy) ** 2
                if dist_sq <= r * r:
                    if dist_sq >= (r - 4) ** 2:
                        img.put("#5D4037", (x, y))
                    else:
                        img.put(DIRT_COLOR, (x, y))
        mole_r = r - 10
        mole_color = "#795548"
        for x in range(size):
            for y in range(size):
                if (x - cx) ** 2 + (y - cy) ** 2 <= mole_r * mole_r:
                    img.put(mole_color, (x, y))
        for ex in [(cx - 12, cy - 8), (cx + 6, cy - 8)]:
            for x in range(ex[0], ex[0] + 10):
                for y in range(ex[1], ex[1] + 10):
                    img.put("white", (x, y))
            for x in range(ex[0] + 3, ex[0] + 7):
                for y in range(ex[1] + 3, ex[1] + 7):
                    img.put("#000000", (x, y))
        for x in range(cx - 4, cx + 4):
            for y in range(cy + 2, cy + 8):
                img.put("#FF8A80", (x, y))
        for x in range(cx - 10, cx + 10):
            for y in range(cy + 10, cy + 14):
                img.put("#4E342E", (x, y))
        return img

    def end_game(self) -> None:
        self.game_over = True
        self.hide_mole()
        for btn in self.holes:
            btn.config(state=tk.DISABLED)
        self.status_label.config(text="\U0001F3C6 Game over!")
        messagebox.showinfo("Game over", f"You reached {self.score} points with {self.misses} misses.")


def main() -> None:
    root = tk.Tk()
    WhackAMoleGame(root)
    root.mainloop()


if __name__ == "__main__":
    main()
