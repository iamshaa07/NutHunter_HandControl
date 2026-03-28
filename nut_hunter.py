import cv2
import mediapipe as mp
import pygame
import sys
import random
import os
import time
import math 

# ======================================================
# 1. AUTO-FIX FOLDER
# ======================================================
try:
    script_dir = os.path.dirname(os.path.abspath(_file_))
    os.chdir(script_dir)
except:
    pass

# ======================================================
# 2. HAND DETECTION
# ======================================================
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(max_num_hands=1)

def is_fist(landmarks):
    tips = [8, 12, 16, 20]
    folded = 0
    for tip in tips:
        if landmarks[tip].y > landmarks[tip - 2].y:
            folded += 1
    return folded >= 3

def detect_fist():
    global cam_frame_small
    success, img = cap.read()
    if not success: return False
    img = cv2.flip(img, 1)
    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    results = hands.process(img_rgb)
    
    frame = cv2.resize(cv2.cvtColor(img, cv2.COLOR_BGR2RGB), (200, 150))
    cam_frame_small = pygame.surfarray.make_surface(frame.swapaxes(0, 1))

    if results.multi_hand_landmarks:
        lm = results.multi_hand_landmarks[0].landmark
        if is_fist(lm): return True
    return False

# ======================================================
# 3. GAME SETUP
# ======================================================
pygame.init()
try:
    pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
except:
    pygame.mixer.init()

WIDTH, HEIGHT = 960, 540
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Nut Hunter - Hand Gesture") 
clock = pygame.time.Clock()

# --- FONT (Support .otf & .ttf) ---
if os.path.exists("font.otf"):
    print("✅ Custom Font (.otf) ditemukan!")
    font = pygame.font.Font("font.otf", 36)
    font_small = pygame.font.Font("font.otf", 24)
    title_font = pygame.font.Font("font.otf", 55)
elif os.path.exists("font.ttf"):
    print("✅ Custom Font (.ttf) ditemukan!")
    font = pygame.font.Font("font.ttf", 36)
    font_small = pygame.font.Font("font.ttf", 24)
    title_font = pygame.font.Font("font.ttf", 55)
else:
    print("⚠ Custom Font tidak ada, pakai Arial.")
    font = pygame.font.SysFont("Arial", 36)
    font_small = pygame.font.SysFont("Arial", 24)       
    title_font = pygame.font.SysFont("Arial", 55, bold=True) 

MENU = 0
PLAY = 1
GAMEOVER = 2
state = MENU

# ======================================================
# 4. LOAD ASSETS (SMART LOADER)
# ======================================================
def load_smart_bg(filename_base):
    for ext in [".png", ".jpg", ".jpeg"]:
        full_path = filename_base + ext
        if os.path.exists(full_path):
            print(f"✅ Background ditemukan: {full_path}")
            return pygame.image.load(full_path).convert()
    return None 

try:
    # --- LOAD MENU IMAGE (SEMI TRANSPARAN) ---
    menu_img = None
    if os.path.exists("menu.png"):
        print("✅ Menu Image (Canva) ditemukan!")
        menu_img = pygame.image.load("menu.png").convert_alpha()
        menu_img.set_alpha(230) 
    else:
        print("Info: 'menu.png' tidak ada.")

    # --- UI SCORE ---
    ui_img = None
    if os.path.exists("ui.png"):
        ui_img = pygame.image.load("ui.png").convert_alpha()
        ui_img = pygame.transform.scale(ui_img, (260, 80))

    # --- BACKGROUND ---
    raw_pagi = load_smart_bg("bg_pagi")
    if raw_pagi is None:
        if os.path.exists("bg.png"): raw_pagi = pygame.image.load("bg.png").convert()
        elif os.path.exists("bg.jpg"): raw_pagi = pygame.image.load("bg.jpg").convert()
        else: 
            print("ERROR: Background Pagi tidak ditemukan!")
            sys.exit()

    bg_pagi = pygame.transform.scale(raw_pagi, (WIDTH, HEIGHT))
    
    raw_sore = load_smart_bg("bg_sore")
    bg_sore = pygame.transform.scale(raw_sore, (WIDTH, HEIGHT)) if raw_sore else bg_pagi
    
    raw_malam = load_smart_bg("bg_malam")
    bg_malam = pygame.transform.scale(raw_malam, (WIDTH, HEIGHT)) if raw_malam else bg_pagi

    bg_x = 0
    
    # Aset Lain
    squirrel_img = pygame.image.load("squirrel.png").convert_alpha()
    squirrel_img = pygame.transform.scale(squirrel_img, (70, 70))
    squirrel_mask = pygame.mask.from_surface(squirrel_img)
    
    acorn_img = pygame.image.load("acorn.png").convert_alpha()
    acorn_img = pygame.transform.scale(acorn_img, (50, 50))
    
    # --- OBSTACLE (STUMP TINGGI) ---
    if os.path.exists("stump.png"):
        print("✅ Gambar Stump (Batang Pohon) ditemukan!")
        obstacle_img = pygame.image.load("stump.png").convert_alpha()
    elif os.path.exists("obstacle.png"):
        obstacle_img = pygame.image.load("obstacle.png").convert_alpha()
    else:
        obstacle_img = pygame.image.load("obstacale.png").convert_alpha()
    
    # Tinggi 600px biar jadi tiang
    obstacle_img = pygame.transform.scale(obstacle_img, (100, 600))
    obstacle_top = pygame.transform.flip(obstacle_img, False, True)

    bird_present = False
    bird_img = None
    if os.path.exists("bird.png"):
        bird_img = pygame.image.load("bird.png").convert_alpha()
        bird_img = pygame.transform.scale(bird_img, (60, 45))
        bird_mask = pygame.mask.from_surface(bird_img)
        bird_present = True
        
