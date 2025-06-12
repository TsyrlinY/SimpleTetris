# ---
# Тетрис на Python (Pygame)
# Вдохновлено референсом: https://ru.pinterest.com/pin/7036943159458914/
# ---
# Управление:
# Влево/Вправо — перемещение, Вниз — ускорить, Вверх — повернуть, Пробел — мгновенное падение
# ---

import pygame
import sys
import random
import os

# --- Константы ---
WINDOW_WIDTH, WINDOW_HEIGHT = 600, 600  # Размер окна
PLAY_WIDTH, PLAY_HEIGHT = 240, 480      # Размер игрового поля (10x20)
BLOCK_SIZE = 24                        # Размер одного блока
TOP_LEFT_X = (WINDOW_WIDTH - PLAY_WIDTH) // 2  # Смещение поля по X
TOP_LEFT_Y = WINDOW_HEIGHT - PLAY_HEIGHT - 40  # Смещение поля по Y

# Цвета (вдохновлены референсом)
BLACK = (10, 10, 10)   # Фон
WHITE = (255, 255, 255) # Текст, рамки
COLORS = [
    (255, 0, 0),      # Ярко-красный
    (0, 255, 0),      # Ярко-зелёный
    (0, 0, 255),      # Ярко-синий
    (255, 165, 0),    # Оранжевый
    (0, 255, 255),    # Голубой
    (128, 0, 255),    # Фиолетовый
    (255, 255, 0)     # Жёлтый
]

# --- Описание фигур (матрицы 5x5) ---
S = [['.....', '.....', '..00.', '.00..', '.....'],
     ['.....', '..0..', '..00.', '...0.', '.....']]
Z = [['.....', '.....', '.00..', '..00.', '.....'],
     ['.....', '..0..', '.00..', '.0...', '.....']]
I = [['..0..', '..0..', '..0..', '..0..', '.....'],
     ['.....', '0000.', '.....', '.....', '.....']]
O = [['.....', '.....', '.00..', '.00..', '.....']]
J = [['.....', '.0...', '.000.', '.....', '.....'],
     ['.....', '..00.', '..0..', '..0..', '.....'],
     ['.....', '.....', '.000.', '...0.', '.....'],
     ['.....', '..0..', '..0..', '.00..', '.....']]
L = [['.....', '...0.', '.000.', '.....', '.....'],
     ['.....', '..0..', '..0..', '..00.', '.....'],
     ['.....', '.....', '.000.', '.0...', '.....'],
     ['.....', '.00..', '..0..', '..0..', '.....']]
T = [['.....', '..0..', '.000.', '.....', '.....'],
     ['.....', '..0..', '..00.', '..0..', '.....'],
     ['.....', '.....', '.000.', '..0..', '.....'],
     ['.....', '..0..', '.00..', '..0..', '.....']]

SHAPES = [S, Z, I, O, J, L, T]
SHAPE_COLORS = COLORS

# --- Класс фигуры ---
class Piece:
    def __init__(self, x, y, shape):
        self.x = x  # Положение фигуры по X
        self.y = y  # Положение фигуры по Y
        self.shape = shape  # Матрица фигуры
        self.color = SHAPE_COLORS[SHAPES.index(shape)]  # Цвет фигуры
        self.rotation = 0  # Текущий поворот

# --- Создание сетки игрового поля ---
def create_grid(locked_positions={}):
    grid = [[BLACK for _ in range(10)] for _ in range(20)]
    for i in range(len(grid)):
        for j in range(len(grid[i])):
            if (j, i) in locked_positions:
                grid[i][j] = locked_positions[(j, i)]
    return grid

# --- Преобразование фигуры в координаты на поле ---
def convert_shape_format(piece):
    positions = []
    format = piece.shape[piece.rotation % len(piece.shape)]
    for i, line in enumerate(format):
        row = list(line)
        for j, column in enumerate(row):
            if column == '0':
                positions.append((piece.x + j, piece.y + i))
    return positions

# --- Проверка валидности положения фигуры ---
def valid_space(piece, grid):
    accepted_pos = [[(j, i) for j in range(10) if grid[i][j] == BLACK] for i in range(20)]
    accepted_pos = [j for sub in accepted_pos for j in sub]
    formatted = convert_shape_format(piece)
    for pos in formatted:
        if pos not in accepted_pos:
            if pos[1] > -1:
                return False
    return True

