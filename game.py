import math
import os
import random
import time
import pygame
import sys

from python.MyPygame.scripts import health_bar
from python.MyPygame.scripts.health_bar import HealthBar
from scripts.spark import Spark
from scripts.utilities import load_image, load_images, Animation
from scripts.entities import Player, Enemy
from scripts.tilemap import Tilemap

class Game:
    def __init__(self):
        # initializing screen display and other key components
        pygame.init()

        pygame.display.set_caption('Dungeons & Dungeons')

        scr_res = (720, 640)
        self.screen = pygame.display.set_mode(scr_res)

        self.display = pygame.Surface((100,100))

        self.clock = pygame.time.Clock()

        self.movement = [False, False, False, False]

        # initializing assets
        self.assets = {
            'decor': load_images('tiles/decor'),
            'grass': load_images('tiles/grass'),
            'large_decor': load_images('tiles/large_decor'),
            'stone': load_images('tiles/stone'),
            'player': load_image('entities/player.png'),
            'enemy/idle': Animation(load_images('entities/enemy/idle'), img_dur=6),
            'enemy/run': Animation(load_images('entities/enemy/run'), img_dur=4),
            'player/idle': Animation(load_images('entities/player/idle'), img_dur = 6),
            'player/run': Animation(load_images('entities/player/run'), img_dur = 4),
            'gun': load_image('gun.png'),
            'projectile': load_image('projectile.png'),
        }

        # initializing audio
        self.sfx = {
            'player_shoot': pygame.mixer.Sound('data/sfx/player_shoot.wav'),
            'enemy_shoot': pygame.mixer.Sound('data/sfx/enemy_shoot.wav'),
            'player_death': pygame.mixer.Sound('data/sfx/player_death.wav'),
            'enemy_death': pygame.mixer.Sound('data/sfx/enemy_death.wav'),
        }

        # setting audio volume
        self.sfx['player_shoot'].set_volume(0.4)
        self.sfx['player_death'].set_volume(0.8)
        self.sfx['enemy_shoot'].set_volume(0.4)
        self.sfx['enemy_death'].set_volume(0.8)


        # initializing player
        self.player = Player(self, (50,50), (8, 15))

        # initializing tilemap
        self.tilemap = Tilemap(self, tile_size=16)

        # keeps track of level
        self.level = 0
        self.load_level(self.level)

    # load level method loads everything outside of run function and handles loading different levels
    def load_level(self, map_id):
        self.tilemap.load('data/maps/' + str(map_id) + '.json')
        self.enemies = []
        self.trap_doors = []

        # draws a collision area on the trap door on the map by extracting the position of decor 3
        for decor in self.tilemap.extract([('decor', 0), ('decor', 1), ('decor', 2), ('decor', 3)]):
            if decor['variant'] == 3:
                trap_door_rect = pygame.Rect(decor['pos'][0], decor['pos'][1], 16, 16)
                self.trap_doors.append(trap_door_rect)

        # spawns the players and the enemies
        for spawner in self.tilemap.extract([('spawners', 0), ('spawners', 1)]):
            if spawner['variant'] == 0:
                self.player.pos = spawner['pos']
            else:
                self.enemies.append(Enemy(self, spawner['pos'], (8, 15)))

        # inititalizing lists to keep track of objects
        self.projectiles = []
        self.enemy_projectiles = []
        self.sparks = []
        self.font = pygame.font.SysFont('times', 15)
        self.scroll = [0, 0]
        self.dead = 0
        self.health_bar = HealthBar(40, 95, 30, 3, 10)


    def run(self):
        # starts the music
        pygame.mixer.music.load('data/musica.wav')
        pygame.mixer.music.set_volume(0.5)
        pygame.mixer.music.play(-1)
        while True:
            self.display.fill('black')

            # if the player rect collides with trap door transition to next level
            for trap_door in self.trap_doors:
                if self.player.rect().colliderect(trap_door):
                    self.screen.fill((0,0,0))
                    pygame.display.update()
                    time.sleep(0.5)
                    self.player.health = 10
                    self.level = min(self.level + 1, len(os.listdir('data/maps')) - 1)
                    self.load_level(self.level)

            # scroll logic
            scroll_inc = 30
            self.scroll[0] += (self.player.rect().centerx - self.display.get_width() / 2 - self.scroll[0]) / scroll_inc
            self.scroll[1] += (self.player.rect().centery - self.display.get_height() / 2 - self.scroll[1]) / scroll_inc
            render_scroll = (int(self.scroll[0]), int(self.scroll[1]))

            self.tilemap.render(self.display, offset=render_scroll)

            #renders the enemies
            for enemy in self.enemies.copy():
                kill = enemy.update(self.tilemap, (0,0))
                enemy.render(self.display, offset=render_scroll)
                if kill:
                    self.enemies.remove(enemy)

            # handles 8 directional movement
            x_move = self.movement[1] - self.movement[0]
            y_move = self.movement[3] - self.movement[2]

            # renders player and uses 8d movement to update position
            if not self.dead:
                self.player.update(self.tilemap,(x_move, y_move))
                self.player.render(self.display, offset=render_scroll)

            # handles enemies shooting
            for enemy_projectile in self.enemy_projectiles.copy():
                enemy_projectile[0][0] += enemy_projectile[1]
                enemy_projectile[0][1] += enemy_projectile[2]
                enemy_projectile[3] += 1

                # renders projectile
                img = self.assets['projectile']
                self.display.blit(img, (enemy_projectile[0][0] - img.get_width() / 2 - render_scroll[0], enemy_projectile[0][1] - img.get_height() / 2 - render_scroll[1]))

                # if the projectile hits a wall make sparks come out opposite to the direction the projectile hit
                if self.tilemap.solid_check(enemy_projectile[0]):
                    self.enemy_projectiles.remove(enemy_projectile)

                    vel_x = enemy_projectile[1]
                    vel_y = enemy_projectile[2]

                    angle = math.atan2(vel_y, vel_x)

                    for i in range(4):
                        spark_angle = angle + math.pi + (random.random() - 0.5) * 0.5
                        speed = 2 + random.random()

                        self.sparks.append(Spark(enemy_projectile[0], spark_angle, speed))
                elif enemy_projectile[3] > 360:
                    self.enemy_projectiles.remove(enemy_projectile)
                # if the porjectile hits the player
                elif self.player.rect().collidepoint(enemy_projectile[0]):
                    self.enemy_projectiles.remove(enemy_projectile)
                    self.player.health -= 1
                    self.health_bar.hp -= 1
                    if self.player.health <= 0:
                        self.dead = 1
                    for i in range(30):
                        angle = random.random() * math.pi * 2
                        speed = random.random() * 5
                        self.sparks.append(Spark(self.player.rect().center, angle, 2 + random.random()))

            # handles player shooting
            for projectile in self.projectiles.copy():
                projectile[0][0] += projectile[1]
                projectile[2] += 1

                # draws prokectile
                img = self.assets['projectile']
                self.display.blit(img, (projectile[0][0] - img.get_width() / 2 - render_scroll[0], projectile[0][1] - img.get_height() / 2 - render_scroll[1]))

                if self.tilemap.solid_check(projectile[0]):
                    self.projectiles.remove(projectile)
                    for i in range(4):
                        self.sparks.append(Spark(projectile[0], random.random() - 0.5 + (math.pi if projectile[1] > 0 else 0), 2 + random.random()))
                elif projectile[2] > 360:
                    self.projectiles.remove(projectile)
                # if the projectile hits the enemy play sound effect and sparks and remove enemy
                for enemy in self.enemies.copy():
                   if enemy.rect().collidepoint(projectile[0]):
                        self.sfx['enemy_death'].play(0)
                        self.enemies.remove(enemy)
                        self.projectiles.remove(projectile)
                        for i in range(30):
                            angle = random.random() * math.pi * 2
                            speed = random.random() * 5
                            self.sparks.append(Spark(enemy.rect().center, angle, 2 + random.random()))

            # renders sparks
            for spark in self.sparks.copy():
                kill = spark.update()
                spark.render(self.display, offset=render_scroll)
                if kill:
                    self.sparks.remove(spark)

            # renders health bar
            self.health_bar.draw(self.display)

            # if dead play death effect and death message and reload the level
            if self.dead:
                self.dead += 1
                death = self.font.render("You Died", True, (255, 0, 0))
                pygame.draw.rect(self.display, (0,0,0), (0, (self.display.get_height() // 2 - death.get_height() // 2) - 1, self.display.get_width(), death.get_height() + 2 * 1))
                self.sfx['player_death'].play(0)
                self.display.blit(death, (self.display.get_width() // 2 - death.get_width() // 2, self.display.get_height() // 2 - death.get_height() // 2))
                if self.dead > 60:
                    self.player.health = 10
                    self.load_level(self.level)

            # key down inputs
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_a:
                        self.movement[0] = True
                    if event.key == pygame.K_d:
                        self.movement[1] = True
                    if event.key == pygame.K_w:
                        self.movement[2] = True
                    if event.key == pygame.K_s:
                        self.movement[3] = True
                    if event.key == pygame.K_SPACE:
                        self.player.shoot()

                # key up inputs
                if event.type == pygame.KEYUP:
                    if event.key == pygame.K_a:
                        self.movement[0] = False
                    if event.key == pygame.K_d:
                        self.movement[1] = False
                    if event.key == pygame.K_w:
                        self.movement[2] = False
                    if event.key == pygame.K_s:
                        self.movement[3] = False

            # update the screen
            self.screen.blit(pygame.transform.scale(self.display, self.screen.get_size()), (0, 0))
            pygame.display.update()
            self.clock.tick(60)

Game().run()