except Exception as e:
    print(f"GAMBAR ERROR: {e}")
    sys.exit()

# AUDIO
jump_sound = None
score_sound = None
dead_sound = None

if os.path.exists("jump.wav"): jump_sound = pygame.mixer.Sound("jump.wav")
elif os.path.exists("jump.mp3"): jump_sound = pygame.mixer.Sound("jump.mp3")
if jump_sound: jump_sound.set_volume(0.6)

if os.path.exists("score.wav"): score_sound = pygame.mixer.Sound("score.wav")
elif os.path.exists("score.mp3"): score_sound = pygame.mixer.Sound("score.mp3")
if score_sound: score_sound.set_volume(0.8)

if os.path.exists("dead.wav"): dead_sound = pygame.mixer.Sound("dead.wav")
elif os.path.exists("dead.mp3"): dead_sound = pygame.mixer.Sound("dead.mp3")
if dead_sound: dead_sound.set_volume(1.0)

has_music = False
if os.path.exists("music.mp3"):
    pygame.mixer.music.load("music.mp3")
    pygame.mixer.music.set_volume(0.4) 
    has_music = True

# ======================================================
# 5. LOGIC
# ======================================================
def load_high_score():
    if os.path.exists("highscore.txt"):
        try:
            with open("highscore.txt", "r") as f: return int(f.read())
        except: return 0
    return 0

def save_high_score(new_high):
    try: 
        with open("highscore.txt", "w") as f: f.write(str(new_high))
    except: pass

squirrel_x = WIDTH // 4
squirrel_y = HEIGHT // 2
velocity = 0
GRAVITY = 0.45
JUMP = -9
GAP = 200 

BASE_SPEED = 8 
current_speed = BASE_SPEED

obstacles = []
acorns = []
birds = [] 
cam_frame_small = None
high_score = load_high_score()
score = 0
cap = cv2.VideoCapture(0)

def create_obstacle():
    center_y = random.randint(160, HEIGHT - 160)
    return [WIDTH + 150, center_y]

def create_acorn():
    return [WIDTH + random.randint(400, 700), random.randint(80, HEIGHT - 80)]

def create_bird():
    start_y = random.randint(50, HEIGHT - 50)
    return [WIDTH + random.randint(50, 200), start_y]

def reset_game():
    global squirrel_y, velocity, obstacles, acorns, birds, score, high_score, current_speed
    
    # Hentikan suara Game Over jika restart
    if dead_sound:
        dead_sound.stop()

    squirrel_y = HEIGHT // 2
    velocity = 0
    current_speed = BASE_SPEED
    
    obstacles = []
    for i in range(3):
        x_pos = WIDTH + 150 + (i * 350)
        y_pos = random.randint(160, HEIGHT - 160)
        obstacles.append([x_pos, y_pos])
        
    acorns = [create_acorn()]
    birds = [] 
    score = 0
    high_score = load_high_score()
    
    if has_music:
        try: pygame.mixer.music.play(-1)
        except: pass

def player_die():
    if has_music: pygame.mixer.music.stop() 
    if dead_sound: dead_sound.play()
    return GAMEOVER

# ======================================================
# 6. MAIN LOOP
# ======================================================
reset_game()
running = True

