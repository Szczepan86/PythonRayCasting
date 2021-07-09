import math
import pygame
import sys
from pygame.locals import *

################################################
# CONSTANTS

# world map - one digit one tile, where 0 is empty space and 1 .. n are different wall colors
WORLD_MAP = [
    [1, 2, 1, 2, 1, 2, 1, 2, 1, 2, 1, 2],
    [1, 0, 0, 0, 0, 0, 2, 0, 0, 0, 0, 2],
    [2, 0, 0, 0, 0, 0, 3, 0, 0, 0, 0, 1],
    [1, 2, 3, 2, 0, 0, 2, 0, 0, 0, 0, 2],
    [2, 0, 0, 3, 0, 0, 0, 0, 0, 0, 0, 1],
    [1, 0, 0, 2, 0, 0, 0, 0, 0, 0, 0, 2],
    [2, 0, 0, 3, 0, 0, 0, 0, 0, 0, 0, 1],
    [1, 0, 0, 0, 0, 0, 2, 3, 0, 0, 0, 2],
    [2, 0, 0, 2, 0, 0, 0, 0, 0, 0, 0, 1],
    [1, 0, 0, 3, 0, 0, 0, 0, 0, 0, 0, 2],
    [1, 2, 1, 2, 1, 2, 1, 2, 1, 2, 1, 1]
]

# colors map - where 0 index is empty and 1 .. n represents specific RGB value
COLORS = [[], [105, 20, 14], [164, 66, 0], [213, 137, 54]]

# window resolution
WIDTH = 1000
HEIGHT = 800

# 'field of view' - it doesn't directly impact geometry, but bigger FOV = more on the screen
FOV = 0.5

# rotation and movement speed
ROTATION_SPEED = 0.002
MOVEMENT_SPEED = 0.007


