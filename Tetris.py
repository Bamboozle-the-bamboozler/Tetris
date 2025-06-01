import pygame
import random

# --- Constants ---
SCREEN_WIDTH, SCREEN_HEIGHT = 300, 600
BLOCK_SIZE = 30
COLUMNS, ROWS = SCREEN_WIDTH // BLOCK_SIZE, SCREEN_HEIGHT // BLOCK_SIZE
FPS = 60

PREVIEW_WIDTH, PREVIEW_HEIGHT = 6 * BLOCK_SIZE, 6 * BLOCK_SIZE  # Preview box size

# Colors
BLACK = (0, 0, 0)
GRAY = (128, 128, 128)
WHITE = (255, 255, 255)
GHOST_COLOR = (200, 200, 200)
COLORS = [
    (0, 255, 255), (0, 0, 255), (255, 165, 0),
    (255, 255, 0), (0, 255, 0), (128, 0, 128), (255, 0, 0)
]

# Shape formats
SHAPES = [
    [[1, 1, 1, 1]],  # I
    [[2, 0, 0], [2, 2, 2]],  # J
    [[0, 0, 3], [3, 3, 3]],  # L
    [[4, 4], [4, 4]],        # O
    [[0, 5, 5], [5, 5, 0]],  # S
    [[0, 6, 0], [6, 6, 6]],  # T
    [[7, 7, 0], [0, 7, 7]],  # Z
]

def get_rotations(shape):
    """Returns a list of all rotation states for a shape."""
    rotations = [shape]
    for _ in range(3):
        shape = [list(row) for row in zip(*shape[::-1])]
        if not any([shape == r for r in rotations]):
            rotations.append(shape)
    return rotations

class Piece:
    def __init__(self, x, y, shape):
        self.x, self.y = x, y
        self.shape_index = SHAPES.index(shape)
        self.rotations = get_rotations(shape)
        self.rotation = 0  # Index in self.rotations

    @property
    def color(self):
        return COLORS[self.shape_index]

    def image(self):
        return self.rotations[self.rotation % len(self.rotations)]

    def rotate(self):
        # O block (square) doesn't rotate
        if len(self.rotations) > 1:
            prev_rotation = self.rotation
            self.rotation = (self.rotation + 1) % len(self.rotations)
            return True
        return False

    def undo_rotate(self):
        if len(self.rotations) > 1:
            self.rotation = (self.rotation - 1) % len(self.rotations)

def create_grid(locked_positions={}):
    grid = [[BLACK for _ in range(COLUMNS)] for _ in range(ROWS)]
    for y in range(ROWS):
        for x in range(COLUMNS):
            if (x, y) in locked_positions:
                grid[y][x] = locked_positions[(x, y)]
    return grid

def convert_shape_format(piece):
    positions = []
    shape = piece.image()
    for i, row in enumerate(shape):
        for j, column in enumerate(row):
            if column != 0:
                positions.append((piece.x + j, piece.y + i))
    return positions

def valid_space(piece, grid):
    accepted_positions = [
        (j, i) for i in range(ROWS) for j in range(COLUMNS) if grid[i][j] == BLACK
    ]
    formatted = convert_shape_format(piece)
    for pos in formatted:
        if pos not in accepted_positions:
            if pos[1] >= 0:
                return False
    return True

def check_lost(positions):
    return any(y < 1 for (x, y) in positions)

def clear_rows(grid, locked):
    inc = 0
    remove_indices = []
    for i in range(ROWS-1, -1, -1):
        row = grid[i]
        if BLACK not in row:
            inc += 1
            remove_indices.append(i)
            for j in range(COLUMNS):
                try:
                    del locked[(j, i)]
                except:
                    continue
    if inc > 0:
        # Move every row above down
        for i in sorted(remove_indices):
            for key in sorted(list(locked), key=lambda x: x[1]):
                x, y = key
                if y < i:
                    newKey = (x, y + 1)
                    locked[newKey] = locked.pop(key)
    return inc

