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
SKY_TOP = '#87CEEB'
SKY_BOTTOM = '#B0E0F6'
GRASS_LIGHT = '#4CAF50'
GRASS_DARK = '#388E3C'
DIRT_COLOR = '#6D4C2E'
FENCE_COLOR = '#DEB887'
FENCE_POST = '#A0825A'
SUN_COLOR = '#FFD700'
SUN_RAY = '#FFF176'
FLOWER_COLORS = ['#FF6F61', '#FF85A1', '#FFD700', '#E040FB', '#FF7043']
LEAF_COLOR = '#2E7D32'
LABEL_BG = '#E8F5E9'
CANVAS_W = 620
CANVAS_H = 760

SPARKLE_COLORS = ['#FFD700', '#FF6F00', '#FF1744', '#E040FB', '#00E5FF']


class WhackAMoleGame:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title('Whack-A-Mole  \U0001F33B')
        self.root.geometry(f'{CANVAS_W}x{CANVAS_H}')
        self.root.resizable(False, False)
        self.root.configure(cursor='none')

        self.score = 0
        self.misses = 0
        self.current_mole_index: int | None = None
        self.mole_visible = False
        self.game_over = False

        # -- background canvas --
        self.canvas = tk.Canvas(self.root, width=CANVAS_W, height=CANVAS_H,
                                highlightthickness=0, cursor='none')
        self.canvas.pack(fill='both', expand=True)

        self.cloud_items: list[list[int]] = []
        self.sun_ray_ids: list[int] = []
        self._draw_garden_background()

        self.hole_image = self._create_hole_image()
        self.mole_image = self._create_mole_image()

        # Hammer cursor – uses a transparent Toplevel so it floats above all widgets
        self.hammer_img = self._create_hammer_image(False)
        self.hammer_smash_img = self._create_hammer_image(True)
        self.hammer_smashing = False

        self.hammer_overlay = tk.Toplevel(self.root)
        self.hammer_overlay.overrideredirect(True)
        self.hammer_overlay.attributes('-topmost', True)
        self.hammer_overlay.attributes('-transparentcolor', '#010101')
        self.hammer_overlay.config(bg='#010101')
        self.hammer_overlay.geometry('32x32+0+0')
        self.hammer_overlay.lift()
        self.hammer_label = tk.Label(self.hammer_overlay, image=self.hammer_img,
                                     bg='#010101', borderwidth=0)
        self.hammer_label.pack()

        # -- instructions --
        instructions = (
            '\U0001F33F  Click the mole to whack it!  '
            'Misses don\'t score. Reach 10 hits to win!  \U0001F33F'
        )
        self.instructions_label = tk.Label(
            self.root, text=instructions, font=('Arial', 11, 'italic'),
            wraplength=560, justify='center', bg=LABEL_BG, fg='#2E7D32',
            relief='groove', padx=8, pady=4, cursor='none',
        )
        self.canvas.create_window(CANVAS_W // 2, 30, window=self.instructions_label)

        # -- scoreboard --
        self.scoreboard_frame = tk.Frame(self.root, bg=LABEL_BG, relief='ridge', bd=2, cursor='none')
        self.score_label = tk.Label(self.scoreboard_frame, text='\U0001F3AF Score: 0',
                                    font=('Arial', 14, 'bold'), bg=LABEL_BG, fg='#1B5E20', cursor='none')
        self.score_label.pack(side=tk.LEFT, padx=10)
        self.miss_label = tk.Label(self.scoreboard_frame, text='\u274C Misses: 0',
                                    font=('Arial', 14, 'bold'), bg=LABEL_BG, fg='#B71C1C', cursor='none')
        self.miss_label.pack(side=tk.LEFT, padx=10)
        self.canvas.create_window(CANVAS_W // 2, 70, window=self.scoreboard_frame)

        # -- grid of holes --
        self.grid_frame = tk.Frame(self.root, bg=GRASS_LIGHT, cursor='none')
        self.holes: list[tk.Button] = []
        for r in range(GRID_ROWS):
            for c in range(GRID_COLS):
                index = r * GRID_COLS + c
                btn = tk.Button(
                    self.grid_frame, text='', image=self.hole_image,
                    compound='center', borderwidth=0, highlightthickness=0,
                    bg=GRASS_LIGHT, activebackground=GRASS_DARK,
                    command=lambda i=index: self.handle_click(i),
                    cursor='none',
                )
                btn.grid(row=r, column=c, padx=12, pady=12)
                self.holes.append(btn)
        self.canvas.create_window(CANVAS_W // 2, 380, window=self.grid_frame)

        # -- status --
        self.status_label = tk.Label(
            self.root, text='\U0001F439 Click the mole!',
            font=('Arial', 13, 'bold'), bg=LABEL_BG, fg='#33691E',
            relief='groove', padx=8, pady=4, cursor='none',
        )
        self.canvas.create_window(CANVAS_W // 2, 660, window=self.status_label)

        # Bind mouse for custom hammer cursor
        self.root.bind('<Motion>', self._move_hammer)
        self.root.bind('<Button-1>', self._hammer_down)
        self.root.bind('<ButtonRelease-1>', self._hammer_up)

        # Start background animations
        self._animate_clouds()
        self._rotate_sun_rays()

        self.root.after(MOLE_INTERVAL_MS, self.spawn_mole)

    # ------------------------------------------------------------------ #
    #  Hammer cursor                                                       #
    # ------------------------------------------------------------------ #

    def _create_hammer_image(self, smash: bool) -> tk.PhotoImage:
        s = 32
        img = tk.PhotoImage(width=s, height=s)
        handle = '#8B4513'
        handle_hi = '#A0522D'
        head = '#757575'
        head_hi = '#9E9E9E'
        head_dk = '#424242'

        if not smash:
            # Handle diagonal lower-right
            for i in range(16):
                bx, by = 8 + i, 16 + i
                for d in range(3):
                    px, py = bx + d, by
                    if 0 <= px < s and 0 <= py < s:
                        img.put(handle if d < 2 else handle_hi, (px, py))
            # Head block at top-left
            for x in range(2, 20):
                for y in range(10, 20):
                    c = head_hi if y < 13 else head_dk if y > 17 else head
                    img.put(c, (x, y))
            for x in range(3, 19):
                img.put('#BDBDBD', (x, 11))
        else:
            # Handle vertical
            for i in range(16):
                bx, by = 14, 16 + i
                if by < s:
                    for d in range(3):
                        img.put(handle if d < 2 else handle_hi, (bx + d, by))
            # Head block horizontal on top
            for x in range(4, 28):
                for y in range(6, 18):
                    if x < s:
                        c = head_hi if y < 9 else head_dk if y > 15 else head
                        img.put(c, (x, y))
            for x in range(5, 27):
                if x < s:
                    img.put('#BDBDBD', (x, 7))
        return img

    def _move_hammer(self, event: 'tk.Event[tk.Misc]') -> None:
        img = self.hammer_smash_img if self.hammer_smashing else self.hammer_img
        self.hammer_label.config(image=img)
        self.hammer_overlay.geometry(f'32x32+{event.x_root}+{event.y_root}')
        self.hammer_overlay.lift()

    def _hammer_down(self, event: 'tk.Event[tk.Misc]') -> None:
        self.hammer_smashing = True
        self._move_hammer(event)
        cx = event.x_root - self.root.winfo_rootx()
        cy = event.y_root - self.root.winfo_rooty()
        self._impact_ring(cx, cy)

    def _hammer_up(self, event: 'tk.Event[tk.Misc]') -> None:
        self.hammer_smashing = False
        self._move_hammer(event)

    def _impact_ring(self, cx: int, cy: int) -> None:
        oid = self.canvas.create_oval(cx - 4, cy - 4, cx + 4, cy + 4,
                                       outline='#FFD700', width=3)
        self._grow_ring(oid, cx, cy, 4, 0)

    def _grow_ring(self, oid: int, cx: int, cy: int, r: int, step: int) -> None:
        if step >= 7:
            self.canvas.delete(oid)
            return
        r += 5
        self.canvas.coords(oid, cx - r, cy - r, cx + r, cy + r)
        shades = ['#FFD700', '#FFC107', '#FFB300', '#FFA000', '#FF8F00', '#FF6F00', '#E65100']
        self.canvas.itemconfigure(oid, outline=shades[step], width=max(1, 3 - step // 2))
        self.root.after(35, self._grow_ring, oid, cx, cy, r, step + 1)

    # ------------------------------------------------------------------ #
    #  Garden background                                                   #
    # ------------------------------------------------------------------ #

    def _draw_garden_background(self) -> None:
        c = self.canvas
        for y in range(0, CANVAS_H // 2, 2):
            ratio = y / (CANVAS_H // 2)
            r = int(135 + (176 - 135) * ratio)
            g = int(206 + (224 - 206) * ratio)
            b = int(235 + (246 - 235) * ratio)
            c.create_line(0, y, CANVAS_W, y, fill=f'#{r:02x}{g:02x}{b:02x}')
        c.create_rectangle(0, CANVAS_H // 2 - 20, CANVAS_W, CANVAS_H,
                            fill=GRASS_LIGHT, outline='')
        for y in range(CANVAS_H // 2, CANVAS_H, 18):
            c.create_rectangle(0, y, CANVAS_W, y + 8, fill=GRASS_DARK, outline='')
        sx, sy, sr = 80, 70, 40
        for i in range(12):
            angle = math.radians(i * 30)
            x1 = sx + math.cos(angle) * (sr + 8)
            y1 = sy + math.sin(angle) * (sr + 8)
            x2 = sx + math.cos(angle) * (sr + 25)
            y2 = sy + math.sin(angle) * (sr + 25)
            ray_id = c.create_line(x1, y1, x2, y2, fill=SUN_RAY, width=4)
            self.sun_ray_ids.append(ray_id)
        c.create_oval(sx - sr, sy - sr, sx + sr, sy + sr,
                        fill=SUN_COLOR, outline='#FFC107', width=2)
        self.sun_cx, self.sun_cy, self.sun_r = sx, sy, sr
        fence_y = CANVAS_H // 2 - 50
        c.create_rectangle(0, fence_y, CANVAS_W, fence_y + 8, fill=FENCE_COLOR, outline=FENCE_POST)
        c.create_rectangle(0, fence_y + 30, CANVAS_W, fence_y + 38, fill=FENCE_COLOR, outline=FENCE_POST)
        for x in range(20, CANVAS_W, 50):
            c.create_rectangle(x, fence_y - 15, x + 10, fence_y + 50,
                                fill=FENCE_COLOR, outline=FENCE_POST)
            c.create_polygon(x, fence_y - 15, x + 5, fence_y - 25, x + 10, fence_y - 15,
                            fill=FENCE_COLOR, outline=FENCE_POST)
        random.seed(42)
        for _ in range(18):
            fx = random.randint(10, CANVAS_W - 10)
            fy = random.randint(CANVAS_H // 2 + 10, CANVAS_H - 30)
            self._draw_flower(c, fx, fy)
        random.seed()
        for cx_, cy_ in [(200, 40), (420, 55), (540, 25)]:
            cloud = self._make_cloud(c, cx_, cy_)
            self.cloud_items.append(cloud)

    def _draw_flower(self, c: tk.Canvas, x: int, y: int) -> None:
        petal = random.choice(FLOWER_COLORS)
        ps = random.randint(5, 8)
        c.create_line(x, y, x, y + 18, fill=LEAF_COLOR, width=2)
        for angle in range(0, 360, 72):
            dx = math.cos(math.radians(angle)) * ps
            dy = math.sin(math.radians(angle)) * ps
            c.create_oval(x + dx - 3, y + dy - 3, x + dx + 3, y + dy + 3,
                            fill=petal, outline='')
        c.create_oval(x - 3, y - 3, x + 3, y + 3, fill='#FFF9C4', outline='')

    def _make_cloud(self, c: tk.Canvas, x: int, y: int) -> list[int]:
        ids = []
        for dx, dy, r in [(-15, 0, 18), (0, -8, 22), (18, 0, 18), (8, 5, 16)]:
            oid = c.create_oval(x + dx - r, y + dy - r, x + dx + r, y + dy + r,
                                fill='white', outline='#E0E0E0')
            ids.append(oid)
        return ids

    # ------------------------------------------------------------------ #
    #  Background animations                                               #
    # ------------------------------------------------------------------ #

    def _animate_clouds(self) -> None:
        for cloud in self.cloud_items:
            for oid in cloud:
                self.canvas.move(oid, 0.3, 0)
                coords = self.canvas.coords(oid)
                if coords and coords[0] > CANVAS_W + 40:
                    w = coords[2] - coords[0]
                    h = coords[3] - coords[1]
                    self.canvas.coords(oid, -40, coords[1], -40 + w, coords[1] + h)
        self.root.after(50, self._animate_clouds)

    def _rotate_sun_rays(self) -> None:
        if not hasattr(self, '_sun_angle'):
            self._sun_angle = 0
        self._sun_angle += 1
        sx, sy, sr = self.sun_cx, self.sun_cy, self.sun_r
        for i, ray_id in enumerate(self.sun_ray_ids):
            angle = math.radians(i * 30 + self._sun_angle)
            x1 = sx + math.cos(angle) * (sr + 8)
            y1 = sy + math.sin(angle) * (sr + 8)
            x2 = sx + math.cos(angle) * (sr + 25)
            y2 = sy + math.sin(angle) * (sr + 25)
            self.canvas.coords(ray_id, x1, y1, x2, y2)
        self.root.after(80, self._rotate_sun_rays)

    # ------------------------------------------------------------------ #
    #  Hit / miss / game-over effects                                      #
    # ------------------------------------------------------------------ #

    def _sparkle_burst(self, cx: int, cy: int) -> None:
        for _ in range(8):
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(2, 5)
            color = random.choice(SPARKLE_COLORS)
            size = random.randint(3, 6)
            oid = self.canvas.create_oval(cx - size, cy - size, cx + size, cy + size,
                                           fill=color, outline='')
            dx = math.cos(angle) * speed
            dy = math.sin(angle) * speed
            self._move_sparkle(oid, dx, dy, 0)

    def _move_sparkle(self, oid: int, dx: float, dy: float, step: int) -> None:
        if step >= 10:
            self.canvas.delete(oid)
            return
        self.canvas.move(oid, dx, dy)
        coords = self.canvas.coords(oid)
        if coords:
            cx = (coords[0] + coords[2]) / 2
            cy = (coords[1] + coords[3]) / 2
            new_r = max(1, (coords[2] - coords[0]) / 2 - 0.3)
            self.canvas.coords(oid, cx - new_r, cy - new_r, cx + new_r, cy + new_r)
        self.root.after(40, self._move_sparkle, oid, dx, dy - 0.3, step + 1)

    def _float_text(self, text: str, cx: int, cy: int, color: str) -> None:
        tid = self.canvas.create_text(cx, cy, text=text, font=('Arial', 18, 'bold'),
                                       fill=color)
        self._rise_text(tid, 0)

    def _rise_text(self, tid: int, step: int) -> None:
        if step >= 15:
            self.canvas.delete(tid)
            return
        self.canvas.move(tid, 0, -2)
        fade = ['#FFD700', '#FFD700', '#FFD700', '#FFC107', '#FFC107',
                '#FFB300', '#FFA000', '#FF8F00', '#FF6F00', '#E65100',
                '#BF360C', '#8D6E63', '#A1887F', '#BCAAA4', '#D7CCC8']
        if step < len(fade):
            self.canvas.itemconfigure(tid, fill=fade[step])
        self.root.after(50, self._rise_text, tid, step + 1)

    def _miss_flash(self, btn: tk.Button) -> None:
        original_bg = btn.cget('bg')
        btn.config(bg='#EF5350')
        self.root.after(120, lambda: btn.config(bg=original_bg))

    def _score_pulse(self) -> None:
        self.score_label.config(font=('Arial', 18, 'bold'), fg='#FFD700')
        self.root.after(150, lambda: self.score_label.config(font=('Arial', 14, 'bold'), fg='#1B5E20'))

    def _screen_shake(self) -> None:
        x = self.root.winfo_x()
        y = self.root.winfo_y()
        offsets = [(5, 0), (-5, 0), (0, 5), (0, -5), (3, 0), (-3, 0), (0, 0)]
        for i, (dx, dy) in enumerate(offsets):
            self.root.after(i * 30, lambda nx=x + dx, ny=y + dy: self.root.geometry(f'+{nx}+{ny}'))

    def _confetti(self) -> None:
        colors = ['#FF1744', '#FFD700', '#2979FF', '#00E676', '#E040FB', '#FF6D00']
        for _ in range(30):
            x = random.randint(50, CANVAS_W - 50)
            y = random.randint(-20, 0)
            color = random.choice(colors)
            size = random.randint(4, 8)
            oid = self.canvas.create_rectangle(x, y, x + size, y + size * 2,
                                                fill=color, outline='')
            dx = random.uniform(-2, 2)
            dy = random.uniform(2, 5)
            self._fall_confetti(oid, dx, dy, 0)

    def _fall_confetti(self, oid: int, dx: float, dy: float, step: int) -> None:
        if step >= 60:
            self.canvas.delete(oid)
            return
        self.canvas.move(oid, dx + math.sin(step * 0.3) * 1.5, dy)
        self.root.after(40, self._fall_confetti, oid, dx, dy, step + 1)

    # ------------------------------------------------------------------ #
    #  Game logic                                                          #
    # ------------------------------------------------------------------ #

    def handle_click(self, index: int) -> None:
        if self.game_over:
            return
        if self.mole_visible and self.current_mole_index == index:
            self.score += 1
            self.update_score_label()
            self.status_label.config(text='\U0001F389 Hit!')
            btn = self.holes[index]
            bx = btn.winfo_rootx() - self.root.winfo_rootx() + btn.winfo_width() // 2
            by = btn.winfo_rooty() - self.root.winfo_rooty() + btn.winfo_height() // 2
            self._sparkle_burst(bx, by)
            self._float_text('+1', bx, by - 20, '#FFD700')
            self._score_pulse()
            self._screen_shake()
            self.hide_mole()
            if self.score >= TARGET_SCORE:
                self.end_game()
        else:
            self.misses += 1
            self.status_label.config(text='\U0001F4A8 Miss!')
            self.update_miss_label()
            self._miss_flash(self.holes[index])

    def update_score_label(self) -> None:
        self.score_label.config(text=f'\U0001F3AF Score: {self.score}')

    def update_miss_label(self) -> None:
        self.miss_label.config(text=f'\u274C Misses: {self.misses}')

    def spawn_mole(self) -> None:
        if self.game_over:
            return
        if self.mole_visible:
            self.hide_mole()
        new_index = random.randrange(GRID_ROWS * GRID_COLS)
        self.current_mole_index = new_index
        self.mole_visible = True
        btn = self.holes[new_index]
        btn.config(bg=GRASS_DARK, image=self.mole_image, compound='center')
        self._bounce_mole(btn, 0)
        self.root.after(MOLE_VISIBLE_MS, self.on_mole_timeout)
        self.root.after(MOLE_INTERVAL_MS, self.spawn_mole)

    def _bounce_mole(self, btn: tk.Button, step: int) -> None:
        if step >= 6:
            btn.grid_configure(pady=12)
            return
        offsets = [-6, -10, -6, 0, -3, 0]
        btn.grid_configure(pady=(12 + offsets[step], 12 - offsets[step]))
        self.root.after(35, self._bounce_mole, btn, step + 1)

    def hide_mole(self) -> None:
        if self.current_mole_index is not None:
            self.holes[self.current_mole_index].config(bg=GRASS_LIGHT, image=self.hole_image, compound='center')
            self.holes[self.current_mole_index].grid_configure(pady=12)
        self.current_mole_index = None
        self.mole_visible = False

    def on_mole_timeout(self) -> None:
        if self.game_over:
            return
        if self.mole_visible:
            self.misses += 1
            self.status_label.config(text='\u23F0 Too slow!')
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
                        img.put('#5D4037', (x, y))
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
                        img.put('#5D4037', (x, y))
                    else:
                        img.put(DIRT_COLOR, (x, y))
        mole_r = r - 10
        mole_color = '#795548'
        for x in range(size):
            for y in range(size):
                if (x - cx) ** 2 + (y - cy) ** 2 <= mole_r * mole_r:
                    img.put(mole_color, (x, y))
        for ex in [(cx - 12, cy - 8), (cx + 6, cy - 8)]:
            for x in range(ex[0], ex[0] + 10):
                for y in range(ex[1], ex[1] + 10):
                    img.put('white', (x, y))
            for x in range(ex[0] + 3, ex[0] + 7):
                for y in range(ex[1] + 3, ex[1] + 7):
                    img.put('#000000', (x, y))
        for x in range(cx - 4, cx + 4):
            for y in range(cy + 2, cy + 8):
                img.put('#FF8A80', (x, y))
        for x in range(cx - 10, cx + 10):
            for y in range(cy + 10, cy + 14):
                img.put('#4E342E', (x, y))
        return img

    def end_game(self) -> None:
        self.game_over = True
        self.hide_mole()
        for btn in self.holes:
            btn.config(state=tk.DISABLED)
        self.status_label.config(text='\U0001F3C6 Game over!')
        self._confetti()
        self.root.after(1500, lambda: messagebox.showinfo(
            'Game over', f'You reached {self.score} points with {self.misses} misses.'))


def main() -> None:
    root = tk.Tk()
    WhackAMoleGame(root)
    root.mainloop()


if __name__ == '__main__':
    main()
