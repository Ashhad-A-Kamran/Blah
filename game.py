import pygame
import cv2
import mediapipe as mp
import random
import time

# Initialize Pygame
pygame.init()

# Screen dimensions
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Gesture Controlled Game")

# Load the ship image and resize it
ship_image = pygame.image.load('./assets/ship.png')
ship_image = pygame.transform.scale(ship_image, (50, 50))  # Resize to 50x50 pixels
ship_rect = ship_image.get_rect()

# Load the obstacle image and resize it
obstacle_image = pygame.image.load('./assets/rock1.png')
obstacle_image = pygame.transform.scale(obstacle_image, (50, 50))  # Resize to 50x50 pixels

# Game variables
clock = pygame.time.Clock()
FPS = 60
player_pos = [400, 500]
player_speed = 5

# Obstacle variables
obstacle_speed = 5
obstacle_spawn_timer = 0
obstacles = []

# Initialize OpenCV and MediaPipe
cap = cv2.VideoCapture(0)
ret, frame = cap.read()

mp_hands = mp.solutions.hands
hands = mp_hands.Hands(max_num_hands=1, min_detection_confidence=0.7)
mp_draw = mp.solutions.drawing_utils

# High score
high_score = 0
start_time = time.time()

def detect_hand_gesture(frame):
    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    result = hands.process(frame_rgb)
    if result.multi_hand_landmarks:
        for hand_landmarks in result.multi_hand_landmarks:
            mp_draw.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)
            
            # Get the coordinates of the index finger tip
            x = int(hand_landmarks.landmark[mp_hands.HandLandmark.INDEX_FINGER_TIP].x * SCREEN_WIDTH)
            y = int(hand_landmarks.landmark[mp_hands.HandLandmark.INDEX_FINGER_TIP].y * SCREEN_HEIGHT)
            # Flip the x-coordinate to correct the direction
            x = SCREEN_WIDTH - x
            
            return x, y
    return None

def spawn_obstacle():
    x = random.randint(0, SCREEN_WIDTH - 50)  # Random x-coordinate within screen bounds
    y = -50  # Start above the screen
    obstacles.append(pygame.Rect(x, y, 50, 50))

def check_collision():
    player_rect = pygame.Rect(player_pos[0], player_pos[1], 50, 50)
    for obstacle in obstacles:
        if player_rect.colliderect(obstacle):
            return True
    return False

def display_message(text, font, color, position):
    message = font.render(text, True, color)
    screen.blit(message, position)

def reset_game():
    global player_pos, obstacles, obstacle_spawn_timer, start_time
    player_pos = [400, 500]
    obstacles = []
    obstacle_spawn_timer = 0
    start_time = time.time()

# Main loop
running = True
game_over = False

# Set up fonts
font = pygame.font.SysFont(None, 55)
small_font = pygame.font.SysFont(None, 35)

while running:
    cv2.imshow('screen', frame)
    if not ret:
        break
    
    
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
        
        # Detect hand gesture
        gesture_pos = detect_hand_gesture(frame)
        if gesture_pos:
            player_pos[0] = gesture_pos[0]
            player_pos[1] = gesture_pos[1]

        # Update obstacle spawn timer
        obstacle_spawn_timer += 1
        if obstacle_spawn_timer >= FPS:  # Spawn every second
            spawn_obstacle()
            obstacle_spawn_timer = 0
        
        # Move obstacles
        for obstacle in obstacles:
            obstacle.y += obstacle_speed
        
        # Remove obstacles that go beyond the screen
        obstacles = [obstacle for obstacle in obstacles if obstacle.y < SCREEN_HEIGHT]
        
        # Check for collisions
        if check_collision():
            game_over = True
            high_score = int(time.time() - start_time)

        # Clear screen
        screen.fill((0, 0, 0))
        
        # Draw obstacles
        for obstacle in obstacles:
            screen.blit(obstacle_image, obstacle.topleft)
        
        # Draw player ship
        ship_rect.center = player_pos
        screen.blit(ship_image, ship_rect.topleft)
        
        # Display high score
        display_message(f"High Score: {int(time.time() - start_time)}", small_font, (255, 255, 255), (10, 10))
        
    else:
        # Game over screen
        screen.fill((0, 0, 0))
        display_message("Game Over", font, (255, 0, 0), (SCREEN_WIDTH//2 - 100, SCREEN_HEIGHT//2 - 50))
        try_again_button = pygame.Rect(SCREEN_WIDTH//2 - 100, SCREEN_HEIGHT//2 + 20, 200, 50)
        pygame.draw.rect(screen, (0, 255, 0), try_again_button)
        display_message("Try Again", small_font, (0, 0, 0), (SCREEN_WIDTH//2 - 60, SCREEN_HEIGHT//2 + 30))
        display_message(f"High Score: {high_score}", small_font, (255, 255, 255), (10, 10))

    # Update screen
    pygame.display.flip()
    
    # Cap the frame rate
    clock.tick(FPS)

    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

# Release resources
cap.release()
cv2.destroyAllWindows()
pygame.quit()
