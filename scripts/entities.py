import math
import random

import pygame

from python.MyPygame.scripts.spark import Spark

# bass class for physics entities
class PhysicsEntity:
    def __init__(self, game, e_type, pos, size):
        self.game = game
        self.type = e_type
        self.pos = list(pos)
        self.size = size
        self.velocity = [0, 0]
        self.collisions = {'up': False, 'down': False, 'right': False, 'left': False}

        self.action = ''
        self.anim_offset = (-3, -3)
        self.flip = False
        self.set_action('idle')

    # draws a rect on the entity
    def rect(self):
        return pygame.Rect(self.pos[0], self.pos[1], self.size[0], self.size[1])

    # determines entities action
    def set_action(self, action):
        if action != self.action:
            self.action = action
            self.animation = self.game.assets[self.type + '/' + self.action].copy()

    # updates entity based on position and collisions
    def update(self, tilemap, movement=(0, 0)):
        self.collisions = {'up': False, 'down': False, 'right': False, 'left': False}

        frame_movement = (movement[0] + self.velocity[0], movement[1] + self.velocity[1])

        self.pos[0] += frame_movement[0]
        entity_rect = self.rect()
        for rect in tilemap.physics_rects_around(self.pos):
            if entity_rect.colliderect(rect):
                if frame_movement[0] > 0:
                    entity_rect.right = rect.left
                    self.collisions['right'] = True
                if frame_movement[0] < 0:
                    entity_rect.left = rect.right
                    self.collisions['left'] = True
                self.pos[0] = entity_rect.x

        self.pos[1] += frame_movement[1]
        entity_rect = self.rect()
        for rect in tilemap.physics_rects_around(self.pos):
            if entity_rect.colliderect(rect):
                if frame_movement[1] > 0:
                    entity_rect.bottom = rect.top
                    self.collisions['down'] = True
                if frame_movement[1] < 0:
                    entity_rect.top = rect.bottom
                    self.collisions['up'] = True
                self.pos[1] = entity_rect.y

        if movement[0] > 0:
            self.flip = False
        if movement[0] < 0:
            self.flip = True

        self.animation.update()

    # renders entity on screen
    def render(self, surf, offset=(0, 0)):
        surf.blit(pygame.transform.flip(self.animation.img(), self.flip, False),
                  (self.pos[0] - offset[0] + self.anim_offset[0], self.pos[1] - offset[1] + self.anim_offset[1]))

#enemy
class Enemy(PhysicsEntity):
    def __init__(self, game, pos, size):
        super().__init__(game, 'enemy', pos, size)

        self.walking = 0
        self.vertical_flip = False
        self.movement_direction = 'x'


    def update(self, tilemap, movement=(0, 0)):
        if self.walking:
            # handles flipping asset
            if (self.collisions['right'] or self.collisions['left']):
                self.flip = not self.flip
            if (self.collisions['up'] or self.collisions['down']):
                self.vertical_flip = not self.vertical_flip

            # enemy able to walk in x or y or x,y axis
            if self.movement_direction == 'x':
                movement = (movement[0] - 0.4 if self.flip else movement[0] + 0.4, movement[1])
            if self.movement_direction == 'y':
                movement = (movement[1] - 0.4 if self.flip else movement[1] + 0.4, movement[0])
            else:
                movement = (
                    movement[0] - 0.4 if self.flip else movement[0] + 0.4,
                    movement[1] - 0.2 if self.vertical_flip else movement[1] + 0.2
            )
            self.walking = max(0, self.walking - 1)
            if not self.walking:
                # calculates player position relative to enemy position
                dis = (self.game.player.pos[0] - self.pos[0], self.game.player.pos[1] - self.pos[1])
                if (abs(dis[0]) < 80 and abs(dis[1]) < 80):

                    distance = (dis[0] ** 2 + dis[1] ** 2) ** 0.5

                    if distance != 0:
                        # shoots at player from enemy
                        direction = (dis[0] / distance, dis[1] / distance)

                        projectile_speed = 2

                        self.game.sfx['enemy_shoot'].play(0)
                        self.game.enemy_projectiles.append([[self.rect().centerx, self.rect().centery], direction[0] * projectile_speed, direction[1] * projectile_speed, 0])

                        projectile_pos = self.game.enemy_projectiles[-1][0]

                        shooting_angle = math.atan2(direction[1], direction[0])

                        for i in range(4):
                            angle_offset = shooting_angle + (random.random() - 0.5) * 1
                            speed_offset = 2 + random.random()
                            self.game.sparks.append(Spark(projectile_pos, angle_offset, speed_offset))
        elif random.random() < 0.01:
            self.walking = random.randint(30,120)
            self.movement_direction = random.choice(['x', 'y', 'both'])

        super().update(tilemap, movement=movement)

        if movement[0] != 0 or movement[1] != 0:
            self.set_action('run')
        else:
            self.set_action('idle')

    # renders enemy and gun
    def render(self, surf, offset=(0, 0)):
        super().render(surf, offset=offset)

        if self.flip:
            surf.blit(pygame.transform.flip(self.game.assets['gun'], True, False),(self.rect().centerx - 4 - self.game.assets['gun'].get_width() - offset[0], self.rect().centery - offset[1]))
        else:
            surf.blit(self.game.assets['gun'], (self.rect().centerx + 4 - offset[0], self.rect().centery - offset[1]))


# player
class Player(PhysicsEntity):
    def __init__(self, game, pos, size):
        super().__init__(game, 'player', pos, size)
        self.health = 10

    def update(self, tilemap, movement=(0, 0)):
        super().update(tilemap, movement=movement)


        if movement[0] != 0 :
            self.set_action('run')
        elif movement[1] != 0:
            self.set_action('run')
        else:
            self.set_action('idle')

    # renders player and gun
    def render(self, surf, offset=(0, 0)):
        super().render(surf, offset=offset)

        if self.flip:
            surf.blit(pygame.transform.flip(self.game.assets['gun'], True, False),(self.rect().centerx - 4 - self.game.assets['gun'].get_width() - offset[0], self.rect().centery - offset[1]))
        else:
            surf.blit(self.game.assets['gun'], (self.rect().centerx + 4 - offset[0], self.rect().centery - offset[1]))

    # determines if projectile shoots left or right depending on flip
    def shoot(self, offset=(0, 0)):
        if self.flip:
            self.game.sfx['player_shoot'].play(0)
            self.game.projectiles.append([[self.rect().centerx - 7, self.rect().centery], -2, 0])
            for i in range(4):
                self.game.sparks.append(Spark(self.game.projectiles[-1][0], random.random() - 0.5 + math.pi, 2 + random.random()))
        if not self.flip:
            self.game.sfx['player_shoot'].play(0)
            self.game.projectiles.append([[self.rect().centerx + 7, self.rect().centery], 2, 0])
            for i in range(4):
                self.game.sparks.append(Spark(self.game.projectiles[-1][0], random.random() - 0.5, 2 + random.random()))
