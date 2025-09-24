"""m1 - Simple Tetris implemented with Pygame.

This is a compact, easy-to-read Tetris implementation intended for
learning and small demos. It uses a simple board representation and
basic collision logic.

Usage (Windows PowerShell):
	python m1

Controls:
	Left/Right: move
	Up: rotate
	Down: soft drop
	Space: hard drop
	P: pause
	Esc/Q: quit
"""

import random
import sys
import pygame

# Game configuration
CELL_SIZE = 30
COLUMNS = 10
ROWS = 20
WIDTH = CELL_SIZE * COLUMNS
HEIGHT = CELL_SIZE * ROWS
FPS = 60

# Colors
BLACK = (0, 0, 0)
GRAY = (128, 128, 128)
WHITE = (255, 255, 255)
COLORS = [
	(0, 255, 255),  # I
	(0, 0, 255),    # J
	(255, 165, 0),  # L
	(255, 255, 0),  # O
	(0, 255, 0),    # S
	(128, 0, 128),  # T
	(255, 0, 0),    # Z
]

# Tetromino shapes (4x4 matrices)
SHAPES = [
	[[1, 1, 1, 1]],  # I
	[[1, 0, 0], [1, 1, 1]],  # J
	[[0, 0, 1], [1, 1, 1]],  # L
	[[1, 1], [1, 1]],  # O
	[[0, 1, 1], [1, 1, 0]],  # S
	[[0, 1, 0], [1, 1, 1]],  # T
	[[1, 1, 0], [0, 1, 1]],  # Z
]


def rotate(shape):
	"""Rotate a shape clockwise.

	Shapes are lists-of-lists (rows). Rotation is implemented by
	transposing the reversed rows (zip of reversed rows), then
	converting each resulting tuple back into a list.
	"""
	return [list(row) for row in zip(*shape[::-1])]


class Piece:
	def __init__(self, shape_index):
		self.shape_index = shape_index
		self.shape = SHAPES[shape_index]
		self.color = COLORS[shape_index]
		# start position (top center)
		self.x = COLUMNS // 2 - len(self.shape[0]) // 2
		self.y = 0

	def rotate(self):
		"""Rotate this piece in-place (clockwise)."""
		self.shape = rotate(self.shape)


