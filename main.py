import random
import tkinter as tk
from tkinter import messagebox


GRID_ROWS = 3
GRID_COLS = 3
MOLE_VISIBLE_MS = 800
MOLE_INTERVAL_MS = 1000
TARGET_SCORE = 10


class WhackAMoleGame:
	def __init__(self, root: tk.Tk) -> None:
		self.root = root
		self.root.title("Whack-A-Mole")

		self.score = 0
		self.misses = 0
		self.current_mole_index: int | None = None
		self.mole_visible = False
		self.game_over = False

		self.score_label = tk.Label(self.root, text="Score: 0", font=("Arial", 14))
		self.score_label.pack(pady=10)

		self.grid_frame = tk.Frame(self.root)
		self.grid_frame.pack(padx=10, pady=10)

		self.holes: list[tk.Button] = []
		for r in range(GRID_ROWS):
			for c in range(GRID_COLS):
				index = r * GRID_COLS + c
				btn = tk.Button(
					self.grid_frame,
					text="",
					width=8,
					height=4,
					bg="saddle brown",
					command=lambda i=index: self.handle_click(i),
				)
				btn.grid(row=r, column=c, padx=5, pady=5)
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

	def update_score_label(self) -> None:
		self.score_label.config(text=f"Score: {self.score}")

	def spawn_mole(self) -> None:
		if self.game_over:
			return

		if self.mole_visible:
			self.hide_mole()

		new_index = random.randrange(GRID_ROWS * GRID_COLS)
		self.current_mole_index = new_index
		self.mole_visible = True

		btn = self.holes[new_index]
		btn.config(bg="green")

		self.root.after(MOLE_VISIBLE_MS, self.on_mole_timeout)
		self.root.after(MOLE_INTERVAL_MS, self.spawn_mole)

	def hide_mole(self) -> None:
		if self.current_mole_index is not None:
			self.holes[self.current_mole_index].config(bg="saddle brown")
		self.current_mole_index = None
		self.mole_visible = False

	def on_mole_timeout(self) -> None:
		if self.game_over:
			return
		if self.mole_visible:
			self.misses += 1
			self.status_label.config(text="Too slow!")
			self.hide_mole()

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