if has_music: pygame.mixer.music.play(-1)

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT: running = False
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE: running = False
            if state == MENU and event.key == pygame.K_s:
                reset_game()
                state = PLAY
            if state == GAMEOVER and event.key == pygame.K_r:
                reset_game()
                state = PLAY

    # DAY/NIGHT
    current_bg_img = bg_pagi
    if score >= 10: current_bg_img = bg_sore
    if score >= 25: current_bg_img = bg_malam

    bg_x -= 1
    if bg_x <= -WIDTH: bg_x = 0
    screen.blit(current_bg_img, (bg_x, 0))
    screen.blit(current_bg_img, (bg_x + WIDTH, 0))

    # --- LOGIKA WARNA FONT OTOMATIS ---
    # Hitam (Pagi/Sore), Putih (Malam)
    dynamic_text_color = (0, 0, 0) 
    if score >= 25: 
        dynamic_text_color = (255, 255, 255)

    # --- MENU SCREEN ---
    if state == MENU:
        if menu_img:
            menu_rect = menu_img.get_rect(center=(WIDTH//2, HEIGHT//2))
            screen.blit(menu_img, menu_rect)
            
            # High Score (Warna Hitam di Menu karena papan cream)
            score_text = f"High Score {high_score}"
            
            s_score = font_small.render(score_text, True, (0, 0, 0)) # Bayangan
            score_rect_s = s_score.get_rect(center=(WIDTH//2 + 2, HEIGHT//2 + 222))
            screen.blit(s_score, score_rect_s)

            t_score = font_small.render(score_text, True, (255, 255, 255)) # Teks Putih
            score_rect = t_score.get_rect(center=(WIDTH//2, HEIGHT//2 + 220)) 
            screen.blit(t_score, score_rect)
            
        else:
            t_title_shadow = title_font.render("NUT HUNTER", True, (30, 15, 5))
            screen.blit(t_title_shadow, (WIDTH//2 - 220 + 4, HEIGHT//2 - 180 + 4))
            t_title = title_font.render("NUT HUNTER", True, (255, 220, 50)) 
            screen.blit(t_title, (WIDTH//2 - 220, HEIGHT//2 - 180))

            icon_sq = pygame.transform.scale(squirrel_img, (90, 90))
            screen.blit(icon_sq, (WIDTH//2 - 45, HEIGHT//2 - 110))

            t_inst1 = font_small.render("CARA BERMAIN:", True, (255, 200, 100))
            t_inst2 = font_small.render("✊ Kepalkan = LOMPAT", True, (255, 255, 255))
            t_inst3 = font_small.render("🖐  Buka Tangan = JATUH", True, (255, 255, 255))
            t_inst4 = font_small.render("⚠ Hindari Pipa & Burung", True, (255, 255, 255))

            screen.blit(t_inst1, (WIDTH//2 - 90, HEIGHT//2 - 10))
            screen.blit(t_inst2, (WIDTH//2 - 160, HEIGHT//2 + 30))
            screen.blit(t_inst3, (WIDTH//2 - 160, HEIGHT//2 + 60))
            screen.blit(t_inst4, (WIDTH//2 - 160, HEIGHT//2 + 90))

            if int(time.time() * 2) % 2 == 0: color_start = (100, 255, 100) 
            else: color_start = (50, 200, 50)   
            t_start = font.render("Press 'S' to Start", True, color_start)
            screen.blit(t_start, (WIDTH//2 - 120, HEIGHT//2 + 140))
            
            t_score = font_small.render(f"High Score {high_score}", True, (255, 220, 50))
            screen.blit(t_score, (WIDTH//2 - 80, HEIGHT//2 + 185))

        pygame.display.update()
        clock.tick(30)
        continue

    # --- PLAY ---
    if state == PLAY:
        level_bonus = score // 10 
        current_speed = min(BASE_SPEED + level_bonus, 20) 
        
        if detect_fist():
            if velocity > 0 and jump_sound: jump_sound.play()
            velocity = JUMP

        velocity += GRAVITY
        squirrel_y += velocity
        sq_rect = squirrel_img.get_rect(center=(squirrel_x, int(squirrel_y)))
        screen.blit(squirrel_img, sq_rect)

        if squirrel_y < 0 or squirrel_y > HEIGHT:
            state = player_die()

        if cam_frame_small is not None:
            screen.blit(cam_frame_small, (15, 15))

        for obs in obstacles:
            obs[0] -= current_speed 
            x = obs[0]
            center = obs[1]
            
            top_rect = obstacle_top.get_rect(midbottom=(x, center - GAP//2))
            screen.blit(obstacle_top, top_rect)
            
            bottom_rect = obstacle_img.get_rect(midtop=(x, center + GAP//2))
            screen.blit(obstacle_img, bottom_rect)

            top_mask = pygame.mask.from_surface(obstacle_top)
            bottom_mask = pygame.mask.from_surface(obstacle_img)
            off_t = (top_rect.x - sq_rect.x, top_rect.y - sq_rect.y)
            off_b = (bottom_rect.x - sq_rect.x, bottom_rect.y - sq_rect.y)

            if squirrel_mask.overlap(top_mask, off_t) or squirrel_mask.overlap(bottom_mask, off_b):
                state = player_die()

        if obstacles[0][0] < -100:
            obstacles.pop(0)
            last_x = obstacles[-1][0]
            new_x = last_x + 350
            new_y = random.randint(160, HEIGHT - 160)
            obstacles.append([new_x, new_y])
            score += 1
            if score_sound: score_sound.play()

        if score >= 15:
            max_birds = 1
            spawn_rate = 2
            if score >= 20: 
                max_birds = 2
                spawn_rate = 4

            if len(birds) < max_birds and random.randint(0, 100) < spawn_rate:
                birds.append(create_bird())

        for b in birds:
            b[0] -= (current_speed + 3) 
            
            if bird_present:
                b_rect = bird_img.get_rect(center=(int(b[0]), int(b[1])))
                screen.blit(bird_img, b_rect)
                off_bird = (b_rect.x - sq_rect.x, b_rect.y - sq_rect.y)
                if squirrel_mask.overlap(bird_mask, off_bird):
                    state = player_die()
            else:
                b_rect = pygame.Rect(b[0], b[1], 40, 40)
                pygame.draw.rect(screen, (255, 0, 0), b_rect)
                if sq_rect.colliderect(b_rect):
                    state = player_die()

        if len(birds) > 0 and birds[0][0] < -100:
            birds.pop(0)

        for a in acorns:
            a[0] -= current_speed
            ar = acorn_img.get_rect(center=(a[0], a[1]))
            screen.blit(acorn_img, ar)
            if sq_rect.colliderect(ar):
                score += 2
                if score_sound: score_sound.play()
                acorns.remove(a)
                acorns.append(create_acorn())
                break

        if len(acorns) > 0 and acorns[0][0] < -50:
            acorns.pop(0)
            acorns.append(create_acorn())

        level = (score // 10) + 1 
        
        # UI SCORE
        if ui_img:
            ui_rect = ui_img.get_rect()
            ui_rect.topright = (WIDTH - 10, 10)
            screen.blit(ui_img, ui_rect)
            # Kalau ada UI papan, tulisan tetap Putih biar jelas
            sc = font_small.render(f"Score {score}  Lv {level}", True, (255, 255, 255)) 
            sc_rect = sc.get_rect(center=ui_rect.center)
            screen.blit(sc, sc_rect)
        else:
            # Kalau gak ada UI, warna BERUBAH sesuai waktu (Hitam/Putih)
            sc = font.render(f"Score {score}  Lv {level}", True, dynamic_text_color)
            sc_rect = sc.get_rect()
            sc_rect.topright = (WIDTH - 20, 20)
            screen.blit(sc, sc_rect)

    # --- GAME OVER ---
    if state == GAMEOVER:
        if score > high_score:
            high_score = score
            save_high_score(high_score)

        # Warna Teks Game Over juga ikut berubah sesuai waktu
        # Judul "GAME OVER" tetap Merah (t1) tapi bayangannya ngikut waktu
        
        t1 = title_font.render("GAME OVER", True, (255, 0, 0)) # Tetap Merah
        t2 = font.render(f"Score {score}  High {high_score}", True, dynamic_text_color)
        t3 = font_small.render("Press R to Restart", True, dynamic_text_color)
        t4 = font_small.render("ESC to Exit", True, dynamic_text_color)

        r1 = t1.get_rect(center=(WIDTH//2, HEIGHT//2 - 80))
        r2 = t2.get_rect(center=(WIDTH//2, HEIGHT//2 - 20))
        r3 = t3.get_rect(center=(WIDTH//2, HEIGHT//2 + 40))
        r4 = t4.get_rect(center=(WIDTH//2, HEIGHT//2 + 90))

        screen.blit(t1, r1)
        screen.blit(t2, r2)
        screen.blit(t3, r3)
        screen.blit(t4, r4)

    pygame.display.update()
    clock.tick(60)

cap.release()
cv2.destroyAllWindows()
pygame.quit()
sys.exit()