def get_shape():
    return Piece(3, 0, random.choice(SHAPES))

def draw_text_middle(surface, text, size, color):
    font = pygame.font.SysFont("comicsans", size, bold=True)
    label = font.render(text, 1, color)
    surface.blit(label, (
        SCREEN_WIDTH // 2 - label.get_width() // 2,
        SCREEN_HEIGHT // 2 - label.get_height() // 2
    ))

def draw_grid(surface, grid):
    for i in range(ROWS):
        pygame.draw.line(surface, GRAY, (0, i * BLOCK_SIZE), (SCREEN_WIDTH, i * BLOCK_SIZE))
        for j in range(COLUMNS):
            pygame.draw.line(surface, GRAY, (j * BLOCK_SIZE, 0), (j * BLOCK_SIZE, SCREEN_HEIGHT))
    pygame.draw.rect(surface, WHITE, (0, 0, SCREEN_WIDTH, SCREEN_HEIGHT), 5)

def draw_window(surface, grid, score=0, level=1):
    surface.fill(BLACK)
    font = pygame.font.SysFont("comicsans", 30)
    label = font.render(f'Score: {score}', 1, WHITE)
    level_label = font.render(f'Level: {level}', 1, WHITE)

    surface.blit(label, (10, 10))
    surface.blit(level_label, (SCREEN_WIDTH - 120, 10))

    for i in range(ROWS):
        for j in range(COLUMNS):
            pygame.draw.rect(
                surface, grid[i][j],
                (j * BLOCK_SIZE, i * BLOCK_SIZE, BLOCK_SIZE, BLOCK_SIZE), 0
            )
    draw_grid(surface, grid)

def draw_ghost_piece(surface, piece, locked_positions):
    ghost = Piece(piece.x, piece.y, SHAPES[piece.shape_index])
    ghost.rotation = piece.rotation
    grid = create_grid(locked_positions)
    while True:
        ghost.y += 1
        if not valid_space(ghost, grid):
            ghost.y -= 1
            break
    ghost_pos = convert_shape_format(ghost)
    for x, y in ghost_pos:
        if y >= 0:
            pygame.draw.rect(
                surface, GHOST_COLOR,
                (x * BLOCK_SIZE, y * BLOCK_SIZE, BLOCK_SIZE, BLOCK_SIZE), 2  # Outline only
            )

def draw_next_piece(surface, next_piece):
    font = pygame.font.SysFont("comicsans", 20)
    label = font.render('Next:', 1, WHITE)
    preview_x = SCREEN_WIDTH + 20
    preview_y = 60
    surface.blit(label, (preview_x, preview_y - 30))
    shape = next_piece.image()
    shape_width = len(shape[0]) * BLOCK_SIZE
    shape_height = len(shape) * BLOCK_SIZE
    offset_x = preview_x + (PREVIEW_WIDTH - shape_width) // 2
    offset_y = preview_y + (PREVIEW_HEIGHT - shape_height) // 2
    for i, row in enumerate(shape):
        for j, val in enumerate(row):
            if val != 0:
                pygame.draw.rect(
                    surface, next_piece.color,
                    (offset_x + j * BLOCK_SIZE, offset_y + i * BLOCK_SIZE, BLOCK_SIZE, BLOCK_SIZE), 0
                )
    pygame.draw.rect(
        surface, WHITE,
        (preview_x, preview_y, PREVIEW_WIDTH, PREVIEW_HEIGHT), 2
    )

