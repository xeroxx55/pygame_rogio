import pygame
import math

RED = (255, 0, 0)
GREEN = (0, 255, 0)

class Enemy:
    # Добавлен enemy_sprite параметр для инициализации спрайта
    def __init__(self, x, y, enemy_type, enemy_sprite):
        self.x = x
        self.y = y
        self.type = enemy_type
        if enemy_type == "melee":
            self.radius = 15 # Это радиус хитбокса
            self.speed = 50
            self.health = 50
            self.initial_health = 50 # Сохраняем начальное здоровье для корректного отображения полосы здоровья
            self.damage = 10
            self.attack_cooldown = 1
            self.current_cooldown = 0
            self.color = RED # Этот цвет используется для полосы здоровья, а не для основного тела, если используется спрайт
        else:
            pass # Потенциально другие типы врагов
        
        # Обработка спрайта
        self.original_sprite = enemy_sprite # Передается из Game
        # Масштабируем спрайт под размер хитбокса (диаметр = радиус * 2)
        sprite_size = self.radius * 2
        self.original_sprite = pygame.transform.scale(self.original_sprite, (sprite_size, sprite_size))
        self.sprite = self.original_sprite.copy()
        self.angle = 0 # Угол для поворота спрайта

    def update(self, dt, player, obstacles):
        # Вычисляем направление к игроку
        dx = player.x - self.x
        dy = player.y - self.y
        dist = math.hypot(dx, dy)

        # Нормализуем вектор направления
        if dist != 0:
            dx_norm = dx / dist
            dy_norm = dy / dist
        else:
            dx_norm = 0
            dy_norm = 0

        # Вычисляем потенциальную новую позицию
        potential_new_x = self.x + dx_norm * self.speed * dt
        potential_new_y = self.y + dy_norm * self.speed * dt

        # --- Улучшенное обнаружение и разрешение скользящих столкновений ---
        # Этот алгоритм позволяет врагу "скользить" вдоль препятствий,
        # но не реализует полноценный поиск кратчайшего пути вокруг них.
        # Для поиска кратчайшего пути требуется более сложный алгоритм (например, A*).
        
        # Проверяем движение по оси X
        test_rect_x = pygame.Rect(potential_new_x - self.radius, self.y - self.radius,
                                  self.radius * 2, self.radius * 2)
        can_move_x = True
        for obstacle in obstacles:
            if test_rect_x.colliderect(obstacle.rect):
                can_move_x = False
                break
        if can_move_x:
            self.x = potential_new_x

        # Проверяем движение по оси Y (с учетом потенциально обновленной позиции по X)
        test_rect_y = pygame.Rect(self.x - self.radius, potential_new_y - self.radius,
                                  self.radius * 2, self.radius * 2)
        can_move_y = True
        for obstacle in obstacles:
            if test_rect_y.colliderect(obstacle.rect):
                can_move_y = False
                break
        if can_move_y:
            self.y = potential_new_y
        
        # --- Поворот спрайта ---
        # Вычисляем угол к игроку для поворота спрайта
        # atan2(dy, dx) дает угол в радианах от положительной оси X, против часовой стрелки.
        # pygame.transform.rotate вращает против часовой стрелки.
        # Если спрайт по умолчанию смотрит вправо (0 градусов), то угол поворота:
        self.angle = -math.degrees(math.atan2(dy, dx)) # Угол для поворота
        self.sprite = pygame.transform.rotate(self.original_sprite, self.angle)

        # --- Логика атаки ---
        if self.current_cooldown > 0:
            self.current_cooldown -= dt
        else:
            dist_to_player = math.hypot(player.x - self.x, player.y - self.y)
            # Проверяем, достаточно ли близко враг, чтобы атаковать игрока
            # Число '5' здесь - это магическое число для допуска к дальности атаки. Можно сделать константой.
            if dist_to_player < self.radius + player.radius + 5:
                if player.take_damage(self.damage):
                    return True # Игрок умер
                self.current_cooldown = self.attack_cooldown
        return False # Игрок все еще жив

    def take_damage(self, amount):
        self.health -= amount
        return self.health <= 0

    def draw(self, surface):
        # Отрисовываем повернутый спрайт
        rotated_rect = self.sprite.get_rect(center=(int(self.x), int(self.y)))
        surface.blit(self.sprite, rotated_rect)

        # Отрисовываем полосу здоровья
        # Используем initial_health для знаменателя, чтобы получить правильное соотношение
        if self.health < self.initial_health: # Отрисовываем только если здоровье не полное
            health_ratio = self.health / self.initial_health
            # Позиция полосы здоровья относительно центра врага
            bar_width = self.radius * 2
            bar_height = 4
            bar_x = self.x - self.radius
            bar_y = self.y - self.radius - 8 # 8 пикселей над спрайтом/хитбоксом
            
            pygame.draw.rect(surface, RED, (bar_x, bar_y, bar_width, bar_height))
            pygame.draw.rect(surface, GREEN, (bar_x, bar_y, bar_width * health_ratio, bar_height))
