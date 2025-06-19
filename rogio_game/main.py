import pygame
import random
import sys
import math
from pygame import mixer
# Инициализация Pygame
pygame.init()
from src.bullet import Bullet
from src.enemy import Enemy
from src.obstacle import Obstacle
# --- ГЛОБАЛЬНЫЕ КОНСТАНТЫ ---
# Размеры экрана
WIDTH, HEIGHT = 800, 600
SCREEN_SIZE = (WIDTH, HEIGHT)
# Цвета
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
GRAY = (100, 100, 100)
YELLOW = (255, 255, 0)
# Шрифты (будут инициализированы в классе Game)
FONT_SIZE_NORMAL = 36
FONT_SIZE_BIG = 72
FONT_NAME = None # Используем системный шрифт по умолчанию
# Параметры игрока
PLAYER_RADIUS = 20 # Радиус хитбокса игрока
PLAYER_BASE_SPEED = 5
PLAYER_BASE_HEALTH = 100
PLAYER_BASE_EXP_TO_LEVEL = 100
PLAYER_ATTACK_RANGE = 150
PLAYER_EXP_REWARD_ENEMY = 20
PLAYER_SCORE_REWARD_ENEMY = 10
PLAYER_DAMAGE_LEVEL_UP_BONUS = 5
PLAYER_SPEED_LEVEL_UP_BONUS = 0.2
PLAYER_EXP_TO_LEVEL_MULTIPLIER = 1.5
# Типы игроков
PLAYER_TYPE_STRONG_DAMAGE = 30
PLAYER_TYPE_STRONG_ATTACK_SPEED = 0.5 # атак в секунду
PLAYER_TYPE_STRONG_COLOR = BLUE # Цвет для индикации, если нужен
PLAYER_TYPE_FAST_DAMAGE = 10
PLAYER_TYPE_FAST_ATTACK_SPEED = 2 # атак в секунду
PLAYER_TYPE_FAST_COLOR = GREEN # Цвет для индикации, если нужен
# Параметры волн
MAX_WAVES = 5
WAVE_BASE_ENEMIES = 3
WAVE_ENEMIES_PER_WAVE = 2
ENEMY_SPAWN_CHANCE = 0.05 # Шанс появления врага за кадр
ENEMY_SPAWN_OFFSET = 20 # Отступ от края экрана для появления врагов
# Параметры препятствий
OBSTACLE_COUNT = 10
OBSTACLE_MIN_SIZE = 30
OBSTACLE_MAX_SIZE = 80
OBSTACLE_PLAYER_SAFE_ZONE = 150 # Радиус вокруг игрока, где не появляются препятствия
# Настройки звука
MUSIC_VOLUME_DEFAULT = 0.5
SOUND_VOLUME_DEFAULT = 0.7
BUTTON_SOUND_VOLUME = 0.5
SHOOT_SOUND_VOLUME = 0.2
HIT_SOUND_VOLUME = 0.4
# Параметры UI
OVERLAY_ALPHA = 180 # Прозрачность оверлеев (0-255)
TITLE_IMAGE_SIZE = (500, 250) # Изменена ширина заголовка на 500 пикселей
BUTTON_WIDTH = 200
BUTTON_HEIGHT = 60
# --- Инициализация Pygame и экрана ---
screen = pygame.display.set_mode(SCREEN_SIZE)
pygame.display.set_caption("rog.io")
# --- Инициализация микшера звука ---
mixer_available = False
button_sound = None
shoot_sound = None
hit_sound = None
try:
    mixer.init()
    mixer_available = True
    button_sound = mixer.Sound('sounds/button.wav')
    shoot_sound = mixer.Sound('sounds/shoot.wav')
    hit_sound = mixer.Sound('sounds/hit.wav')
    button_sound.set_volume(BUTTON_SOUND_VOLUME)
    shoot_sound.set_volume(SHOOT_SOUND_VOLUME)
    hit_sound.set_volume(HIT_SOUND_VOLUME)
except Exception as error:
    print(f"Error initializing mixer: {error}")
    print("Audio drivers:", pygame.mixer.get_init())
    print("Sound devices:", pygame.mixer.get_num_channels())
    print("Sound initialization failed - continuing without sound")
# --- Вспомогательные функции ---
def _play_sound(sound_obj):
    """Воспроизводит звук, если микшер доступен."""
    if mixer_available and sound_obj:
        sound_obj.play()