# --- Проверка проигрыша ---
def check_lost(positions):
    for pos in positions:
        x, y = pos
        if y < 1:
            return True
    return False

# --- Получение случайной фигуры ---
def get_shape():
    return Piece(3, 0, random.choice(SHAPES))

# --- Отрисовка текста по центру ---
def draw_text_middle(surface, text, size, color):
    font = pygame.font.SysFont('comicsans', size, bold=True)
    label = font.render(text, 1, color)
    surface.blit(label, (TOP_LEFT_X + PLAY_WIDTH/2 - (label.get_width()/2),
                        TOP_LEFT_Y + PLAY_HEIGHT/2 - label.get_height()/2))

# --- Отрисовка сетки ---
def draw_grid(surface, grid):
    sx = TOP_LEFT_X
    sy = TOP_LEFT_Y
    for i in range(len(grid)):
        pygame.draw.line(surface, (40, 40, 40), (sx, sy + i*BLOCK_SIZE), (sx + PLAY_WIDTH, sy + i*BLOCK_SIZE))
        for j in range(len(grid[i])):
            pygame.draw.line(surface, (40, 40, 40), (sx + j*BLOCK_SIZE, sy), (sx + j*BLOCK_SIZE, sy + PLAY_HEIGHT))

# --- Очистка заполненных линий ---
def clear_rows(grid, locked):
    inc = 0
    for i in range(len(grid)-1, -1, -1):
        row = grid[i]
        if BLACK not in row:
            inc += 1
            ind = i
            for j in range(len(row)):
                try:
                    del locked[(j, i)]
                except:
                    continue
    if inc > 0:
        for key in sorted(list(locked), key=lambda x: x[1])[::-1]:
            x, y = key
            if y < ind:
                newKey = (x, y + inc)
                locked[newKey] = locked.pop(key)
    return inc

# --- Отрисовка следующей фигуры ---
def draw_next_shape(piece, surface):
    sx = TOP_LEFT_X + PLAY_WIDTH + 40
    sy = TOP_LEFT_Y + 2*60 + 30  # 2*spacing + небольшой отступ
    format = piece.shape[piece.rotation % len(piece.shape)]
    for i, line in enumerate(format):
        row = list(line)
        for j, column in enumerate(row):
            if column == '0':
                pygame.draw.rect(surface, piece.color, (sx + j*BLOCK_SIZE, sy + i*BLOCK_SIZE, BLOCK_SIZE, BLOCK_SIZE), 0)

# --- Основное окно игры ---
def draw_window(surface, grid, score=0, last_score=0):
    surface.fill(BLACK)
    # Название
    font = pygame.font.SysFont('comicsans', 40)
    label = font.render('ТЕТРИС', 1, WHITE)
    surface.blit(label, (TOP_LEFT_X + PLAY_WIDTH/2 - (label.get_width()/2), 10))
    # Расчёт позиций для равных отступов
    sx = TOP_LEFT_X + PLAY_WIDTH + 40
    sy = TOP_LEFT_Y
    spacing = 60
    # Счёт
    font = pygame.font.SysFont('comicsans', 24)
    label = font.render(f'Счёт: {score}', 1, WHITE)
    surface.blit(label, (sx, sy))
    # Рекорд
    label = font.render(f'Рекорд: {last_score}', 1, WHITE)
    surface.blit(label, (sx, sy + spacing))
    # Надпись 'Следующая'
    label = font.render('Следующая:', 1, WHITE)
    surface.blit(label, (sx, sy + 2*spacing))
    # Игровое поле
    for i in range(len(grid)):
        for j in range(len(grid[i])):
            pygame.draw.rect(surface, grid[i][j], (TOP_LEFT_X + j*BLOCK_SIZE, TOP_LEFT_Y + i*BLOCK_SIZE, BLOCK_SIZE, BLOCK_SIZE), 0)
    # Сетка
    draw_grid(surface, grid)
    # Рамка
    pygame.draw.rect(surface, WHITE, (TOP_LEFT_X, TOP_LEFT_Y, PLAY_WIDTH, PLAY_HEIGHT), 4)

