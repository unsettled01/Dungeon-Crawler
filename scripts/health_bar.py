import pygame

class HealthBar():
    def __init__(self, x, y, w, h, max_hp):
        self.x = x
        self.y = y
        self.w = w
        self.h = h
        self.hp = max_hp
        self.max_hp = max_hp

    def draw(self, surface):
        # draws the health bar using 3 rects. when health goes down green bar goes down by adjusting health ratio
        ratio = self.hp / self.max_hp
        pygame.draw.rect(surface, 'black', (self.x - 1, self.y -1 , self.w + 2, self.h + 2))
        pygame.draw.rect(surface, 'red', (self.x, self.y, self.w, self.h))
        pygame.draw.rect(surface, 'green', (self.x, self.y, self.w * ratio, self.h))