def _draw_overlay(surface, alpha=OVERLAY_ALPHA):
    """Рисует полупрозрачный черный оверлей на экране."""
    s = pygame.Surface(SCREEN_SIZE, pygame.SRCALPHA)
    s.fill((0, 0, 0, alpha))
    surface.blit(s, (0, 0))
def load_image(path, size=None, colorkey=None):
    """
    Загружает изображение, масштабирует его и устанавливает colorkey при необходимости.
    """
    try:
        image = pygame.image.load(path).convert_alpha()
    except pygame.error as e:
        print(f"Error loading image {path}: {e}")
        return pygame.Surface((1, 1), pygame.SRCALPHA)
    if colorkey is not None:
        image.set_colorkey(colorkey)
    if size is not None:
        image = pygame.transform.scale(image, size)
    return image
# --- Класс Button ---
class Button:
    def __init__(self, x, y, width, height, text, color, hover_color, font_obj): # Принимает объект шрифта
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.color = color
        self.hover_color = hover_color
        self.current_color = color
        self.font = font_obj # Используем переданный объект шрифта
    def draw(self, surface):
        pygame.draw.rect(surface, self.current_color, self.rect)
        text_surf = self.font.render(self.text, True, WHITE)
        text_rect = text_surf.get_rect(center=self.rect.center)
        surface.blit(text_surf, text_rect)
    def check_hover(self, mouse_pos):
        if self.rect.collidepoint(mouse_pos):
            self.current_color = self.hover_color
        else:
            self.current_color = self.color
    def is_clicked(self, mouse_pos, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            return self.rect.collidepoint(mouse_pos)
        return False
# --- Класс Player ---
class Player:
    def __init__(self, x, y, player_type, player_sprite):
        self.x = x
        self.y = y
        self.radius = PLAYER_RADIUS # Радиус хитбокса
        self.speed = PLAYER_BASE_SPEED
        self.health = PLAYER_BASE_HEALTH
        self.max_health = PLAYER_BASE_HEALTH
        self.level = 1
        self.exp = 0
        self.exp_to_level = PLAYER_BASE_EXP_TO_LEVEL
        self.type = player_type  # "strong" или "fast"
        if player_type == "strong":
            self.damage = PLAYER_TYPE_STRONG_DAMAGE
            self.attack_speed = PLAYER_TYPE_STRONG_ATTACK_SPEED
            self.color = PLAYER_TYPE_STRONG_COLOR # Цвет для индикации, если нужен
        else:  # "fast"
            self.damage = PLAYER_TYPE_FAST_DAMAGE
            self.attack_speed = PLAYER_TYPE_FAST_ATTACK_SPEED
            self.color = PLAYER_TYPE_FAST_COLOR # Цвет для индикации, если нужен
        self.attack_cooldown = 0
        self.attack_range = PLAYER_ATTACK_RANGE
        self.bullets = []
        # Спрайт игрока
        self.original_sprite = player_sprite
        # Масштабируем спрайт под размер хитбокса (диаметр = радиус * 2)
        sprite_size = self.radius * 2
        self.original_sprite = pygame.transform.scale(self.original_sprite, (sprite_size, sprite_size))
        self.sprite = self.original_sprite.copy()
        self.angle = 0 # Угол поворота спрайта
    def move(self, dx, dy, obstacles):
        """Перемещает игрока, учитывая столкновения с препятствиями (скользящее столкновение)."""
        # Нормализация вектора движения, чтобы скорость была постоянной по диагонали
        magnitude = math.hypot(dx, dy)
        if magnitude > 0:
            dx_norm = dx / magnitude
            dy_norm = dy / magnitude
        else:
            dx_norm = 0
            dy_norm = 0
        # Попытка перемещения по оси X
        potential_x = self.x + dx_norm * self.speed
        temp_rect_x = pygame.Rect(potential_x - self.radius, self.y - self.radius,
                                 self.radius * 2, self.radius * 2)
        can_move_x = True
        for obstacle in obstacles:
            if temp_rect_x.colliderect(obstacle.rect):
                can_move_x = False
                break
        if can_move_x:
            self.x = potential_x
        # Попытка перемещения по оси Y (с учетом возможного изменения X)
        potential_y = self.y + dy_norm * self.speed
        temp_rect_y = pygame.Rect(self.x - self.radius, potential_y - self.radius,
                                 self.radius * 2, self.radius * 2)
        can_move_y = True
        for obstacle in obstacles:
            if temp_rect_y.colliderect(obstacle.rect):
                can_move_y = False
                break
        if can_move_y:
            self.y = potential_y
        # Ограничение движения в пределах экрана
        self.x = max(self.radius, min(WIDTH - self.radius, self.x))
        self.y = max(self.radius, min(HEIGHT - self.radius, self.y))
    def attack(self, enemies):
        """Игрок атакует ближайшего врага в радиусе атаки."""
        if self.attack_cooldown <= 0:
            closest_enemy = None
            min_dist = float('inf')
            for enemy in enemies:
                dist = math.hypot(enemy.x - self.x, enemy.y - self.y)
                if dist < self.attack_range and dist < min_dist:
                    min_dist = dist
                    closest_enemy = enemy
            if closest_enemy:
                angle = math.atan2(closest_enemy.y - self.y, closest_enemy.x - self.x)
                self.bullets.append(Bullet(self.x, self.y, angle, self.damage, self.color))
                self.attack_cooldown = 1 / self.attack_speed
                _play_sound(shoot_sound)
    def take_damage(self, amount):
        """Игрок получает урон."""
        self.health -= amount
        if self.health <= 0:
            self.health = 0
            return True # Игрок умер
        return False # Игрок жив
    def gain_exp(self, amount):
        """Игрок получает опыт и проверяет повышение уровня."""
        self.exp += amount
        if self.exp >= self.exp_to_level:
            self.level_up()
    def level_up(self):
        """Повышает уровень игрока, увеличивает характеристики."""
        self.level += 1
        self.exp -= self.exp_to_level
        self.exp_to_level = int(self.exp_to_level * PLAYER_EXP_TO_LEVEL_MULTIPLIER)
        self.damage += PLAYER_DAMAGE_LEVEL_UP_BONUS
        self.speed += PLAYER_SPEED_LEVEL_UP_BONUS
    def update(self, dt, obstacles, enemies): 
        """Обновляет состояние игрока и его снарядов."""
        if self.attack_cooldown > 0:
            self.attack_cooldown -= dt
        # Поворот спрайта игрока к ближайшему врагу
        closest_enemy = None
        min_dist = float('inf')
        for enemy in enemies:
            dist = math.hypot(enemy.x - self.x, enemy.y - self.y)
            if dist < min_dist: # Ищем ближайшего врага, независимо от attack_range
                min_dist = dist
                closest_enemy = enemy
        if closest_enemy:
            dx = closest_enemy.x - self.x
            dy = closest_enemy.y - self.y
            # Если спрайт по умолчанию смотрит вправо (0 градусов), то угол поворота:
            self.angle = -math.degrees(math.atan2(dy, dx))
            self.sprite = pygame.transform.rotate(self.original_sprite, self.angle)
        else:
            self.sprite = self.original_sprite.copy()
        for bullet in self.bullets[:]: # Итерируем по копии списка, чтобы безопасно удалять элементы
            bullet.update(dt)
            # Удаление снарядов, вышедших за пределы экрана
            if (bullet.x < 0 or bullet.x > WIDTH or
                bullet.y < 0 or bullet.y > HEIGHT):
                self.bullets.remove(bullet)
                continue
            # Проверка столкновений снарядов с препятствиями
            for obstacle in obstacles[:]:
                if obstacle.rect.collidepoint(bullet.x, bullet.y):
                    if bullet in self.bullets:
                        self.bullets.remove(bullet)
                    break
    def draw(self, surface):
        """Отрисовывает игрока и его полосу здоровья."""
        rotated_rect = self.sprite.get_rect(center=(int(self.x), int(self.y)))
        surface.blit(self.sprite, rotated_rect)
        # Отрисовка полосы здоровья
        health_ratio = self.health / self.max_health
        # Позиция полосы здоровья над спрайтом
        bar_width = self.radius * 2
        bar_height = 5
        bar_x = self.x - self.radius
        bar_y = self.y - self.radius - 10 # 10 пикселей над спрайтом/хитбоксом
        pygame.draw.rect(surface, RED, (bar_x, bar_y, bar_width, bar_height))
        pygame.draw.rect(surface, GREEN, (bar_x, bar_y, bar_width * health_ratio, bar_height))
# --- Класс Game ---
class Game:
    def __init__(self):
        self.state = "menu"
        self.settings_visible = False
        self.player = None
        self.enemies = []
        self.obstacles = []
        self.wave = 0
        self.max_waves = MAX_WAVES
        self.enemies_to_spawn = 0
        self.score = 0
        self.game_time = 0
        self.music_volume = MUSIC_VOLUME_DEFAULT
        self.sound_volume = SOUND_VOLUME_DEFAULT

        # Пути к музыкальным файлам
        self.menu_music_path = 'sounds/menu_music.mp3'
        self.game_music_path = 'sounds/game_music.mp3'
        self.current_music_playing = None # Отслеживает, какая музыка сейчас загружена и играет ("menu", "game", или None)

        # Инициализация шрифтов
        self.font = pygame.font.SysFont(FONT_NAME, FONT_SIZE_NORMAL)
        self.big_font = pygame.font.SysFont(FONT_NAME, FONT_SIZE_BIG)
        # Загрузка фоновых изображений и спрайтов
        self.background_image = load_image('assets/background.png', SCREEN_SIZE)
        self.game_background_image = load_image('assets/background_game.jpg', SCREEN_SIZE)
        self.title_image = load_image('assets/name.png', TITLE_IMAGE_SIZE)
        self.player_sprite_image = load_image('assets/hero.png')
        self.enemy_sprite_image = load_image('assets/enemy.png')
        # Инициализация кнопок главного меню (текстовые)
        # Передаем объекты шрифтов в конструкторы кнопок
        self.start_button = Button(WIDTH//2 - 100, HEIGHT//2 - 30, 200, 60, "Start", GREEN, (100, 255, 100), self.font)
        self.settings_button = Button(WIDTH//2 - 100, HEIGHT//2 + 40, 200, 60, "Settings", BLUE, (100, 100, 255), self.font)
        self.exit_button = Button(WIDTH//2 - 100, HEIGHT//2 + 110, 200, 60, "Exit", RED, (255, 100, 100), self.font)
        # Остальные текстовые кнопки (используются в других состояниях)
        self.strong_button = Button(WIDTH//2 - 210, HEIGHT//2 - 30, 200, 60, "Strong", BLUE, (100, 100, 255), self.font)
        self.fast_button = Button(WIDTH//2 + 10, HEIGHT//2 - 30, 200, 60, "Fast", GREEN, (100, 255, 100), self.font)
        self.back_button = Button(WIDTH//2 - 100, HEIGHT//2 + 110, 200, 60, "Back", RED, (255, 100, 100), self.font)
        self.resume_button = Button(WIDTH//2 - 100, HEIGHT//2 - 60, 200, 60, "Resume", GREEN, (100, 255, 100), self.font)
        self.menu_button = Button(WIDTH//2 - 100, HEIGHT//2 + 40, 200, 60, "Main Menu", BLUE, (100, 100, 255), self.font)
        self.restart_button = Button(WIDTH//2 - 100, HEIGHT//2 - 20, 200, 60, "Restart", GREEN, (100, 255, 100), self.font)
        self.music_plus = Button(WIDTH//2 + 50, HEIGHT//2 - 45, 40, 40, "+", GREEN, (100, 255, 100), self.font)
        self.music_minus = Button(WIDTH//2 - 90, HEIGHT//2 - 45, 40, 40, "-", RED, (255, 100, 100), self.font)
        self.sound_plus = Button(WIDTH//2 + 50, HEIGHT//2 + 30, 40, 40, "+", GREEN, (100, 255, 100), self.font)
        self.sound_minus = Button(WIDTH//2 - 90, HEIGHT//2 + 30, 40, 40, "-", RED, (255, 100, 100), self.font)
        self.back_settings = Button(WIDTH//2 - 100, HEIGHT//2 + 100, 200, 50, "Back", BLUE, (100, 100, 255), self.font)
        
        # Установка начальной громкости музыки
        if mixer_available:
            pygame.mixer.music.set_volume(self.music_volume)
            self._play_music_for_state() # Запускаем начальную музыку (меню)

    def _play_music_for_state(self):
        """Управляет воспроизведением фоновой музыки в зависимости от состояния игры."""
        if not mixer_available:
            return

        if self.state == "menu" or self.state == "character_select":
            if self.current_music_playing != "menu":
                try:
                    pygame.mixer.music.load(self.menu_music_path)
                    pygame.mixer.music.set_volume(self.music_volume)
                    pygame.mixer.music.play(-1) # -1 означает зацикливание
                    self.current_music_playing = "menu"
                except pygame.error as e:
                    print(f"Error loading menu music: {e}")
                    self.current_music_playing = None
        elif self.state == "playing":
            if self.current_music_playing != "game":
                try:
                    pygame.mixer.music.load(self.game_music_path)
                    pygame.mixer.music.set_volume(self.music_volume)
                    pygame.mixer.music.play(-1)
                    self.current_music_playing = "game"
                except pygame.error as e:
                    print(f"Error loading game music: {e}")
                    self.current_music_playing = None
        # Для состояний "paused", "game_over", "game_won" музыка должна продолжать играть
        # то, что играло до перехода в эти состояния. Явных изменений здесь не требуется.

    def start_game(self, player_type):
        """Начинает новую игру с выбранным типом игрока."""
        self.state = "playing"
        # Передаем спрайт игрока в конструктор Player
        self.player = Player(WIDTH//2, HEIGHT//2, player_type, self.player_sprite_image)
        self.enemies = []
        self.obstacles = self.generate_obstacles(OBSTACLE_COUNT)
        self.wave = 0
        self.score = 0
        self.game_time = 0
        self.start_next_wave()
        self._play_music_for_state() # Убеждаемся, что игровая музыка начинается

    def generate_obstacles(self, count):
        """Генерирует случайные препятствия, избегая области вокруг игрока."""
        obstacles = []
        for _ in range(count):
            width = random.randint(OBSTACLE_MIN_SIZE, OBSTACLE_MAX_SIZE)
            height = random.randint(OBSTACLE_MIN_SIZE, OBSTACLE_MAX_SIZE)
            # Генерируем позицию, пока она не будет достаточно далеко от центра
            while True:
                x = random.randint(0, WIDTH - width)
                y = random.randint(0, HEIGHT - height)
                # Проверяем расстояние от центра препятствия до центра экрана
                # Используем центр препятствия для проверки безопасной зоны
                if math.hypot(x + width/2 - WIDTH/2, y + height/2 - HEIGHT/2) >= OBSTACLE_PLAYER_SAFE_ZONE:
                    break
            obstacles.append(Obstacle(x, y, width, height))
        return obstacles
    def start_next_wave(self):
        """Начинает следующую волну врагов."""
        if self.wave < self.max_waves:
            self.wave += 1
            self.enemies_to_spawn = WAVE_BASE_ENEMIES + self.wave * WAVE_ENEMIES_PER_WAVE
        else:
            self.state = "game_won"
    def spawn_enemy(self):
        """Появляет одного врага за пределами экрана."""
        if self.enemies_to_spawn > 0:
            side = random.randint(0, 3) # 0: top, 1: right, 2: bottom, 3: left
            if side == 0:
                x = random.randint(0, WIDTH)
                y = -ENEMY_SPAWN_OFFSET
            elif side == 1:
                x = WIDTH + ENEMY_SPAWN_OFFSET
                y = random.randint(0, HEIGHT)
            elif side == 2:
                x = random.randint(0, WIDTH)
                y = HEIGHT + ENEMY_SPAWN_OFFSET
            else:
                x = -ENEMY_SPAWN_OFFSET
                y = random.randint(0, HEIGHT)
            # Передаем спрайт врага в конструктор Enemy
            self.enemies.append(Enemy(x, y, "melee", self.enemy_sprite_image))
            self.enemies_to_spawn -= 1
    def update(self, dt):
        """Обновляет состояние игры в зависимости от текущего состояния."""
        if self.state == "playing":
            self.game_time += dt
            # Случайное появление врагов
            if random.random() < ENEMY_SPAWN_CHANCE and self.enemies_to_spawn > 0:
                self.spawn_enemy()
            # Переход к следующей волне, если все враги текущей волны уничтожены
            if self.enemies_to_spawn == 0 and len(self.enemies) == 0:
                self.start_next_wave()
            # Обработка ввода игрока
            keys = pygame.key.get_pressed()
            dx = keys[pygame.K_RIGHT] - keys[pygame.K_LEFT]
            dy = keys[pygame.K_DOWN] - keys[pygame.K_UP]
            self.player.move(dx, dy, self.obstacles)
            # Атака игрока
            self.player.attack(self.enemies)
            # Обновление игрока и его снарядов (передаем enemies для поворота спрайта игрока)
            self.player.update(dt, self.obstacles, self.enemies)
            # Обновление врагов и проверка столкновений с игроком/снарядами
            for enemy in self.enemies[:]: # Итерируем по копии списка
                player_died = enemy.update(dt, self.player, self.obstacles)
                if player_died:
                    self.state = "game_over"
                    break # Выходим из цикла, так как игра окончена
                for bullet in self.player.bullets[:]: # Итерируем по копии списка снарядов игрока
                    # Проверка столкновения снаряда с врагом
                    # Используем расстояние между центрами кругов (снаряд и враг)
                    if math.hypot(bullet.x - enemy.x, bullet.y - enemy.y) < bullet.radius + enemy.radius:
                        if enemy.take_damage(bullet.damage):
                            _play_sound(hit_sound) # Звук попадания
                            self.player.gain_exp(PLAYER_EXP_REWARD_ENEMY)
                            self.score += PLAYER_SCORE_REWARD_ENEMY
                            self.enemies.remove(enemy)
                        if bullet in self.player.bullets: # Проверяем, что снаряд еще в списке
                            self.player.bullets.remove(bullet)
                        break # Снаряд попал, переходим к следующему врагу
    def _draw_game_stats(self, surface, offset_y=0):
        """Вспомогательный метод для отрисовки статистики игры."""
        stats = [
            f"Wave reached: {self.wave}/{self.max_waves}",
            f"Score: {self.score}",
            f"Time survived: {int(self.game_time)}s",
            f"Level reached: {self.player.level}" if self.player else "Level reached: N/A"
        ]
        for i, stat in enumerate(stats):
            text = self.font.render(stat, True, WHITE) # Используем self.font
            surface.blit(text, (WIDTH//2 - text.get_width()//2, HEIGHT//2 + offset_y + i * 40))
    def draw_settings(self):
        """Отрисовывает меню настроек."""
        title = self.big_font.render("Settings", True, WHITE) # Используем self.big_font
        screen.blit(title, (WIDTH//2 - title.get_width()//2, HEIGHT//4))
        music_text = self.font.render(f"Music Volume: {int(self.music_volume * 100)}%", True, WHITE) # Используем self.font
        screen.blit(music_text, (WIDTH//2 - music_text.get_width()//2, HEIGHT//2 - 70))
        sound_text = self.font.render(f"Sound Volume: {int(self.sound_volume * 100)}%", True, WHITE) # Используем self.font
        screen.blit(sound_text, (WIDTH//2 - sound_text.get_width()//2, HEIGHT//2 ))
        mouse_pos = pygame.mouse.get_pos()
        self.music_minus.check_hover(mouse_pos)
        self.music_plus.check_hover(mouse_pos)
        self.sound_minus.check_hover(mouse_pos)
        self.sound_plus.check_hover(mouse_pos)
        self.back_settings.check_hover(mouse_pos)
        self.music_minus.draw(screen)
        self.music_plus.draw(screen)
        self.sound_minus.draw(screen)
        self.sound_plus.draw(screen)
        self.back_settings.draw(screen)
    def draw(self):
        """Отрисовывает все элементы игры в зависимости от текущего состояния."""
        screen.fill(BLACK) # Заливаем фон черным по умолчанию
        # Отрисовка соответствующего фона в зависимости от состояния игры
        if self.state == "playing":
            screen.blit(self.game_background_image, (0, 0))
        else: # Для меню, выбора персонажа, паузы, настроек, конца игры, победы
            screen.blit(self.background_image, (0, 0))
        # Далее отрисовываем элементы UI и игровые объекты поверх выбранного фона
        if self.settings_visible:
            # _draw_overlay(screen) # Оверлей убран, чтобы фон был полностью виден
            self.draw_settings()
        elif self.state == "menu":
            title_rect = self.title_image.get_rect(center=(WIDTH//2, HEIGHT//4))
            screen.blit(self.title_image, title_rect)
            mouse_pos = pygame.mouse.get_pos()
            self.start_button.check_hover(mouse_pos)
            self.settings_button.check_hover(mouse_pos)
            self.exit_button.check_hover(mouse_pos)
            self.start_button.draw(screen)
            self.settings_button.draw(screen)
            self.exit_button.draw(screen)
        elif self.state == "character_select":
            # _draw_overlay(screen) # Оверлей убран, чтобы фон был полностью виден
            title = self.font.render("Select Character", True, WHITE)
            screen.blit(title, (WIDTH//2 - title.get_width()//2, HEIGHT//4))
            mouse_pos = pygame.mouse.get_pos()
            self.strong_button.check_hover(mouse_pos)
            self.fast_button.check_hover(mouse_pos)
            self.back_button.check_hover(mouse_pos)
            self.strong_button.draw(screen)
            self.fast_button.draw(screen)
            self.back_button.draw(screen)
            strong_desc = self.font.render("High damage, slow attack", True, BLUE)
            fast_desc = self.font.render("Low damage fast attack", True, GREEN)
            screen.blit(strong_desc, (WIDTH//2 - 260, HEIGHT//2 + 40))
            screen.blit(fast_desc, (WIDTH//2 + 50, HEIGHT//2 + 40))
        elif self.state == "playing":
            for obstacle in self.obstacles:
                obstacle.draw(screen)
            self.player.draw(screen)
            for enemy in self.enemies:
                enemy.draw(screen)
            # Отрисовка HUD
            health_text = self.font.render(f"HP: {self.player.health}/{self.player.max_health}", True, WHITE)
            level_text = self.font.render(f"Level: {self.player.level}", True, WHITE)
            wave_text = self.font.render(f"Wave: {self.wave}/{self.max_waves}", True, WHITE)
            score_text = self.font.render(f"Score: {self.score}", True, WHITE)
            screen.blit(health_text, (10, 10))
            screen.blit(level_text, (10, 50))
            screen.blit(wave_text, (10, 90))
            screen.blit(score_text, (10, 130))
        elif self.state == "paused":
            _draw_overlay(screen)
            title = self.font.render("Game Paused", True, WHITE)
            screen.blit(title, (WIDTH//2 - title.get_width()//2, HEIGHT//4))
            mouse_pos = pygame.mouse.get_pos()
            self.resume_button.check_hover(mouse_pos)
            self.menu_button.check_hover(mouse_pos)
            self.resume_button.draw(screen)
            self.menu_button.draw(screen)
        elif self.state == "game_over":
            _draw_overlay(screen)
            title = self.big_font.render("Game Over", True, RED)
            screen.blit(title, (WIDTH//2 - title.get_width()//2, HEIGHT//4))
            self._draw_game_stats(screen, offset_y=HEIGHT//4) # Используем смещение для статистики
            mouse_pos = pygame.mouse.get_pos()
            self.restart_button.check_hover(mouse_pos)
            self.menu_button.check_hover(mouse_pos)
            self.restart_button.draw(screen)
            self.menu_button.draw(screen)
        elif self.state == "game_won":
            _draw_overlay(screen)
            title = self.big_font.render("Victory!", True, GREEN)
            screen.blit(title, (WIDTH//2 - title.get_width()//2, HEIGHT//4))
            self._draw_game_stats(screen, offset_y=HEIGHT//4) # Используем смещение для статистики
            mouse_pos = pygame.mouse.get_pos()
            self.restart_button.check_hover(mouse_pos)
            self.menu_button.check_hover(mouse_pos)
            self.restart_button.draw(screen)
            self.menu_button.draw(screen)
        pygame.display.flip()
    def handle_events(self):
        """Обрабатывает события ввода пользователя."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    if self.state == "playing":
                        self.state = "paused"
                    elif self.state == "paused":
                        self.state = "playing"
                    elif self.settings_visible:
                        self.settings_visible = False
                    self._play_music_for_state() # Переоцениваем состояние музыки при паузе/снятии с паузы/выходе из настроек
            if event.type == pygame.MOUSEBUTTONDOWN:
                mouse_pos = pygame.mouse.get_pos()
                if self.settings_visible:
                    if self.music_plus.is_clicked(mouse_pos, event):
                        self.music_volume = min(1.0, self.music_volume + 0.1)
                        _play_sound(button_sound)
                        if mixer_available:
                            pygame.mixer.music.set_volume(self.music_volume)
                    elif self.music_minus.is_clicked(mouse_pos, event):
                        self.music_volume = max(0.0, self.music_volume - 0.1)
                        _play_sound(button_sound)
                        if mixer_available:
                            pygame.mixer.music.set_volume(self.music_volume)
                    elif self.sound_plus.is_clicked(mouse_pos, event):
                        self.sound_volume = min(1.0, self.sound_volume + 0.1)
                        # Обновляем громкость всех звуков, которые используют SOUND_VOLUME_DEFAULT
                        # Они глобальные, поэтому нужно обновить их напрямую
                        if button_sound: button_sound.set_volume(BUTTON_SOUND_VOLUME * self.sound_volume / SOUND_VOLUME_DEFAULT)
                        if shoot_sound: shoot_sound.set_volume(SHOOT_SOUND_VOLUME * self.sound_volume / SOUND_VOLUME_DEFAULT)
                        if hit_sound: hit_sound.set_volume(HIT_SOUND_VOLUME * self.sound_volume / SOUND_VOLUME_DEFAULT)
                        _play_sound(button_sound)
                    elif self.sound_minus.is_clicked(mouse_pos, event):
                        self.sound_volume = max(0.0, self.sound_volume - 0.1)
                        if button_sound: button_sound.set_volume(BUTTON_SOUND_VOLUME * self.sound_volume / SOUND_VOLUME_DEFAULT)
                        if shoot_sound: shoot_sound.set_volume(SHOOT_SOUND_VOLUME * self.sound_volume / SOUND_VOLUME_DEFAULT)
                        if hit_sound: hit_sound.set_volume(HIT_SOUND_VOLUME * self.sound_volume / SOUND_VOLUME_DEFAULT)
                        _play_sound(button_sound)
                    elif self.back_settings.is_clicked(mouse_pos, event):
                        self.settings_visible = False
                        _play_sound(button_sound)
                        self._play_music_for_state() # Переоцениваем состояние музыки после выхода из настроек
                elif self.state == "menu":
                    # Обработка кликов для текстовых кнопок
                    if self.start_button.is_clicked(mouse_pos, event):
                        _play_sound(button_sound)
                        self.state = "character_select"
                        self._play_music_for_state() # Убеждаемся, что музыка меню продолжает играть или начинается
                    elif self.settings_button.is_clicked(mouse_pos, event):
                        _play_sound(button_sound)
                        self.settings_visible = True
                    elif self.exit_button.is_clicked(mouse_pos, event):
                        return False
                elif self.state == "character_select":
                    if self.strong_button.is_clicked(mouse_pos, event):
                        _play_sound(button_sound)
                        self.start_game("strong") # start_game уже вызывает _play_music_for_state
                    elif self.fast_button.is_clicked(mouse_pos, event):
                        _play_sound(button_sound)
                        self.start_game("fast") # start_game уже вызывает _play_music_for_state
                    elif self.back_button.is_clicked(mouse_pos, event):
                        _play_sound(button_sound)
                        self.state = "menu"
                        self._play_music_for_state() # Убеждаемся, что музыка меню начинается/продолжается
                elif self.state == "paused":
                    if self.resume_button.is_clicked(mouse_pos, event):
                        _play_sound(button_sound)
                        self.state = "playing"
                        self._play_music_for_state() # Возобновляем игровую музыку
                    elif self.menu_button.is_clicked(mouse_pos, event):
                        _play_sound(button_sound)
                        self.state = "menu"
                        self._play_music_for_state() # Возвращаемся к музыке меню
                elif self.state == "game_over" or self.state == "game_won":
                    if self.restart_button.is_clicked(mouse_pos, event):
                        _play_sound(button_sound)
                        self.start_game(self.player.type) # start_game уже вызывает _play_music_for_state
                    elif self.menu_button.is_clicked(mouse_pos, event):
                        _play_sound(button_sound)
                        self.state = "menu"
                        self._play_music_for_state() # Возвращаемся к музыке меню
        return True
def main():
    clock = pygame.time.Clock()
    game = Game()
    running = True
    while running:
        dt = clock.tick(60) / 1000.0 # Время кадра в секундах
        running = game.handle_events()
        game.update(dt)
        game.draw()
    pygame.quit()
    sys.exit()
if __name__ == "__main__":
    main()
