import pygame
import socketio
import eventlet

# Initialize Pygame
pygame.init()

# Constants
WIDTH, HEIGHT = 600, 400
BALL_SPEED = 5
PADDLE_SPEED = 7

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)

# Initialize SocketIO
sio = socketio.Server(cors_allowed_origins='*')
app = socketio.WSGIApp(sio)

# Create the screen
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Pong Game")

# Create paddles and ball
player_paddle = pygame.Rect(50, HEIGHT // 2 - 30, 10, 60)
opponent_paddle = pygame.Rect(WIDTH - 60, HEIGHT // 2 - 30, 10, 60)
ball = pygame.Rect(WIDTH // 2 - 10, HEIGHT // 2 - 10, 20, 20)

# Set initial ball direction
ball_direction = [1, 1]

# Initialize scores
player_score = 0
opponent_score = 0

# Main game loop
def game_loop():
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sio.emit('exit', namespace='/game')
                exit()

        # Move the paddles
        keys = pygame.key.get_pressed()
        if keys[pygame.K_UP] and player_paddle.top > 0:
            player_paddle.y -= PADDLE_SPEED
        if keys[pygame.K_DOWN] and player_paddle.bottom < HEIGHT:
            player_paddle.y += PADDLE_SPEED

        # Send player paddle position to the opponent
        sio.emit('update_paddle', {'y': player_paddle.y}, namespace='/game')

        # Move the ball
        ball.x += BALL_SPEED * ball_direction[0]
        ball.y += BALL_SPEED * ball_direction[1]

        # Ball collisions with walls
        if ball.top <= 0 or ball.bottom >= HEIGHT:
            ball_direction[1] *= -1

        # Ball collisions with paddles
        if ball.colliderect(player_paddle) or ball.colliderect(opponent_paddle):
            ball_direction[0] *= -1

        # Check for scoring
        if ball.left <= 0:
            # Opponent scored
            sio.emit('score', {'player': 'opponent'}, namespace='/game')
        elif ball.right >= WIDTH:
            # Player scored
            sio.emit('score', {'player': 'player'}, namespace='/game')

        # Reset ball position if scored
        if ball.left <= 0 or ball.right >= WIDTH:
            ball.x = WIDTH // 2 - 10
            ball.y = HEIGHT // 2 - 10

        # Draw everything
        screen.fill(BLACK)
        pygame.draw.rect(screen, WHITE, player_paddle)
        pygame.draw.rect(screen, WHITE, opponent_paddle)
        pygame.draw.ellipse(screen, WHITE, ball)

        # Display scores
        font = pygame.font.Font(None, 36)
        player_score_text = font.render(str(player_score), True, WHITE)
        opponent_score_text = font.render(str(opponent_score), True, WHITE)
        screen.blit(player_score_text, (WIDTH // 4, 20))
        screen.blit(opponent_score_text, (3 * WIDTH // 4 - 20, 20))

        # Update the display
        pygame.display.flip()

        # Cap the frame rate
        pygame.time.Clock().tick(30)

# SocketIO event handlers
@sio.on('connect', namespace='/game')
def connect(sid, environ):
    print(f"Player connected: {sid}")
    sio.emit('connected', namespace='/game')

@sio.on('disconnect', namespace='/game')
def disconnect(sid):
    print(f"Player disconnected: {sid}")

@sio.on('update_paddle', namespace='/game')
def update_paddle(sid, data):
    opponent_paddle.y = data['y']

@sio.on('score', namespace='/game')
def score(sid, data):
    global player_score, opponent_score

    if data['player'] == 'player':
        player_score += 1
    elif data['player'] == 'opponent':
        opponent_score += 1

    sio.emit('update_score', {'player_score': player_score, 'opponent_score': opponent_score}, namespace='/game')

# Run the game loop in a separate thread
if __name__ == '__main__':
    eventlet.spawn(game_loop)
    eventlet.wsgi.server(eventlet.listen(('localhost', 5000)), app)