class Tetris:
	def __init__(self):
		self.board = [[None for _ in range(COLUMNS)] for _ in range(ROWS)]
		self.score = 0
		self.level = 1
		self.lines = 0
		self.fall_time = 0
		self.fall_speed = 500  # milliseconds per cell
		self.current = Piece(random.randrange(len(SHAPES)))
		self.next_piece = Piece(random.randrange(len(SHAPES)))
		self.game_over = False

	def inside(self, x, y):
		"""Return True if (x, y) is inside the play field bounds."""
		return 0 <= x < COLUMNS and 0 <= y < ROWS

	def collision(self, shape, offset_x, offset_y):
		"""Check whether drawing `shape` at (offset_x, offset_y) collides.

		Empty cells in the shape are falsy (0); occupied cells are truthy.
		We consider collision when the position is out-of-bounds or the
		board already contains a block at the target position.
		"""
		for dy, row in enumerate(shape):
			for dx, cell in enumerate(row):
				if not cell:
					continue
				x = offset_x + dx
				y = offset_y + dy
				if not self.inside(x, y) or (y >= 0 and self.board[y][x] is not None):
					return True
		return False

	def lock_piece(self):
		"""Lock the current piece into the board and spawn the next piece.

		After inserting the piece cells into `self.board`, we clear any
		completed lines, advance current/next pieces, and check for
		immediate collision which indicates game over.
		"""
		for dy, row in enumerate(self.current.shape):
			for dx, cell in enumerate(row):
				if not cell:
					continue
				x = self.current.x + dx
				y = self.current.y + dy
				if 0 <= y < ROWS and 0 <= x < COLUMNS:
					self.board[y][x] = self.current.color
		self.clear_lines()
		self.current = self.next_piece
		self.next_piece = Piece(random.randrange(len(SHAPES)))
		if self.collision(self.current.shape, self.current.x, self.current.y):
			# New piece collides immediately -> game over
			self.game_over = True

	def clear_lines(self):
		"""Remove completed lines from the board and update score/level.

		Simple scoring: square of cleared lines * 100 (e.g., single=100,
		double=400, triple=900, tetris=1600). Level increases every 10
		lines and fall speed becomes faster (lower milliseconds).
		"""
		new_board = [row for row in self.board if any(cell is None for cell in row)]
		cleared = ROWS - len(new_board)
		if cleared > 0:
			for _ in range(cleared):
				new_board.insert(0, [None for _ in range(COLUMNS)])
			self.board = new_board
			self.lines += cleared
			self.score += (cleared ** 2) * 100
			self.level = max(1, 1 + self.lines // 10)
			# Make falling speed faster as level increases
			self.fall_speed = max(50, 500 - (self.level - 1) * 40)

	def move(self, dx):
		"""Attempt to move the current piece horizontally by dx (-1 or +1)."""
		if not self.collision(self.current.shape, self.current.x + dx, self.current.y):
			self.current.x += dx

	def rotate_current(self):
		"""Rotate the current piece if there's no collision after rotation."""
		new_shape = rotate(self.current.shape)
		if not self.collision(new_shape, self.current.x, self.current.y):
			self.current.shape = new_shape

	def soft_drop(self):
		"""Move the piece one cell down (soft drop).

		Returns True if the piece moved, False if it was locked because it
		couldn't move further.
		"""
		if not self.collision(self.current.shape, self.current.x, self.current.y + 1):
			self.current.y += 1
			return True
		else:
			self.lock_piece()
			return False

	def hard_drop(self):
		while not self.collision(self.current.shape, self.current.x, self.current.y + 1):
			self.current.y += 1
		self.lock_piece()


def draw_grid(surface):
	"""Draw the grid lines over the playfield for visual clarity."""
	for x in range(COLUMNS + 1):
		pygame.draw.line(surface, GRAY, (x * CELL_SIZE, 0), (x * CELL_SIZE, HEIGHT))
	for y in range(ROWS + 1):
		pygame.draw.line(surface, GRAY, (0, y * CELL_SIZE), (WIDTH, y * CELL_SIZE))


def draw_board(surface, game):
	"""Render the board (locked blocks) and the currently falling piece."""
	surface.fill(BLACK)
	# Draw locked blocks on the board
	for y, row in enumerate(game.board):
		for x, cell in enumerate(row):
			if cell is not None:
				rect = pygame.Rect(x * CELL_SIZE, y * CELL_SIZE, CELL_SIZE, CELL_SIZE)
				pygame.draw.rect(surface, cell, rect)
				pygame.draw.rect(surface, WHITE, rect, 1)
	# Draw the active falling piece
	for dy, row in enumerate(game.current.shape):
		for dx, cell in enumerate(row):
			if not cell:
				continue
			x = game.current.x + dx
			y = game.current.y + dy
			if y >= 0:
				rect = pygame.Rect(x * CELL_SIZE, y * CELL_SIZE, CELL_SIZE, CELL_SIZE)
				pygame.draw.rect(surface, game.current.color, rect)
				pygame.draw.rect(surface, WHITE, rect, 1)
	draw_grid(surface)


def draw_side(surface, game, font):
	# Draw score/lines/level in the top-left corner of the window.
	# `sx` and `surface_rect` are leftovers from a two-pane layout; they
	# are kept for clarity but not used in this simple single-surface UI.
	sx = WIDTH + 10
	surface_rect = surface.get_rect()
	text_surface = font.render(f"Score: {game.score}", True, WHITE)
	surface.blit(text_surface, (10, 10))
	text_surface = font.render(f"Lines: {game.lines}", True, WHITE)
	surface.blit(text_surface, (10, 40))
	text_surface = font.render(f"Level: {game.level}", True, WHITE)
	surface.blit(text_surface, (10, 70))


def main():
	pygame.init()
	pygame.display.set_caption("Tetris - m1")
	screen = pygame.display.set_mode((WIDTH, HEIGHT))
	clock = pygame.time.Clock()
	font = pygame.font.SysFont(None, 24)

	game = Tetris()
	paused = False
	drop_event = pygame.USEREVENT + 1
	pygame.time.set_timer(drop_event, game.fall_speed)

	running = True
	# Main game loop: process events, update game state, render.
	while running:
		dt = clock.tick(FPS)
		for event in pygame.event.get():
			if event.type == pygame.QUIT:
				running = False
			elif event.type == pygame.KEYDOWN:
				# Quit keys
				if event.key == pygame.K_ESCAPE or event.key == pygame.K_q:
					running = False
				# Toggle pause
				if event.key == pygame.K_p:
					paused = not paused
				# Gameplay keys only have effect when not paused and not over
				if not paused and not game.game_over:
					if event.key == pygame.K_LEFT:
						game.move(-1)
					elif event.key == pygame.K_RIGHT:
						game.move(1)
					elif event.key == pygame.K_UP:
						game.rotate_current()
					elif event.key == pygame.K_DOWN:
						game.soft_drop()
					elif event.key == pygame.K_SPACE:
						game.hard_drop()
			elif event.type == drop_event and not paused and not game.game_over:
				# Timer-driven automatic drop
				if not game.soft_drop():
					# Piece locked; adjust timer to current fall speed
					pygame.time.set_timer(drop_event, game.fall_speed)
        print
		# Render scene
		draw_board(screen, game)
		draw_side(screen, game, font)

		# Show paused/game-over messages
		if paused:
			text = font.render("PAUSED", True, WHITE)
			screen.blit(text, (WIDTH // 2 - text.get_width() // 2, HEIGHT // 2))
		if game.game_over:
			text = font.render("GAME OVER - Press Esc to quit", True, WHITE)
			screen.blit(text, (WIDTH // 2 - text.get_width() // 2, HEIGHT // 2))

		pygame.display.flip()

	pygame.quit()


if __name__ == "__main__":
	try:
		main()
	except Exception as e:
		print("Error:", e)
		pygame.quit()
		raise