# --- Сохранение рекорда ---
def update_score(new_score):
    score = get_max_score()
    with open('record.txt', 'w') as f:
        if new_score > score:
            f.write(str(new_score))
        else:
            f.write(str(score))

# --- Получение рекорда ---
def get_max_score():
    try:
        with open('record.txt', 'r') as f:
            lines = f.readlines()
            score = int(lines[0].strip())
    except:
        score = 0
    return score

# --- ДОБАВЛЕНИЕ ЗВУКОВ ---
def play_sound(name):
    try:
        pygame.mixer.Sound(os.path.join('sounds', name)).play()
    except Exception:
        pass

# --- Основной игровой цикл ---
def main():
    pygame.init()
    pygame.mixer.init()
    win = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
    pygame.display.set_caption('Тетрис')
    run = True
    clock = pygame.time.Clock()
    fall_time = 0
    fall_speed = 0.35
    level_time = 0
    score = 0
    last_score = get_max_score()
    locked_positions = {}
    grid = create_grid(locked_positions)
    change_piece = False
    current_piece = get_shape()
    next_piece = get_shape()
    while run:
        grid = create_grid(locked_positions)
        fall_time += clock.get_rawtime()
        level_time += clock.get_rawtime()
        clock.tick()
        # Ускорение игры со временем
        if level_time/1000 > 5:
            level_time = 0
            if fall_speed > 0.12:
                fall_speed -= 0.005
        # Падение фигуры
        if fall_time/1000 > fall_speed:
            fall_time = 0
            current_piece.y += 1
            if not(valid_space(current_piece, grid)) and current_piece.y > 0:
                current_piece.y -= 1
                change_piece = True
        # Обработка событий
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
                pygame.display.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_LEFT:
                    current_piece.x -= 1
                    if not(valid_space(current_piece, grid)):
                        current_piece.x += 1
                if event.key == pygame.K_RIGHT:
                    current_piece.x += 1
                    if not(valid_space(current_piece, grid)):
                        current_piece.x -= 1
                if event.key == pygame.K_DOWN:
                    current_piece.y += 1
                    if not(valid_space(current_piece, grid)):
                        current_piece.y -= 1
                if event.key == pygame.K_UP:
                    current_piece.rotation = (current_piece.rotation + 1) % len(current_piece.shape)
                    if valid_space(current_piece, grid):
                        play_sound('rotate.wav')
                    else:
                        current_piece.rotation = (current_piece.rotation - 1) % len(current_piece.shape)
                if event.key == pygame.K_SPACE:
                    while valid_space(current_piece, grid):
                        current_piece.y += 1
                    current_piece.y -= 1
        # Отрисовка фигуры на поле
        shape_pos = convert_shape_format(current_piece)
        for i in range(len(shape_pos)):
            x, y = shape_pos[i]
            if y > -1:
                grid[y][x] = current_piece.color
        # Если фигура упала
        if change_piece:
            for pos in shape_pos:
                p = (pos[0], pos[1])
                locked_positions[p] = current_piece.color
            current_piece = next_piece
            next_piece = get_shape()
            change_piece = False
            cleared = clear_rows(grid, locked_positions)
            if cleared > 0:
                play_sound('clear.wav')
            score += cleared * 10
            # Синхронизация рекорда и счёта
            if score > last_score:
                last_score = score
                update_score(score)
        # Отрисовка окна
        draw_window(win, grid, score, last_score)
        draw_next_shape(next_piece, win)
        pygame.display.update()
        # Проверка проигрыша
        if check_lost(locked_positions):
            play_sound('gameover.wav')
            draw_text_middle(win, 'Вы проиграли!', 40, (255, 255, 255))
            pygame.display.update()
            pygame.time.delay(2000)
            run = False
            update_score(score)

# --- Главное меню ---
def main_menu():
    pygame.init()
    win = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
    pygame.display.set_caption('Тетрис')
    run = True
    while run:
        win.fill(BLACK)
        draw_text_middle(win, 'Нажмите любую клавишу для старта', 32, WHITE)
        pygame.display.update()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
                pygame.display.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                main()
    pygame.quit()

if __name__ == '__main__':
    main_menu() 