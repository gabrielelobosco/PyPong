# A Simple Pong Game - Made using PyPong - gabrielelobosco

import pygame
import random
import math

# Initialize pygame configurations

pygame.init()
pygame.display.set_caption("PyPong - A game by: gabrielelobosco")
pygame.display.set_icon(pygame.image.load("icons/PyGame_icon.png"))

# Variables

screen = pygame.display.set_mode((1280, 720))
clock = pygame.time.Clock()

score_font = pygame.font.Font("fonts/PixelifySans.ttf", 44)
title_font = pygame.font.Font("fonts/PixelifySans.ttf", 64)
msg_font = pygame.font.Font("fonts/PixelifySans.ttf", 42)
created_by_font = pygame.font.Font("fonts/PixelifySans.ttf", 28)

points_to_win = 3

score_left = 0
score_right = 0
bounces = 0

selected = 1

hit = pygame.mixer.Sound("sounds/pong_sound.wav")
end = pygame.mixer.Sound("sounds/the_end_sound.wav")
score = pygame.mixer.Sound("sounds/goal_sound.wav")
start = pygame.mixer.Sound("sounds/start_game_sound.wav")
select = pygame.mixer.Sound("sounds/select_menu_sound.wav")

# Functions to draw the current score and the current number of bounces

def draw_score():
    global score_left, score_right
    score_text = f"{score_left} : {score_right}"
    text = score_font.render(score_text, True, "white")
    rect_text = text.get_rect(center=(screen.get_width() / 2, 30))
    screen.blit(text, rect_text)

def draw_bounces():
    global bounces
    bounces_text = f"{bounces}"
    text = score_font.render(bounces_text, True, "white")
    rect_text = text.get_rect(center=(screen.get_width() / 2, screen.get_height() - 30))
    screen.blit(text, rect_text)

# Main Menu function (handle the game's starting screen)

