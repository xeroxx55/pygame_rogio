import math 
import pygame


class Bullet:
    def __init__(self, x, y, angle, damage, color):
        self.x = x
        self.y = y
        self.speed = 300
        self.damage = damage
        self.color = color
        self.radius = 5
        self.dx = math.cos(angle) * self.speed
        self.dy = math.sin(angle) * self.speed
        
    def update(self, dt):
        self.x += self.dx * dt
        self.y += self.dy * dt
        
    def draw(self, surface):
        pygame.draw.circle(surface, self.color, (int(self.x), int(self.y)), self.radius)
