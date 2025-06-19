import pygame

GRAY = (100, 100, 100)
BLACK = (0, 0, 0)


class Obstacle:
    def __init__(self, x, y, width, height):
        self.rect = pygame.Rect(x, y, width, height)
        self.health = 30 
        
        
    def draw(self, surface):
        pygame.draw.rect(surface, GRAY, self.rect)
        pygame.draw.rect(surface, BLACK, self.rect, 2)
        