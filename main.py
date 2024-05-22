import pygame
import cv2
import mediapipe as mp
import random
import time

# Initialize Pygame
pygame.init()

# Screen dimensions
SCREEN_WIDTH = 1920
SCREEN_HEIGHT = 1200
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Gesture Controlled Game")

# Load the ship image and resize it
ship_image = pygame.image.load('./assets/ship.png')
ship_image = pygame.transform.scale(ship_image, (100, 100))  # Resize to 50x50 pixels
ship_rect = ship_image.get_rect()

# Load obstacle images and resize them
large_obstacle_image = pygame.image.load('./assets/rock1.png')
large_obstacle_image = pygame.transform.scale(large_obstacle_image, (50, 50))  # Resize to 50x50 pixels
small_obstacle_image = pygame.image.load('./assets/rock2.png')
small_obstacle_image = pygame.transform.scale(small_obstacle_image, (25, 25))  # Resize to 25x25 pixels

# Game variables
clock = pygame.time.Clock()
FPS = 60
player_pos = [400, 500]
player_speed = 5

# Obstacle variables
obstacle_speed = 5
small_obstacle_speed = 7
obstacle_spawn_timer = 0
small_obstacle_spawn_timer = 0
obstacles = []
small_obstacles = []

# Projectile variables
projectiles = []
projectile_speed = 10

# Game state variables
running = True
game_over = False
collision_time = None

# Level variables
level = 1
level_threshold = 15  # Score threshold to progress to the next level

# Initialize OpenCV and MediaPipe
cap = cv2.VideoCapture(0)
ret, frame = cap.read()
#cv2.resize(frame, (1600, 900))

cv2.namedWindow('full-screen', cv2.WINDOW_NORMAL)
# cv2.setWindowProperty('full-screen', cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

mp_hands = mp.solutions.hands
hands = mp_hands.Hands(max_num_hands=1, min_detection_confidence=0.7)
mp_draw = mp.solutions.drawing_utils

# Function to detect hand gestures and determine if a pinching gesture is made
def detect_hand_gesture(frame):
    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    result = hands.process(frame_rgb)
    if result.multi_hand_landmarks:
        for hand_landmarks in result.multi_hand_landmarks:
            mp_draw.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)
            x = int(hand_landmarks.landmark[mp_hands.HandLandmark.INDEX_FINGER_TIP].x * SCREEN_WIDTH)
            y = int(hand_landmarks.landmark[mp_hands.HandLandmark.INDEX_FINGER_TIP].y * SCREEN_HEIGHT)
            x = SCREEN_WIDTH - x  # Flip x-coordinate
            pinch_distance = abs(
                hand_landmarks.landmark[mp_hands.HandLandmark.THUMB_TIP].x -
                hand_landmarks.landmark[mp_hands.HandLandmark.INDEX_FINGER_TIP].x
            )
            pinching = pinch_distance < 0.05  # Pinching threshold
            return (x, y), pinching
    return None, False

# Function to spawn large obstacles
def spawn_obstacle():
    x = random.randint(0, SCREEN_WIDTH - 50)
    y = -50
    obstacles.append(pygame.Rect(x, y, 50, 50))

# Function to spawn small obstacles
def spawn_small_obstacle():
    x = random.randint(0, SCREEN_WIDTH - 25)
    y = -25
    small_obstacles.append(pygame.Rect(x, y, 25, 25))

# Function to shoot projectiles
def shoot_projectile():
    x = player_pos[0] + 24  # Center of the spaceship
    y = player_pos[1]
    projectiles.append(pygame.Rect(x, y, 2, 5))

# Function to check collisions between the spaceship and obstacles
def check_collision():
    player_rect = pygame.Rect(player_pos[0], player_pos[1], 50, 50)
    for obstacle in small_obstacles:
        if player_rect.colliderect(obstacle):
            return True
    return False
# Function to update the obstacle speed based on the level
def update_obstacle_speed():
    global obstacle_speed, small_obstacle_speed
    obstacle_speed = 5 + level  # Increase speed as level increases
    small_obstacle_speed = 7 + level

# Function to display a message on the screen
def display_message(text, font, color, position):
    message = font.render(text, True, color)
    screen.blit(message, position)

# Function to reset the game variables
def reset_game():
    global player_pos, obstacles, small_obstacles, projectiles, obstacle_spawn_timer, small_obstacle_spawn_timer, start_time
    player_pos = [400, 500]
    obstacles = []
    small_obstacles = []
    projectiles = []
    obstacle_spawn_timer = 0
    small_obstacle_spawn_timer = 0
    start_time = time.time()

# Set up fonts
font = pygame.font.SysFont(None, 55)
small_font = pygame.font.SysFont(None, 35)

