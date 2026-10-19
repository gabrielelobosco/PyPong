# A Simple Pong Game - Made using PyPong - gabrielelobosco

import os
import pygame
import random
import math

# --- Driver controller (macOS) ---
# I pad USB generici (es. Rii Gaming GP100) su macOS vengono visti solo con HIDAPI e il
# framework Apple GameController (MFI) disattivati. Da impostare PRIMA di pygame.init().
os.environ["SDL_JOYSTICK_HIDAPI"] = "0"
os.environ["SDL_JOYSTICK_MFI"] = "0"
# Consegna gli eventi dei controller anche se la finestra non è in primo piano
os.environ["SDL_JOYSTICK_ALLOW_BACKGROUND_EVENTS"] = "1"

# --- Mappatura pulsanti del controller (pad USB stile SNES) ---
# Se un pulsante risulta sbagliato basta cambiare il numero qui.
BTN_X = 0
BTN_A = 1
BTN_B = 2
BTN_Y = 3
BTN_L = 4
BTN_R = 5
BTN_SELECT = 8
BTN_START = 9

BTN_CONFIRM = (BTN_A, BTN_START)  # conferma / avanti
BTN_BACK = (BTN_B,)  # indietro / esci al menu dalla pausa
BTN_PAUSE = (BTN_X, BTN_START)  # apre (e chiude) la pausa durante la partita

# Initialize pygame configurations

pygame.init()
pygame.joystick.init()

pygame.display.set_caption("PongIEEE - A game by: gabrielelobosco")
pygame.display.set_icon(pygame.image.load("icons/pypong_icon.png"))

# Check which joysticks are connected

joysticks = []
for i in range(pygame.joystick.get_count()):
    try:
        joy = pygame.joystick.Joystick(i)
    except pygame.error as e:
        print(f"Controller {i} non utilizzabile ({e}): ignorato.")
        continue
    joysticks.append(joy)
    print(f"Controller connesso: {joy.get_name()}")

if len(joysticks) > 2:
    print("Attenzione: sono consigliati al più 2 controller collegati per questo gioco!")


# Functions to handle controller input

def safe_event_get():
    """pygame.event.get() che non manda in crash il gioco se SDL/pygame generano un
    evento di un controller non apribile."""
    try:
        return pygame.event.get()
    except (SystemError, KeyError, pygame.error) as e:
        print(f"Evento controller ignorato ({e!r})")
        return []


def handle_joy_hotplug(event):
    """Aggiunge/rimuove i controller mentre il gioco è già aperto."""
    if event.type == pygame.JOYDEVICEADDED:
        try:
            new_joy = pygame.joystick.Joystick(event.device_index)
            new_id = new_joy.get_instance_id()
        except pygame.error as e:
            print(f"Controller {event.device_index} non utilizzabile ({e}): ignorato.")
            return
        if any(j.get_instance_id() == new_id for j in joysticks):
            return  # già registrato all'avvio
        joysticks.append(new_joy)
        print(f"Controller connesso: {new_joy.get_name()}")
    elif event.type == pygame.JOYDEVICEREMOVED:
        for j in joysticks[:]:
            if j.get_instance_id() == event.instance_id:
                joysticks.remove(j)
                print(f"Controller scollegato: {j.get_name()}")


_axis_state = {}


def joy_nav(event):
    """Traduce un evento del controller in un'azione di menu:
    'up', 'down', 'confirm' (A / Start), 'back' (B), 'pause' (X). None se non rilevante.
    Funziona con il D-pad come asse (pad USB stile SNES), come hat e con la levetta analogica."""
    handle_joy_hotplug(event)
    # D-pad come hat
    if event.type == pygame.JOYHATMOTION:
        if event.value[1] == 1:
            return 'up'
        if event.value[1] == -1:
            return 'down'
    # D-pad o levetta analogica sull'asse verticale (asse 1)
    elif event.type == pygame.JOYAXISMOTION and event.axis == 1:
        key = getattr(event, 'instance_id', getattr(event, 'joy', 0))
        prev = _axis_state.get(key, 0)
        if event.value > 0.6 and prev != 1:
            _axis_state[key] = 1
            return 'down'
        elif event.value < -0.6 and prev != -1:
            _axis_state[key] = -1
            return 'up'
        elif abs(event.value) < 0.3:
            _axis_state[key] = 0
    # Pulsanti
    elif event.type == pygame.JOYBUTTONDOWN:
        if event.button in BTN_CONFIRM:
            return 'confirm'
        if event.button in BTN_BACK:
            return 'back'
        if event.button in BTN_PAUSE:
            return 'pause'
    return None