def main():
    pygame.init()
    pygame.key.set_repeat(200, 70)  # Smoother, but not too fast for movement
    win = pygame.display.set_mode((SCREEN_WIDTH + PREVIEW_WIDTH + 40, SCREEN_HEIGHT))
    pygame.display.set_caption('Tetris')
    clock = pygame.time.Clock()

    locked_positions = {}
    grid = create_grid(locked_positions)

    change_piece = False
    run = True
    current_piece = get_shape()
    next_piece = get_shape()
    fall_time = 0
    score = 0
    level = 1
    fall_speed = 0.5

    line_clear_animation = False
    lines_to_clear = []

    while run:
        grid = create_grid(locked_positions)
        fall_time += clock.get_rawtime()
        clock.tick(FPS)

        fall_speed = max(0.12, 0.5 - (level - 1) * 0.04)

        if not line_clear_animation:
            if fall_time / 1000 > fall_speed:
                fall_time = 0
                current_piece.y += 1
                if not valid_space(current_piece, grid) and current_piece.y > 0:
                    current_piece.y -= 1
                    change_piece = True

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
                pygame.display.quit()
                quit()

            if event.type == pygame.KEYDOWN:
                if line_clear_animation:
                    continue
                if event.key == pygame.K_LEFT:
                    current_piece.x -= 1
                    if not valid_space(current_piece, grid):
                        current_piece.x += 1
                elif event.key == pygame.K_RIGHT:
                    current_piece.x += 1
                    if not valid_space(current_piece, grid):
                        current_piece.x -= 1
                elif event.key == pygame.K_DOWN:
                    current_piece.y += 1
                    if not valid_space(current_piece, grid):
                        current_piece.y -= 1
                elif event.key == pygame.K_UP:
                    prev_rotation = current_piece.rotation
                    current_piece.rotate()
                    if not valid_space(current_piece, grid):
                        kicked = False
                        for dx in [-1, 1, -2, 2]:
                            current_piece.x += dx
                            if valid_space(current_piece, grid):
                                kicked = True
                                break
                            current_piece.x -= dx
                        if not kicked:
                            current_piece.rotation = prev_rotation  # Undo rotate

        shape_pos = convert_shape_format(current_piece)

        win.fill(BLACK)
        draw_window(win, grid, score, level)
        draw_ghost_piece(win, current_piece, locked_positions)
        for x, y in shape_pos:
            if y > -1:
                pygame.draw.rect(
                    win, current_piece.color,
                    (x * BLOCK_SIZE, y * BLOCK_SIZE, BLOCK_SIZE, BLOCK_SIZE), 0
                )
        draw_next_piece(win, next_piece)

        if line_clear_animation and lines_to_clear:
            for row_idx in lines_to_clear:
                pygame.draw.rect(
                    win, (255, 255, 255),
                    (0, row_idx * BLOCK_SIZE, SCREEN_WIDTH, BLOCK_SIZE)
                )
            pygame.display.update()
            pygame.time.delay(120)
            for row_idx in lines_to_clear:
                for j in range(COLUMNS):
                    try:
                        del locked_positions[(j, row_idx)]
                    except:
                        continue
            for row_idx in sorted(lines_to_clear):
                for key in sorted(list(locked_positions), key=lambda x: x[1]):
                    x, y = key
                    if y < row_idx:
                        newKey = (x, y + 1)
                        locked_positions[newKey] = locked_positions.pop(key)
            score += len(lines_to_clear) * 100
            level = 1 + score // 500
            line_clear_animation = False
            lines_to_clear = []
            continue

        pygame.display.update()

        if change_piece and not line_clear_animation:
            for pos in shape_pos:
                p = (pos[0], pos[1])
                locked_positions[p] = current_piece.color
            grid_with_piece = create_grid(locked_positions)
            lines_to_clear = []
            for i in range(ROWS):
                if BLACK not in grid_with_piece[i]:
                    lines_to_clear.append(i)
            if lines_to_clear:
                line_clear_animation = True
                change_piece = False
                continue
            current_piece = next_piece
            next_piece = get_shape()
            change_piece = False

        if check_lost(locked_positions):
            draw_text_middle(win, "GAME OVER", 80, (255, 0, 0))
            pygame.display.update()
            pygame.time.delay(2000)
            run = False

if __name__ == '__main__':
    main()