def main_menu():
    global selected
    waiting = True
    while waiting:
        screen.fill("black")
        
        title = title_font.render("PyPong", True, "white")
        msg = msg_font.render("Press space to start the game", True, "white")
        created_by = created_by_font.render("A game by: gabrielelobosco", True, "gray")
        rect_title = title.get_rect(center=(screen.get_width()//2, screen.get_height()//2 - 150))
        rect_msg = msg.get_rect(center=(screen.get_width()//2, screen.get_height()//2 - 75))
        
        screen.blit(title, rect_title)
        screen.blit(msg, rect_msg)
        screen.blit(created_by, (screen.get_width() / 2 - created_by.get_width() / 2, screen.get_height() - created_by.get_height() - 20))

        singleplayer = msg_font.render("1 Player", True, "red" if selected == 1 else "white")
        multiplayer = msg_font.render("2 Players", True, "red" if selected == 2 else "white")
        endless = msg_font.render("Endless (1P)", True, "red" if selected == 0 else "white")
        
        rect_single = singleplayer.get_rect(center=(screen.get_width()//2, screen.get_height()//2 + 100))
        rect_multi  = multiplayer.get_rect(center=(screen.get_width()//2, screen.get_height()//2 + 150))
        rect_endless  = endless.get_rect(center=(screen.get_width()//2, screen.get_height()//2 + 200))
        
        screen.blit(singleplayer, rect_single)
        screen.blit(multiplayer, rect_multi)
        screen.blit(endless, rect_endless)

        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                quit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    start.play()
                    waiting = False
                if event.key == pygame.K_DOWN:
                    selected = (selected + 1) % 3
                    select.play()
                if event.key == pygame.K_UP:
                    selected = (selected - 1) % 3
                    select.play()
        clock.tick(60)

# Function to handle the pause screen (when 'escape' is pressed)

def pause_menu():
    paused = True
    while paused:
        title = title_font.render("Game Paused", True, "white")
        msg = msg_font.render("Press esc to continue, canc to quit", True, "white")
        game_name = created_by_font.render("PyPong", True, "gray")
        screen.blit(title, (screen.get_width() / 2 - title.get_width() / 2, screen.get_height() / 2 - title.get_height() / 2 - msg.get_height() / 2))
        screen.blit(msg, (screen.get_width() / 2 - msg.get_width() / 2, screen.get_height() / 2 + title.get_height() / 2))
        screen.blit(game_name, (screen.get_width() / 2 - game_name.get_width() / 2, screen.get_height() - game_name.get_height() - 50))
        
        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                quit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    paused = False
                if event.key == pygame.K_DELETE:
                    pygame.quit()
                    quit()
                
        clock.tick(60)

# Function to handle the pause screen (when someone scores)

def scored_pause(winner):
    global score_left, score_right, bounces
    paused = True
    while paused:
        winner_announcement = msg_font.render(winner + " scored!", True, "white")
        screen.blit(winner_announcement, (screen.get_width() / 2 - winner_announcement.get_width() / 2, 
                                          screen.get_height() / 2 - winner_announcement.get_height()))
        msg = msg_font.render("Press space to continue!", True, "white")
        screen.blit(msg, (screen.get_width() / 2 - msg.get_width() / 2,
                          screen.get_height() / 2 + msg.get_height() / 2))
        draw_score()
        draw_bounces()

        pygame.display.flip()
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                quit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    bounces = 0
                    paused = False
    clock.tick(60)

# Function to display the end screen (when a player wins)

def the_end(winner):
    global score_left, score_right, bounces
    end.play()
    waiting = True
    while waiting:
        screen.fill("black")
        title = title_font.render("The End!", True, "white")
        msg = msg_font.render(winner + " wins!", True, "white")
        sub_msg = msg_font.render("Press space to restart or enter to quit!", True, "white")
        screen.blit(title, (screen.get_width() / 2 - title.get_width() / 2, screen.get_height() / 2 - title.get_height() / 2 - msg.get_height() / 2))
        screen.blit(msg, (screen.get_width() / 2 - msg.get_width() / 2, screen.get_height() / 2 + title.get_height() / 2))
        screen.blit(sub_msg, (screen.get_width() / 2 - sub_msg.get_width() / 2, screen.get_height() - sub_msg.get_height() - 20))

        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                quit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    pygame.quit()
                    quit()
                if event.key == pygame.K_SPACE:
                    score_left = 0
                    score_right = 0
                    bounces = 0
                    waiting = False
                    return
        clock.tick(60)

# Game Loop 

def game_loop():
    global score_left, score_right, bounces
    clock.tick(60)

    running = True
    field_padding = 20

    rect_width = 10
    rect_height = 100

    rect1_x = 100
    rect2_x = screen.get_width() - rect_width - 100

    rect1_y = screen.get_height() / 2 - rect_height
    rect2_y = screen.get_height() / 2 - rect_height

    ball_radius = 20
    ball_pos = pygame.Vector2(screen.get_width() / 2, 
                              screen.get_height() / 2)

    speed = 300

    ball_speed_x = random.choice([-1, 1]) * speed
    ball_speed_y = random.choice([-1, 1]) * speed

    score_left = 0
    score_right = 0

    player_speed = 300

    if selected == 1:
        mode = 1
    elif selected == 2:
        mode = 2
    else:
        mode = 3

    while running:
        dt = clock.tick(60) / 1000

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    pause_menu()

        if score_left >= points_to_win and score_left > score_right:
            winner = "Left"
            running = False
            the_end(winner)
        elif score_right >= points_to_win and score_right > score_left:
            winner = "Right"
            running = False
            the_end(winner)
        

        screen.fill("black")

        # Draw player paddles (rectangles)

        rect1 = (rect1_x, rect1_y, rect_width, rect_height)
        rect2 = (rect2_x, rect2_y, rect_width, rect_height)

        pygame.draw.rect(screen, "white", rect1)
        pygame.draw.rect(screen, "white", rect2)

        keys = pygame.key.get_pressed()

        # Check if the keys are pressed and move paddles

        if keys[pygame.K_w]:
            rect1_y -= player_speed * dt

        if keys[pygame.K_s]:
            rect1_y += player_speed * dt

        if mode == 2:
            if keys[pygame.K_UP]:
                rect2_y -= player_speed * dt

            if keys[pygame.K_DOWN]:
                rect2_y += player_speed * dt
        elif mode == 3:
            rect2_y = ball_pos.y
        else:
            target_y = ball_pos.y - rect_height
            total_error = random.choice([-1, 1]) * random.uniform(-1, 1)
            target_y += total_error
            smooth_speed = 0.05
            diff = target_y - rect2_y
            rect2_y += diff * smooth_speed * player_speed * dt

        # Restrictions to player paddles positions (screen boundaries)

        if rect1_y < field_padding:
            rect1_y = field_padding

        if rect1_y > screen.get_height() - field_padding - rect_height:
            rect1_y = screen.get_height() - field_padding - rect_height

        if rect2_y < field_padding:
            rect2_y = field_padding

        if rect2_y > screen.get_height() - field_padding - rect_height:
            rect2_y = screen.get_height() - field_padding - rect_height

        # Draw the ball (circle)

        pygame.draw.circle(screen, "white", ball_pos, ball_radius)

        ball_rect = pygame.Rect(
            ball_pos.x - ball_radius,
            ball_pos.y - ball_radius,
            ball_radius * 2,
            ball_radius * 2
        )

        # Handle ball movement with bounds checking

        ball_pos.update(x = ball_pos.x + ball_speed_x * dt, 
                        y = ball_pos.y + ball_speed_y * dt)

        if ball_pos.y < field_padding + ball_radius:
            ball_pos.y = field_padding + ball_radius
            ball_speed_y = -ball_speed_y

        if ball_pos.y > screen.get_height() - field_padding - ball_radius:
            ball_pos.y = screen.get_height() - field_padding - ball_radius
            ball_speed_y = -ball_speed_y

        # Win and Loose

        if ball_pos.x < ball_radius:
            ball_pos.x = screen.get_width() / 2
            ball_pos.y = screen.get_height() / 2
            speed = 300
            ball_speed_x = speed
            ball_speed_y = random.choice([-1, 1]) * speed
            score_right += 1
            score.play()
            scored_pause("Right")

        if ball_pos.x > screen.get_width() - ball_radius:
            ball_pos.x = screen.get_width() / 2
            ball_pos.y = screen.get_height() / 2
            speed = 300
            ball_speed_x = -speed
            ball_speed_y = random.choice([-1, 1]) * speed
            score_left += 1
            score.play()
            scored_pause("Left")


        # Check if the ball collides with one of the players

        if ball_rect.colliderect(rect1) or ball_rect.colliderect(rect2):
            hit.play()
            bounces += 1
            speed = math.hypot(ball_speed_x, ball_speed_y)
            speed = min(speed + 10, 1200)
            angle = random.uniform(-45, 45)
            if ball_rect.colliderect(rect1):
                ball_pos.x = rect1_x + rect_width + ball_radius + 1
                ball_speed_x = abs(speed * math.cos(math.radians(angle)))
                ball_speed_y = speed * math.sin(math.radians(angle))
            if ball_rect.colliderect(rect2):
                ball_pos.x = rect2_x - ball_radius - 1
                ball_speed_x = -abs(speed * math.cos(math.radians(angle)))
                ball_speed_y = speed * math.sin(math.radians(angle))

        draw_score()
        draw_bounces()

        pygame.display.flip()
    return

while True:
    main_menu()
    game_loop()