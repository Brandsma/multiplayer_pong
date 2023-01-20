# Developer : Hamdy Abou El Anein

import random
import pygame
import sys
from pygame import *

# from easygui import *
from dataclasses import dataclass
import time as time_module
from network_data import GameState, PlayerInputEvent


# image = "/usr/share/daylight/daylightstart/DayLightLogoSunSet.gif"
# msg = "                           Welcome to Daylight Pong \n\n\n Rules of Daylight Pong \n\n\n Player 1 \n\n Arrow up = UP \n Arrow down = DOWN\n\n Player 2 \n\n Z = UP \n S = Down"
# choices = ["OK"]
# buttonbox(msg, image=image, choices=choices)

pygame.init()
fps = pygame.time.Clock()


FRAME_RATE = 60

DEBUG = True

WHITE = (255, 255, 255)
ORANGE = (255, 140, 0)
GREEN = (0, 255, 0)
BLACK = (0, 0, 0)

WIDTH = 600
HEIGHT = 400
BALL_RADIUS = 20
PAD_WIDTH = 8
PAD_HEIGHT = 80
HALF_PAD_WIDTH = PAD_WIDTH // 2
HALF_PAD_HEIGHT = PAD_HEIGHT // 2


class Pong:
    def __init__(self, name="Daylight pong", run_with_viewer=True):

        self.run_with_viewer = run_with_viewer

        self.ball_pos = [0, 0]
        self.ball_vel = [0, 0]
        self.paddle1_pos = [HALF_PAD_WIDTH - 1, HEIGHT // 2]
        self.paddle2_pos = [WIDTH + 1 - HALF_PAD_WIDTH, HEIGHT // 2]
        self.paddle1_vel = 0
        self.paddle2_vel = 0
        self.l_score = 0
        self.r_score = 0
        self.cur_time = 0.0
        self.ping = 0.0

        # Server Reconciliation
        self.sequence_number = 0
        self.player_sequence_numbers = {}
        self.local_updates = []

        # Authoritative Server
        self.handle_events = []

        self.window = pygame.display.set_mode((WIDTH, HEIGHT), 0, 32)
        pygame.display.set_caption(name)

    def get_gamestate(self):
        return GameState(
            self.ball_pos,
            self.ball_vel,
            self.paddle1_pos,
            self.paddle2_pos,
            self.paddle1_vel,
            self.paddle2_vel,
            self.l_score,
            self.r_score,
            time_module.time(),
            self.sequence_number,
        )

    def set_gamestate(self, gamestate):

        self.ball_pos = gamestate.ball_pos
        self.ball_vel = gamestate.ball_vel
        self.paddle1_pos = gamestate.paddle1_pos
        self.paddle2_pos = gamestate.paddle2_pos
        self.paddle1_vel = 0
        self.paddle2_vel = 0
        self.l_score = gamestate.l_score
        self.r_score = gamestate.r_score
        self.cur_time = gamestate.cur_time

        self.reapply_local_updates(gamestate.sequence_number)

    def reapply_local_updates(self, sequence_number):
        # If we applied local updates, we need to reapply them
        if len(self.local_updates) != 0:
            # print(f"local updates before remove: {len(self.local_updates)}")
            # print(
            #     f"sequences: first local {self.local_updates[0].sequence_number}, last local {self.local_updates[-1].sequence_number} server {sequence_number}"
            # )
            # for all updates that have not been applied yet since the last gamestate update from the server
            while (
                len(self.local_updates) != 0
                and self.local_updates[0].sequence_number <= sequence_number
            ):
                self.local_updates.pop(0)
                # Apply local update
            # print(f"local updates after remove: {len(self.local_updates)}")
            for local_update in self.local_updates:
                # print(
                #     f"reapply local update (server reconciliation) {sequence_number}, {len(self.local_updates)}"
                # )
                self.handle_event(local_update.key_direction, local_update.key_value)
                # Set fps to infinity so the updates are applied (near) instantly
                fps.tick()

    def ball_init(self, right):
        # global self.ball_pos, self.ball_vel
        self.ball_pos = [WIDTH // 2, HEIGHT // 2]
        horz = random.randrange(2, 4)
        vert = random.randrange(1, 3)

        if right == False:
            horz = -horz

        self.ball_vel = [horz, -vert]

    def init(self):
        # global self.paddle1_pos, self.paddle2_pos, self.paddle1_vel, self.paddle2_vel, self.l_score, self.r_score  # these are floats
        # global score1, score2  # these are ints
        # self.paddle1_pos = [HALF_PAD_WIDTH - 1, HEIGHT // 2]
        # self.paddle2_pos = [WIDTH + 1 - HALF_PAD_WIDTH, HEIGHT // 2]
        self.l_score = 0
        self.r_score = 0
        if random.randrange(0, 2) == 0:
            self.ball_init(True)
        else:
            self.ball_init(False)

    def update(self):
        self.move_paddles()
        self.move_ball()
        self.ball_bounce_or_score()

    def move_paddles(self):
        if (
            self.paddle1_pos[1] > HALF_PAD_HEIGHT
            and self.paddle1_pos[1] < HEIGHT - HALF_PAD_HEIGHT
        ):
            self.paddle1_pos[1] += self.paddle1_vel
        elif self.paddle1_pos[1] == HALF_PAD_HEIGHT and self.paddle1_vel > 0:
            self.paddle1_pos[1] += self.paddle1_vel
        elif self.paddle1_pos[1] == HEIGHT - HALF_PAD_HEIGHT and self.paddle1_vel < 0:
            self.paddle1_pos[1] += self.paddle1_vel

        if (
            self.paddle2_pos[1] > HALF_PAD_HEIGHT
            and self.paddle2_pos[1] < HEIGHT - HALF_PAD_HEIGHT
        ):
            self.paddle2_pos[1] += self.paddle2_vel
        elif self.paddle2_pos[1] == HALF_PAD_HEIGHT and self.paddle2_vel > 0:
            self.paddle2_pos[1] += self.paddle2_vel
        elif self.paddle2_pos[1] == HEIGHT - HALF_PAD_HEIGHT and self.paddle2_vel < 0:
            self.paddle2_pos[1] += self.paddle2_vel

    def move_ball(self):
        self.ball_pos[0] += int(self.ball_vel[0])
        self.ball_pos[1] += int(self.ball_vel[1])

    def draw_background(self, canvas):
        canvas.fill(BLACK)
        pygame.draw.line(canvas, WHITE, [WIDTH // 2, 0], [WIDTH // 2, HEIGHT], 1)
        pygame.draw.line(canvas, WHITE, [PAD_WIDTH, 0], [PAD_WIDTH, HEIGHT], 1)
        pygame.draw.line(
            canvas, WHITE, [WIDTH - PAD_WIDTH, 0], [WIDTH - PAD_WIDTH, HEIGHT], 1
        )
        pygame.draw.circle(canvas, WHITE, [WIDTH // 2, HEIGHT // 2], 70, 1)

    def draw_ball(self, canvas):
        pygame.draw.circle(canvas, ORANGE, self.ball_pos, 20, 0)

    def draw_paddles(self, canvas):
        pygame.draw.polygon(
            canvas,
            GREEN,
            [
                [
                    self.paddle1_pos[0] - HALF_PAD_WIDTH,
                    self.paddle1_pos[1] - HALF_PAD_HEIGHT,
                ],
                [
                    self.paddle1_pos[0] - HALF_PAD_WIDTH,
                    self.paddle1_pos[1] + HALF_PAD_HEIGHT,
                ],
                [
                    self.paddle1_pos[0] + HALF_PAD_WIDTH,
                    self.paddle1_pos[1] + HALF_PAD_HEIGHT,
                ],
                [
                    self.paddle1_pos[0] + HALF_PAD_WIDTH,
                    self.paddle1_pos[1] - HALF_PAD_HEIGHT,
                ],
            ],
            0,
        )
        pygame.draw.polygon(
            canvas,
            GREEN,
            [
                [
                    self.paddle2_pos[0] - HALF_PAD_WIDTH,
                    self.paddle2_pos[1] - HALF_PAD_HEIGHT,
                ],
                [
                    self.paddle2_pos[0] - HALF_PAD_WIDTH,
                    self.paddle2_pos[1] + HALF_PAD_HEIGHT,
                ],
                [
                    self.paddle2_pos[0] + HALF_PAD_WIDTH,
                    self.paddle2_pos[1] + HALF_PAD_HEIGHT,
                ],
                [
                    self.paddle2_pos[0] + HALF_PAD_WIDTH,
                    self.paddle2_pos[1] - HALF_PAD_HEIGHT,
                ],
            ],
            0,
        )

    def ball_bounce_or_score(self):
        if int(self.ball_pos[1]) <= BALL_RADIUS:
            self.ball_vel[1] = -self.ball_vel[1]
        if int(self.ball_pos[1]) >= HEIGHT + 1 - BALL_RADIUS:
            self.ball_vel[1] = -self.ball_vel[1]

        if int(self.ball_pos[0]) <= BALL_RADIUS + PAD_WIDTH and int(
            self.ball_pos[1]
        ) in range(
            self.paddle1_pos[1] - HALF_PAD_HEIGHT,
            self.paddle1_pos[1] + HALF_PAD_HEIGHT,
            1,
        ):
            self.ball_vel[0] = -self.ball_vel[0]
            self.ball_vel[0] *= 1.1
            self.ball_vel[1] *= 1.1
        elif int(self.ball_pos[0]) <= BALL_RADIUS + PAD_WIDTH:
            self.r_score += 1
            print(f"Right player scores! R: {self.r_score} L: {self.l_score}")
            self.ball_init(True)

        if int(self.ball_pos[0]) >= WIDTH + 1 - BALL_RADIUS - PAD_WIDTH and int(
            self.ball_pos[1]
        ) in range(
            self.paddle2_pos[1] - HALF_PAD_HEIGHT,
            self.paddle2_pos[1] + HALF_PAD_HEIGHT,
            1,
        ):
            self.ball_vel[0] = -self.ball_vel[0]
            self.ball_vel[0] *= 1.1
            self.ball_vel[1] *= 1.1
        elif int(self.ball_pos[0]) >= WIDTH + 1 - BALL_RADIUS - PAD_WIDTH:
            self.l_score += 1
            print(f"Left player scores! R: {self.r_score} L: {self.l_score}")
            self.ball_init(False)

    def draw_score(self, canvas):
        myfont1 = pygame.font.SysFont("Comic Sans MS", 20)
        label1 = myfont1.render("Score " + str(self.l_score), 1, (255, 255, 0))
        canvas.blit(label1, (50, 20))

        myfont2 = pygame.font.SysFont("Comic Sans MS", 20)
        label2 = myfont2.render("Score " + str(self.r_score), 1, (255, 255, 0))
        canvas.blit(label2, (470, 20))

        if DEBUG:
            ping = myfont2.render(f"Ping {self.ping}", 1, (255, 255, 0))
            canvas.blit(ping, (310, 20))

    def draw(self, canvas):
        # global self.paddle1_pos, self.paddle2_pos, self.ball_pos, self.ball_vel, self.l_score, self.r_score

        self.draw_background(canvas)
        self.draw_ball(canvas)
        self.draw_paddles(canvas)
        self.draw_score(canvas)

    def set_ping(self, ping):
        self.ping = int(1000 * ping)

    def add_player_input_to_events(self, player_input_event):
        self.handle_events.append(player_input_event)

    def server_run(self, server):
        self.init()

        while True:
            self.update()

            if self.run_with_viewer:
                self.draw(self.window)

            for player_input_event in self.handle_events:
                self.handle_event(
                    player_input_event.key_direction, player_input_event.key_value
                )

                self.player_sequence_numbers[player_input_event.player_id] += 1

            self.handle_events = []

            pygame.display.update()
            fps.tick(60)

            server.send_gamestate_to_all_connections()

    def handle_event(self, key_direction, event_key):
        if key_direction == KEYDOWN:
            if event_key == K_UP:
                self.paddle2_vel = -8
            elif event_key == K_DOWN:
                self.paddle2_vel = 8
            elif event_key == K_z:
                self.paddle1_vel = 8
            elif event_key == K_s:
                self.paddle1_vel = -8
        elif key_direction == KEYUP:
            if event_key in (K_z, K_s):
                self.paddle1_vel = 0
            elif event_key in (K_UP, K_DOWN):
                self.paddle2_vel = 0

    def client_run(self, client):
        self.init()

        while True:
            self.update()

            if self.run_with_viewer:
                self.draw(self.window)

            for event in pygame.event.get():

                if event.type == QUIT:
                    pygame.display.quit()
                    pygame.quit()
                    sys.exit()

                if event.type == KEYDOWN or event.type == KEYUP:
                    player_input_event = PlayerInputEvent(
                        player_id=client.connection_info["player_data"].player_id,
                        key_value=event.key,
                        key_direction=event.type,
                        sequence_number=self.sequence_number,
                    )
                    self.sequence_number += 1

                    client.send(player_input_event)

                    # Client side prediction
                    self.local_updates.append(player_input_event)
                    # NOTE for reimplementation in snake, local updates should be a 'weaker' version than the server / reconciliation updates.
                    # e.g. dont show that the snake is dead yet, even if it booped into a wall/tail. Only show it when the server confirms it.
                    self.handle_event(event.type, event.key)

            pygame.display.update()
            fps.tick(60)


if __name__ == "__main__":
    pong = Pong()
    pong.run()