def joy_vertical(joy):
    """Movimento verticale del controller (-1 su ... +1 giù): D-pad come asse o come hat,
    oppure levetta analogica."""
    v = 0.0
    if joy.get_numaxes() >= 2:
        axis = joy.get_axis(1)
        if abs(axis) > 0.1:  # Deadzone
            v = axis
    if joy.get_numhats() > 0:
        hat_y = joy.get_hat(0)[1]  # (x, y): y = 1 su, -1 giù
        if hat_y != 0:
            v = -hat_y
    return v


# Variables

screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
clock = pygame.time.Clock()

score_font = pygame.font.Font("fonts/PixelifySans.ttf", 44)
title_font = pygame.font.Font("fonts/PixelifySans.ttf", 64)
msg_font = pygame.font.Font("fonts/PixelifySans.ttf", 36)
created_by_font = pygame.font.Font("fonts/PixelifySans.ttf", 28)
countdown_font = pygame.font.Font("fonts/PixelifySans.ttf", 160)

points_to_win = 2

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

    try:
        logo_raw = pygame.image.load("images/ieee_pixel.webp").convert_alpha()
        logo_h = 50
        logo_w = int(logo_h * (logo_raw.get_width() / logo_raw.get_height()))
        logo_title = pygame.transform.scale(logo_raw, (logo_w, logo_h))
    except Exception:
        logo_title = None

    # Scritta scorrevole (marquee)
    marquee_surf = msg_font.render(
        "Premi A per giocare a PongIEEE!   ---   "
        "Sfida un amico in 2 Players o metti alla prova i tuoi riflessi in Endless!   ---   ",
        True, "white")
    marquee_w = marquee_surf.get_width()
    marquee_offset = 0.0
    marquee_speed = 120  # pixel al secondo
    band_h = 60

    while waiting:
        screen.fill("black")

        # Colore ufficiale IEEE
        ieee_blue = (0, 98, 155)

        # Fascia con scritta che scorre verso sinistra
        marquee_offset = (marquee_offset + marquee_speed * clock.get_time() / 1000) % marquee_w
        pygame.draw.rect(screen, ieee_blue, (0, 0, screen.get_width(), band_h))
        x = -marquee_offset
        while x < screen.get_width():
            screen.blit(marquee_surf, (x, (band_h - marquee_surf.get_height()) // 2))
            x += marquee_w

        # Renderizza i testi dell'intestazione
        title = title_font.render("PongIEEE", True, ieee_blue)
        ieee_subtitle = msg_font.render("IEEE Student Branch Unibas", True, "white")
        msg = created_by_font.render("Press space / A to start the game", True, "gray")
        created_by = created_by_font.render("A game by: gabrielelobosco", True, "gray")

        # Calcolo allineamento orizzontale LOGO + TITOLO
        spacing = 15
        center_y = screen.get_height() // 2 - 220

        if logo_title:
            total_w = logo_title.get_width() + spacing + title.get_width()
            start_x = (screen.get_width() - total_w) // 2

            rect_logo = logo_title.get_rect(midleft=(start_x, center_y))
            rect_title = title.get_rect(midleft=(start_x + logo_title.get_width() + spacing, center_y))

            screen.blit(logo_title, rect_logo)
            screen.blit(title, rect_title)
        else:
            rect_title = title.get_rect(center=(screen.get_width() // 2, center_y))
            screen.blit(title, rect_title)

        # Sottotitolo e messaggi
        rect_ieee_sub = ieee_subtitle.get_rect(center=(screen.get_width() // 2, screen.get_height() // 2 - 150))
        rect_msg = msg.get_rect(center=(screen.get_width() // 2, screen.get_height() // 2 - 100))
        rect_created_by = created_by.get_rect(center=(screen.get_width() // 2, screen.get_height() - 30))

        screen.blit(ieee_subtitle, rect_ieee_sub)
        screen.blit(msg, rect_msg)
        screen.blit(created_by, rect_created_by)

        # Usa il blu IEEE per l'opzione selezionata
        singleplayer = msg_font.render("1 Player", True, ieee_blue if selected == 1 else "white")
        multiplayer = msg_font.render("2 Players", True, ieee_blue if selected == 2 else "white")
        endless = msg_font.render("Endless (1P)", True, ieee_blue if selected == 3 else "white")
        about_text = msg_font.render("Chi siamo", True, ieee_blue if selected == 4 else "white")
        quit_text = msg_font.render("Quit", True, ieee_blue if selected == 0 else "white")

        # Posizionamento menu
        rect_single = singleplayer.get_rect(center=(screen.get_width() // 2, screen.get_height() // 2 - 20))
        rect_multi = multiplayer.get_rect(center=(screen.get_width() // 2, screen.get_height() // 2 + 40))
        rect_endless = endless.get_rect(center=(screen.get_width() // 2, screen.get_height() // 2 + 100))
        rect_about = about_text.get_rect(center=(screen.get_width() // 2, screen.get_height() // 2 + 190))
        rect_quit = quit_text.get_rect(center=(screen.get_width() // 2, screen.get_height() // 2 + 250))

        # Disegna menu
        screen.blit(singleplayer, rect_single)
        screen.blit(multiplayer, rect_multi)
        screen.blit(endless, rect_endless)
        screen.blit(about_text, rect_about)
        screen.blit(quit_text, rect_quit)

        pygame.display.flip()

        for event in safe_event_get():
            if event.type == pygame.QUIT:
                pygame.quit()
                quit()

            # Azione da tastiera o da controller
            action = joy_nav(event)
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    action = 'confirm'
                elif event.key == pygame.K_DOWN:
                    action = 'down'
                elif event.key == pygame.K_UP:
                    action = 'up'

            if action == 'confirm':
                if selected == 0:
                    pygame.quit()
                    quit()
                elif selected == 4:
                    select.play()
                    about_us_screen()
                else:
                    start.play()
                    waiting = False
            if action == 'down':
                selected = (selected + 1) % 5
                select.play()
            if action == 'up':
                selected = (selected - 1) % 5  # Cambiato in 5!
                select.play()
        clock.tick(60)


# Function to handle the pause screen (when 'escape' is pressed)

def pause_menu():
    paused = True
    while paused:
        title = title_font.render("Game Paused", True, "white")
        msg = msg_font.render("Press esc / A / X / Start to continue, q / B to quit", True, "white")
        game_name = created_by_font.render("PyPong", True, "gray")
        screen.blit(title, (screen.get_width() / 2 - title.get_width() / 2,
                            screen.get_height() / 2 - title.get_height() / 2 - msg.get_height() / 2))
        screen.blit(msg,
                    (screen.get_width() / 2 - msg.get_width() / 2, screen.get_height() / 2 + title.get_height() / 2))
        screen.blit(game_name, (screen.get_width() / 2 - game_name.get_width() / 2,
                                screen.get_height() - game_name.get_height() - 50))

        pygame.display.flip()

        for event in safe_event_get():
            if event.type == pygame.QUIT:
                pygame.quit()
                quit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return False
                if event.key == pygame.K_q:
                    return True
            action = joy_nav(event)
            if action in ('confirm', 'pause'):
                return False
            if action == 'back':
                return True

        clock.tick(60)


# Function to handle the pause screen (when someone scores)

def scored_pause(winner):
    global score_left, score_right, bounces
    paused = True
    while paused:
        winner_announcement = msg_font.render(winner + " scored!", True, "white")
        screen.blit(winner_announcement, (screen.get_width() / 2 - winner_announcement.get_width() / 2,
                                          screen.get_height() / 2 - winner_announcement.get_height()))
        msg = msg_font.render("Press space / A to continue!", True, "white")
        screen.blit(msg, (screen.get_width() / 2 - msg.get_width() / 2,
                          screen.get_height() / 2 + msg.get_height() / 2))
        draw_score()
        draw_bounces()

        pygame.display.flip()

        for event in safe_event_get():
            if event.type == pygame.QUIT:
                pygame.quit()
                quit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    bounces = 0
                    paused = False
            if joy_nav(event) == 'confirm':
                bounces = 0
                paused = False
    clock.tick(60)


# Function to display the about us screen (when a player quits or wins a game)

def about_us_screen():
    waiting = True
    ieee_blue = (0, 98, 155)

    # Carica le immagini e ridimensionale a 150x150 pixel
    try:
        logo_image = pygame.image.load("images/ieee_pixel.webp").convert_alpha()
        orig_w, orig_h = logo_image.get_size()
        max_w, max_h = 180, 150
        scale = min(max_w / orig_w, max_h / orig_h)
        new_size = (int(orig_w * scale), int(orig_h * scale))
        logo_image = pygame.transform.scale(logo_image, new_size)

        qr_image = pygame.image.load("images/qrCodeCommIEEE.png").convert_alpha()
        qr_image = pygame.transform.scale(qr_image, (150, 150))
    except Exception as e:
        print(f"Errore nel caricamento delle immagini: {e}")
        logo_image = pygame.Surface((150, 150))
        logo_image.fill(ieee_blue)
        qr_image = pygame.Surface((150, 150))
        qr_image.fill("white")

    while waiting:
        screen.fill("black")

        # Titoli e Descrizione
        title = title_font.render("IEEE Student Branch Unibas", True, ieee_blue)
        line1 = created_by_font.render("Siamo la sezione studentesca dell'Institute of Electrical and", True, "white")
        line2 = created_by_font.render("Electronics Engineers (IEEE) dell'Universita' della Basilicata.", True, "white")
        line3 = created_by_font.render("Uniamo studenti, docenti e professionisti del mondo STEM.", True, "white")

        # Messaggio CTA (Call to Action)
        scan_msg = msg_font.render("Scansiona per unirti alla Community!", True, ieee_blue)
        exit_msg = created_by_font.render("Premi SPAZIO / A per tornare al menu", True, "gray")

        # Posizionamento testi
        rect_title = title.get_rect(center=(screen.get_width() // 2, 80))
        rect_line1 = line1.get_rect(center=(screen.get_width() // 2, 160))
        rect_line2 = line2.get_rect(center=(screen.get_width() // 2, 200))
        rect_line3 = line3.get_rect(center=(screen.get_width() // 2, 240))
        rect_scan = scan_msg.get_rect(center=(screen.get_width() // 2, screen.get_height() // 2 + 200))
        rect_exit = exit_msg.get_rect(center=(screen.get_width() // 2, screen.get_height() - 40))

        # --- LOGO IEEE ---
        rect_logo = logo_image.get_rect(center=(screen.get_width() // 2 - 200, screen.get_height() // 2 + 50))
        screen.blit(logo_image, rect_logo)

        # --- QR CODE ---
        rect_qr = qr_image.get_rect(center=(screen.get_width() // 2 + 200, screen.get_height() // 2 + 50))
        screen.blit(qr_image, rect_qr)

        # Disegna a schermo i testi
        screen.blit(title, rect_title)
        screen.blit(line1, rect_line1)
        screen.blit(line2, rect_line2)
        screen.blit(line3, rect_line3)
        screen.blit(scan_msg, rect_scan)
        screen.blit(exit_msg, rect_exit)

        pygame.display.flip()

        for event in safe_event_get():
            if event.type == pygame.QUIT:
                pygame.quit()
                quit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE or event.key == pygame.K_ESCAPE or event.key == pygame.K_RETURN:
                    waiting = False  # Esce e torna al menu
            if joy_nav(event) in ('confirm', 'back'):
                waiting = False  # Esce e torna al menu (A / B / Start)

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
        sub_msg = msg_font.render("Premi SPAZIO / A per continuare", True, "white")

        rect_title = title.get_rect(center=(screen.get_width() // 2, screen.get_height() // 2 - 100))
        rect_msg = msg.get_rect(center=(screen.get_width() // 2, screen.get_height() // 2))
        rect_sub_msg = sub_msg.get_rect(center=(screen.get_width() // 2, screen.get_height() - 50))

        screen.blit(title, rect_title)
        screen.blit(msg, rect_msg)
        screen.blit(sub_msg, rect_sub_msg)

        pygame.display.flip()

        for event in safe_event_get():
            if event.type == pygame.QUIT:
                pygame.quit()
                quit()
            go_on = False
            if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                go_on = True
            if joy_nav(event) == 'confirm':  # Tasto A (o Start) del controller
                go_on = True
            if go_on:
                score_left = 0
                score_right = 0
                bounces = 0
                waiting = False
                about_us_screen()
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

    rect1_y = (screen.get_height() / 2) - (rect_height / 2)
    rect2_y = (screen.get_height() / 2) - (rect_height / 2)

    ball_radius = 20
    ball_pos = pygame.Vector2(screen.get_width() / 2,
                              screen.get_height() / 2)

    speed = 400

    ball_speed_x = random.choice([-1, 1]) * speed
    ball_speed_y = random.choice([-1, 1]) * speed

    score_left = 0
    score_right = 0
    bounces = 0

    player_speed = 500  # Leggermente aumentato per reattività con i pad

    if selected == 1:
        mode = 1
    elif selected == 2:
        mode = 2
    else:
        mode = 3

    # Countdown 3... 2... 1 (scena ferma sullo sfondo)

    def countdown():
        """Mostra 3... 2... 1 al centro dello schermo con la scena ferma sullo sfondo."""
        ieee_blue = (0, 98, 155)
        for n in (3, 2, 1):
            select.play()
            end_time = pygame.time.get_ticks() + 1000
            while pygame.time.get_ticks() < end_time:
                for event in safe_event_get():
                    if event.type == pygame.QUIT:
                        pygame.quit()
                        quit()
                    handle_joy_hotplug(event)

                screen.fill("black")
                pygame.draw.rect(screen, "white", (rect1_x, rect1_y, rect_width, rect_height))
                pygame.draw.rect(screen, "white", (rect2_x, rect2_y, rect_width, rect_height))
                pygame.draw.circle(screen, "white", ball_pos, ball_radius)
                draw_score()
                draw_bounces()

                number = countdown_font.render(str(n), True, ieee_blue)
                screen.blit(number, number.get_rect(
                    center=(screen.get_width() // 2, screen.get_height() // 2 - 150)))

                pygame.display.flip()
                clock.tick(60)
        clock.tick(60)  # evita un dt enorme al primo frame dopo il conto

    # Conto alla rovescia all'inizio della partita (UNA volta sola, fuori dal ciclo)
    countdown()

    while running:
        dt = clock.tick(60) / 1000

        for event in safe_event_get():
            if event.type == pygame.QUIT:
                running = False
            handle_joy_hotplug(event)
            # Pausa: ESC da tastiera oppure X / Start sul controller
            if (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE) or \
                    (event.type == pygame.JOYBUTTONDOWN and event.button in BTN_PAUSE):
                ritorna_al_menu = pause_menu()
                if ritorna_al_menu:
                    about_us_screen()
                    return
                countdown()  # dopo la pausa
                dt = clock.tick(60) / 1000  # azzera il dt accumulato

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

        # --- GESTIONE INPUT (Tastiera + Controller) ---
        keys = pygame.key.get_pressed()

        # Giocatore 1 (Tastiera W/S o Controller)
        p1_moving = False

        # 1. Controllo da tastiera (W / S)
        if keys[pygame.K_w]:
            rect1_y -= player_speed * dt
            p1_moving = True
        if keys[pygame.K_s]:
            rect1_y += player_speed * dt
            p1_moving = True

        # 2. Controllo da controller (D-pad o levetta)
        #    - Modalità 2 giocatori: il Giocatore 1 usa solo il primo controller
        #    - Modalità 1 giocatore / Endless: qualsiasi controller collegato comanda il paddle
        if len(joysticks) >= 1 and not p1_moving:
            p1_sources = joysticks[:1] if mode == 2 else joysticks
            for joy_src in p1_sources:
                v = joy_vertical(joy_src)
                if v != 0:
                    rect1_y += v * player_speed * dt
                    break

        # Giocatore 2 (Tastiera Freccia Su/Giu, secondo controller, o IA)
        p2_moving = False

        if mode == 2:
            # 1. Controllo da tastiera (Frecce UP / DOWN)
            if keys[pygame.K_UP]:
                rect2_y -= player_speed * dt
                p2_moving = True
            if keys[pygame.K_DOWN]:
                rect2_y += player_speed * dt
                p2_moving = True

            # 2. Controllo dal secondo controller (D-pad o levetta, se connesso)
            if len(joysticks) >= 2 and not p2_moving:
                v2 = joy_vertical(joysticks[1])
                if v2 != 0:
                    rect2_y += v2 * player_speed * dt

        elif mode == 3:
            rect2_y = ball_pos.y - (rect_height / 2)
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

        # Handle ball movement with bounds checking

        ball_pos.update(x=ball_pos.x + ball_speed_x * dt,
                        y=ball_pos.y + ball_speed_y * dt)

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
            speed = 400
            ball_speed_x = speed
            ball_speed_y = random.choice([-1, 1]) * speed
            score_right += 1
            score.play()
            scored_pause("Right")
            if max(score_left, score_right) < points_to_win:  # niente conto se la partita è finita
                countdown()

        if ball_pos.x > screen.get_width() - ball_radius:
            ball_pos.x = screen.get_width() / 2
            ball_pos.y = screen.get_height() / 2
            speed = 400
            ball_speed_x = -speed
            ball_speed_y = random.choice([-1, 1]) * speed
            score_left += 1
            score.play()
            scored_pause("Left")
            if max(score_left, score_right) < points_to_win:
                countdown()

        # Check if the ball collides with one of the players

        ball_rect = pygame.Rect(
            ball_pos.x - ball_radius,
            ball_pos.y - ball_radius,
            ball_radius * 2,
            ball_radius * 2
        )

        # --- PADDLE SINISTRO ---
        if ball_rect.colliderect(rect1) and ball_speed_x < 0:

            overlap_left = (rect1_x + rect_width) - (ball_pos.x - ball_radius)

            if ball_pos.y < rect1_y:
                overlap_y = (ball_pos.y + ball_radius) - rect1_y
            elif ball_pos.y > rect1_y + rect_height:
                overlap_y = (rect1_y + rect_height) - (ball_pos.y - ball_radius)
            else:
                overlap_y = float('inf')

            if overlap_left < overlap_y:
                hit.play()
                bounces += 1

                speed = math.hypot(ball_speed_x, ball_speed_y)
                speed = min(speed + 10, 1200)
                ball_pos.x = rect1_x + rect_width + ball_radius

                center_y = rect1_y + rect_height / 2
                offset = center_y - ball_pos.y
                normalized = offset / (rect_height / 2)

                max_angle = math.radians(60)
                bounce_angle = normalized * max_angle

                ball_speed_x = speed * math.cos(bounce_angle)
                ball_speed_y = speed * -math.sin(bounce_angle)
            else:
                if ball_pos.y < rect1_y and ball_speed_y > 0:
                    hit.play()
                    ball_pos.y = rect1_y - ball_radius
                    ball_speed_y = -abs(ball_speed_y)
                elif ball_pos.y > rect1_y + rect_height and ball_speed_y < 0:
                    hit.play()
                    ball_pos.y = rect1_y + rect_height + ball_radius
                    ball_speed_y = abs(ball_speed_y)

        # --- PADDLE DESTRO ---
        elif ball_rect.colliderect(rect2) and ball_speed_x > 0:

            overlap_right = (ball_pos.x + ball_radius) - rect2_x

            if ball_pos.y < rect2_y:
                overlap_y = (ball_pos.y + ball_radius) - rect2_y
            elif ball_pos.y > rect2_y + rect_height:
                overlap_y = (rect2_y + rect_height) - (ball_pos.y - ball_radius)
            else:
                overlap_y = float('inf')

            if overlap_right < overlap_y:
                hit.play()
                bounces += 1

                speed = math.hypot(ball_speed_x, ball_speed_y)
                speed = min(speed + 30, 1500)
                ball_pos.x = rect2_x - ball_radius

                center_y = rect2_y + rect_height / 2
                offset = center_y - ball_pos.y
                normalized = offset / (rect_height / 2)

                max_angle = math.radians(60)
                bounce_angle = normalized * max_angle

                ball_speed_x = speed * -math.cos(bounce_angle)
                ball_speed_y = speed * -math.sin(bounce_angle)
            else:
                if ball_pos.y < rect2_y and ball_speed_y > 0:
                    hit.play()
                    ball_pos.y = rect2_y - ball_radius
                    ball_speed_y = -abs(ball_speed_y)
                elif ball_pos.y > rect2_y + rect_height and ball_speed_y < 0:
                    hit.play()
                    ball_pos.y = rect2_y + rect_height + ball_radius
                    ball_speed_y = abs(ball_speed_y)

        draw_score()
        draw_bounces()

        pygame.display.flip()
    return


while True:
    main_menu()
    game_loop()