# Start the game timer
start_time = time.time()
high_score = 0

# Main loop
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif game_over and event.type == pygame.MOUSEBUTTONDOWN:
            mouse_pos = event.pos
            if try_again_button.collidepoint(mouse_pos):
                game_over = False
                reset_game()

    if not game_over:
        # Capture frame from webcam
        ret, frame = cap.read()
        if not ret:
            break
        
        # Flip the frame horizontally
        frame = cv2.flip(frame, 1)
        
        # Detect hand gesture
        gesture_pos, pinching = detect_hand_gesture(frame)
        if gesture_pos:
            player_pos[0] = SCREEN_WIDTH - gesture_pos[0]  # Move in the opposite direction of the finger
            player_pos[1] = gesture_pos[1]

            # Shoot projectile if pinching gesture is detected
            if pinching:
                shoot_projectile()

        # Update obstacle spawn timer
        obstacle_spawn_timer += 1
        small_obstacle_spawn_timer += 1
        if obstacle_spawn_timer >= FPS:  # Spawn every second
            spawn_obstacle()
            obstacle_spawn_timer = 0
        if small_obstacle_spawn_timer >= FPS // 2:  # Spawn every 0.5 seconds
            spawn_small_obstacle()
            small_obstacle_spawn_timer = 0

        # Move obstacles
        for obstacle in obstacles:
            obstacle.y += obstacle_speed
        for small_obstacle in small_obstacles:
            small_obstacle.y += small_obstacle_speed

        # Move projectiles
        for projectile in projectiles:
            projectile.y -= projectile_speed

        # Remove off-screen projectiles
        projectiles = [projectile for projectile in projectiles if projectile.y > 0]

        # Remove off-screen obstacles
        obstacles = [obstacle for obstacle in obstacles if obstacle.y < SCREEN_HEIGHT]
        small_obstacles = [small_obstacle for small_obstacle in small_obstacles if small_obstacle.y < SCREEN_HEIGHT]

        # Check for collisions with projectiles and large obstacles
        for projectile in projectiles[:]:
            for obstacle in obstacles[:]:
                if projectile.colliderect(obstacle):
                    obstacles.remove(obstacle)
                    projectiles.remove(projectile)

        # Check for collisions with player and small obstacles
        if check_collision():
            game_over = True
            level = 0
            collision_time = time.time()
            high_score = int(time.time() - start_time)

        # Update obstacle speed based on level
        update_obstacle_speed()

        # Check level progression
        current_score = int(time.time() - start_time)
        if current_score >= level * level_threshold:
            level += 1
            update_obstacle_speed()

        # Clear screen
        screen.fill((0, 0, 0))

        # Draw obstacles
        for obstacle in obstacles:
            screen.blit(large_obstacle_image, obstacle.topleft)
        for small_obstacle in small_obstacles:
            screen.blit(small_obstacle_image, small_obstacle.topleft)

        # Draw player ship
        ship_rect.center = player_pos
        screen.blit(ship_image, ship_rect.topleft)

        # Draw projectiles
        for projectile in projectiles:
            pygame.draw.rect(screen, (255, 255, 255), projectile)

        # Display high score and level
        display_message(f"High Score: {current_score}", small_font, (255, 255, 255), (10, 10))
        display_message(f"Level: {level}", small_font, (255, 255, 255), (10, 50))

    else:
        # Display game over message and try again button
        screen.fill((0, 0, 0))
        display_message("Game Over!", font, (255, 0, 0), (SCREEN_WIDTH // 2 - 100, SCREEN_HEIGHT // 2 - 50))
        display_message("Restarting in 5 Seconds", font, (255, 255, 255), (SCREEN_WIDTH // 2 - 200, SCREEN_HEIGHT // 2 + 150))
        # try_again_button = pygame.Rect(SCREEN_WIDTH // 2 - 75, SCREEN_HEIGHT // 2 + 20, 150, 50)
        # pygame.draw.rect(screen, (0, 255, 0), try_again_button)
        # display_message("Restart", small_font, (0, 0, 0), (SCREEN_WIDTH // 2 - 60, SCREEN_HEIGHT // 2 + 30))
        display_message(f"High Score: {high_score}", small_font, (255, 255, 255), (10, 10))

        # Restart the game after 5 seconds
        if time.time() - collision_time >= 5:
            game_over = False
            reset_game()

    # Update screen
    pygame.display.flip()

    # Show the frame in fullscreen
    cv2.imshow('full-screen', frame)

    # Cap the frame rate
    clock.tick(FPS)

    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

# Release resources
cap.release()
cv2.destroyAllWindows()
pygame.quit()
