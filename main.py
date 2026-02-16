import random
import tkinter as tk
from tkinter import messagebox


GRID_ROWS = 4
GRID_COLS = 4
MOLE_VISIBLE_MS = 800
MOLE_INTERVAL_MS = 1000
TARGET_SCORE = 10


class WhackAMoleGame:
	def __init__(self, root: tk.Tk) -> None:
		self.root = root
		self.root.title("Whack-A-Mole")
		self.root.geometry("800x900")

		try:
			self.root.configure(cursor="@hammer.cur")
		except tk.TclError:
			self.root.configure(cursor="target")

		self.score = 0
		self.misses = 0
		self.current_mole_index: int | None = None
		self.mole_visible = False
		self.game_over = False
		self.hole_image = self._create_hole_image()
		self.mole_image = self._create_mole_image()

		instructions = (
			"Instructions: Click the mole to whack it. "
			"Misses don’t score. Reach 10 hits to win!"
		)
		self.instructions_label = tk.Label(self.root, text=instructions, font=("Arial", 11), wraplength=560, justify="left")
		self.instructions_label.pack(padx=10, pady=10)

		self.scoreboard_frame = tk.Frame(self.root)
		self.scoreboard_frame.pack(pady=5)

		self.score_label = tk.Label(self.scoreboard_frame, text="Score: 0", font=("Arial", 14))
		self.score_label.pack(side=tk.LEFT, padx=10)

		self.miss_label = tk.Label(self.scoreboard_frame, text="Misses: 0", font=("Arial", 14))
		self.miss_label.pack(side=tk.LEFT, padx=10)

		self.grid_frame = tk.Frame(self.root)
		self.grid_frame.pack(padx=10, pady=10)

		self.holes: list[tk.Button] = []
		for r in range(GRID_ROWS):
			for c in range(GRID_COLS):
				index = r * GRID_COLS + c
				btn = tk.Button(
					self.grid_frame,
					text="",
					bg="saddle brown",
					image=self.hole_image,
					compound="center",
					borderwidth=0,
					highlightthickness=0,
					command=lambda i=index: self.handle_click(i),
				)
				btn.grid(row=r, column=c, padx=10, pady=10)
				self.holes.append(btn)

		self.status_label = tk.Label(self.root, text="Click the mole!", font=("Arial", 12))
		self.status_label.pack(pady=5)

		self.root.after(MOLE_INTERVAL_MS, self.spawn_mole)

	def handle_click(self, index: int) -> None:
		if self.game_over:
			return

		if self.mole_visible and self.current_mole_index == index:
			self.score += 1
			self.update_score_label()
			self.status_label.config(text="Hit!")
			self.hide_mole()
			if self.score >= TARGET_SCORE:
				self.end_game()
		else:
			self.misses += 1
			self.status_label.config(text="Miss!")
			self.update_miss_label()

	def update_score_label(self) -> None:
		self.score_label.config(text=f"Score: {self.score}")

	def update_miss_label(self) -> None:
		self.miss_label.config(text=f"Misses: {self.misses}")

	def spawn_mole(self) -> None:
		if self.game_over:
			return

		if self.mole_visible:
			self.hide_mole()

		new_index = random.randrange(GRID_ROWS * GRID_COLS)
		self.current_mole_index = new_index
		self.mole_visible = True

		btn = self.holes[new_index]
		btn.config(bg="green", image=self.mole_image, compound="center")

		self.root.after(MOLE_VISIBLE_MS, self.on_mole_timeout)
		self.root.after(MOLE_INTERVAL_MS, self.spawn_mole)

	def hide_mole(self) -> None:
		if self.current_mole_index is not None:
			self.holes[self.current_mole_index].config(bg="saddle brown", image=self.hole_image, compound="center")
		self.current_mole_index = None
		self.mole_visible = False

	def on_mole_timeout(self) -> None:
		if self.game_over:
			return
		if self.mole_visible:
			self.misses += 1
			self.status_label.config(text="Too slow!")
			self.update_miss_label()
			self.hide_mole()

	def _create_hole_image(self) -> tk.PhotoImage:
		size = 100
		img = tk.PhotoImage(width=size, height=size)
		bg_color = "#225522"
		hole_color = "#8B4513"
		img.put(bg_color, to=(0, 0, size, size))
		cx, cy, r = size // 2, size // 2, size // 2 - 6
		for x in range(size):
			for y in range(size):
				if (x - cx) * (x - cx) + (y - cy) * (y - cy) <= r * r:
					img.put(hole_color, (x, y))
		return img

	def _create_mole_image(self) -> tk.PhotoImage:
		size = 100
		img = tk.PhotoImage(width=size, height=size)
		bg_color = "#225522"
		mole_color = "#8B4513"
		img.put(bg_color, to=(0, 0, size, size))
		cx, cy, r = size // 2, size // 2, size // 2 - 6
		for x in range(size):
			for y in range(size):
				if (x - cx) * (x - cx) + (y - cy) * (y - cy) <= r * r:
					img.put(mole_color, (x, y))
		for x in range(cx - 12, cx - 4):
			for y in range(cy - 12, cy - 4):
				img.put("#000000", (x, y))
		for x in range(cx + 4, cx + 12):
			for y in range(cy - 12, cy - 4):
				img.put("#000000", (x, y))
		for x in range(cx - 12, cx + 12):
			for y in range(cy + 4, cy + 10):
				img.put("#000000", (x, y))
		return img

	def end_game(self) -> None:
		self.game_over = True
		self.hide_mole()
		for btn in self.holes:
			btn.config(state=tk.DISABLED)
		self.status_label.config(text="Game over!")
		messagebox.showinfo("Game over", f"You reached {self.score} points with {self.misses} misses.")


def main() -> None:
	root = tk.Tk()
	WhackAMoleGame(root)
	root.mainloop()


if __name__ == "__main__":
	main()