################################################
# GAME
def game():
    pygame.init()

    # creating a screen
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("RayCaster Python Demo")

    # initial position
    position_x = 3.0
    position_y = 7.0

    # sight direction
    direction_x = 0.0
    direction_y = 1.0

    # clock to adjust real time for different machines
    clock = pygame.time.Clock()

    # main game loop
    while True:
        # adjusting the speed depending on frame rate
        dt = clock.tick(120)
        rotation_speed_dt = ROTATION_SPEED * dt
        movement_speed_dt = MOVEMENT_SPEED * dt

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.display.quit()
                pygame.quit()
                sys.exit()

        # keys management
        pygame.event.pump()
        keys = pygame.key.get_pressed()

        if keys[K_ESCAPE]:
            pygame.display.quit()
            pygame.quit()
            sys.exit()

        # two dimensional rotation (left / right) - see more at https://en.wikipedia.org/wiki/Rotation_(mathematics)
        if keys[K_LEFT] or keys[K_q]:
            old_direction_x = direction_x
            direction_x = old_direction_x * math.cos(-rotation_speed_dt) - direction_y * math.sin(-rotation_speed_dt)
            direction_y = old_direction_x * math.sin(-rotation_speed_dt) + direction_y * math.cos(-rotation_speed_dt)

        if keys[K_RIGHT] or keys[K_e]:
            old_direction_x = direction_x
            direction_x = old_direction_x * math.cos(rotation_speed_dt) - direction_y * math.sin(rotation_speed_dt)
            direction_y = old_direction_x * math.sin(rotation_speed_dt) + direction_y * math.cos(rotation_speed_dt)

        # forward / backward movement - so increase / decrease x-y position depending on eyes direction
        if keys[K_UP] or keys[K_w]:
            if WORLD_MAP[int(position_x + direction_x * movement_speed_dt)][int(position_y)] == 0:
                position_x += direction_x * movement_speed_dt
            if WORLD_MAP[int(position_x)][int(position_y + direction_y * movement_speed_dt)] == 0:
                position_y += direction_y * movement_speed_dt

        if keys[K_DOWN] or keys[K_s]:
            if WORLD_MAP[int(position_x - direction_x * movement_speed_dt)][int(position_y)] == 0:
                position_x -= direction_x * movement_speed_dt
            if WORLD_MAP[int(position_x)][int(position_y - direction_y * movement_speed_dt)] == 0:
                position_y -= direction_y * movement_speed_dt

        # strafing - similar to forward / backward movement, just with a twist :)
        if keys[K_a]:
            if WORLD_MAP[int(position_x + direction_y * movement_speed_dt)][int(position_y)] == 0:
                position_x += direction_y * movement_speed_dt
            if WORLD_MAP[int(position_x)][int(position_y - direction_x * movement_speed_dt)] == 0:
                position_y -= direction_x * movement_speed_dt

        if keys[K_d]:
            if WORLD_MAP[int(position_x - direction_y * movement_speed_dt)][int(position_y)] == 0:
                position_x -= direction_y * movement_speed_dt
            if WORLD_MAP[int(position_x)][int(position_y + direction_x * movement_speed_dt)] == 0:
                position_y += direction_x * movement_speed_dt

        # filling floor and ground with some colors
        screen.fill((15, 15, 15))
        pygame.draw.rect(screen, (40, 40, 40), (0, int(HEIGHT / 2), WIDTH, int(HEIGHT / 2)))

        # plane calculation (we will cast a series of rays on this plane)
        plane_x = -direction_y * FOV
        plane_y = direction_x * FOV

        # drawing a 3D perspective for every x coordinated screen column, starting from the leftmost column
        # just take a look at https://permadi.com/1996/05/ray-casting-tutorial-5/ to have more understanding of
        # this mechanism - plane x/y define projection plane, and delta is pointing to specific point on a plane
        column = 0
        while column < WIDTH:
            # delta impacts directly how geometry is represented, it should be always between -1 .. 1,
            # so the second static value should be half of the first one - otherwise you might feel a little bit dizzy
            delta = 2.0 * column / WIDTH - 1.0

            # ray direction is calculated just by adding the direction and a plane shifted by current delta value
            ray_direction_x = direction_x + plane_x * delta
            ray_direction_y = direction_y + plane_y * delta

            # defining the tile we're standing on (again - refer to ray casting tutorial)
            map_x = int(position_x)
            map_y = int(position_y)

            # depending on ray direction (pos or neg), our collision algorithm will be slightly different
            if ray_direction_x < 0:
                # define if our rays direction is on the left or right side of X axis
                step_x = -1
                # calculate distance to the nearest tile border
                control_distance_x = (position_x - map_x) * abs(ray_direction_y)
            else:
                step_x = 1
                control_distance_x = (map_x + 1.0 - position_x) * abs(ray_direction_y)

            # similar logic, but for ray direction on y axis
            if ray_direction_y < 0:
                step_y = -1
                control_distance_y = (position_y - map_y) * abs(ray_direction_x)
            else:
                step_y = 1
                control_distance_y = (map_y + 1.0 - position_y) * abs(ray_direction_x)

            # iterating over tiles which intersect the ray path, just to find a closest wall
            # some explanation might be found there: https://permadi.com/1996/05/ray-casting-tutorial-7/
            # this algorithm is slightly different, but general idea is similar
            while True:
                # depending what's closer, our next tile will be taken by changing x or y axis
                if control_distance_x < control_distance_y:
                    # depending on the ray direction, look for x+ or x- tile
                    map_x += step_x
                    side = "x"
                    # stop when a wall is found
                    if WORLD_MAP[map_x][map_y] > 0:
                        break
                    # if no wall is found - increase our 'ray distance'
                    control_distance_x += abs(ray_direction_y)
                else:
                    # mechanism similar to x axis
                    map_y += step_y
                    side = "y"
                    if WORLD_MAP[map_x][map_y] > 0:
                        break
                    control_distance_y += abs(ray_direction_x)

            # at this moment map_x and map_y refers to the closest wall position found by current ray

            # final distance calculation (depending on which axis we intersect our wall)
            if side == "x":
                final_distance = abs((map_x - position_x + (1.0 - step_x) / 2.0) / ray_direction_x)
            else:
                final_distance = abs((map_y - position_y + (1.0 - step_y) / 2.0) / ray_direction_y)

            # line height calculation (higher distance = smaller line) with 0 division patch
            line_height = abs(int(HEIGHT / (final_distance + 0.0000001)))
            draw_start = max(HEIGHT / 2 - line_height / 2, 0)
            if draw_start < 0:
                draw_start = 0

            draw_end = HEIGHT / 2 + line_height / 2
            if draw_end >= HEIGHT:
                draw_end = HEIGHT - 1

            # getting a wall color from the worldmap
            color = COLORS[WORLD_MAP[map_x][map_y]].copy()

            # simple shadows - change the intensity of the color for x axis walls (just to better see corners)
            if side == "x":
                for index, value in enumerate(color):
                    color[index] = int(value / 1.2)

            # change intensity of the color depending on the distance
            for index, value in enumerate(color):
                color[index] = int(value / max(final_distance / 2, 1))

            # draw a column at given width (just to control the performance)
            column_resolution = 2
            pygame.draw.line(screen, color, (column, draw_start), (column, draw_end), column_resolution)

            column += column_resolution

        # finally! update full display surface
        pygame.display.flip()


if __name__ == "__main__":
    game()
