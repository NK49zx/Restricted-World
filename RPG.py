from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
import math

# --- Game State and Player Stats ---
game_state = "character_creation" # Can be "character_creation" or "playing"
available_points = 5
selected_stat_index = 0
stat_keys = ["Strength", "Dexterity", "Intelligence"]

# Player class to manage player stats and level
class Player:
    def __init__(self):
        self.base_stats = {
            "Strength": 5,
            "Dexterity": 5,
            "Intelligence": 5,
        }
        self.stats = {
            "Strength": 5,
            "Dexterity": 5,
            "Intelligence": 5,
            "Health": 100,
            "Mana": 50
        }
        self.level = 1
        self.xp = 0
        self.xp_to_next_level = 100
        self.position = [0, 0, 0] # Use a list for mutable position
        self.rotation_angle = 0.0 # Player's facing direction in degrees
        self.speed = 10.0
        self.rotate_speed = 5.0

player = Player()


# Camera-related variables
camera_pos = (0,500,500)
camera_angle = 90

final_x, final_y, final_z = camera_pos

fovY = 120  # Field of view
GRID_LENGTH = 600  # Length of grid lines
rand_var = 423


def draw_text(x, y, text, font=GLUT_BITMAP_HELVETICA_18):
    glColor3f(1,1,1)
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    
    # Set up an orthographic projection that matches window coordinates
    gluOrtho2D(0, 1000, 0, 800)  # left, right, bottom, top

    
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()
    
    # Draw text at (x, y) in screen coordinates
    glRasterPos2f(x, y)
    for ch in text:
        glutBitmapCharacter(font, ord(ch))
    
    # Restore original projection and modelview matrices
    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)


def draw_character_creation_screen():
    """Draws the UI for the character creation state."""
    draw_text(350, 700, "Create Your Character", GLUT_BITMAP_TIMES_ROMAN_24)
    draw_text(250, 650, "Use UP/DOWN to select a stat. Use LEFT/RIGHT to change values.")
    draw_text(380, 620, "Press ENTER to Start")
    
    draw_text(400, 550, f"Points to Spend: {available_points}")
    
    y_offset = 450
    for i, stat in enumerate(stat_keys):
        prefix = "> " if i == selected_stat_index else "  "
        draw_text(400, y_offset, f"{prefix}{stat}: {player.stats[stat]}")
        y_offset -= 40

def draw_player():
    """Draws a wizard-like player model using basic shapes."""
    glPushMatrix()
    
    # Position the entire player model in the world.
    # The floor is at z=0. The robe's height is 75, and it's drawn around the origin.
    # We lift the model by half the robe's height (37.5) on the Z-axis to make it sit on the floor.
    glTranslatef(player.position[0], player.position[1], 37.5)

    # Input rotation of the player to face the correct direction
    glRotatef(player.rotation_angle, 0, 0, 1)
    
    # --- FIX ---
    # Rotate the entire model 90 degrees around the X-axis to make it stand up.
    # This aligns the model's 'up' (its local Y-axis) with the world's 'up' (the global Z-axis).
    glRotatef(90, 1, 0, 0)

    # --- Draw Wizard Robe (Body) ---
    # Using a stretched cube for the robe
    glColor3f(0.3, 0.2, 0.8) # Dark purple
    glPushMatrix()
    glScalef(1, 1.5, 0.7) # Stretch the cube to be taller than it is wide
    glutSolidCube(50)
    glPopMatrix()

    # --- Draw Head ---
    glColor3f(0.9, 0.7, 0.6) # A skin-like color
    glPushMatrix()
    glTranslatef(0, 55, 0) # Position head on top of the body
    glutSolidSphere(20, 20, 20) # Radius, slices, stacks
    glPopMatrix()

    # --- Draw Wizard Hat ---
    glColor3f(0.2, 0.1, 0.6) # Even darker purple for the hat
    glPushMatrix()
    glTranslatef(0, 65, 0) # Position hat on top of the head
    glRotatef(-90, 1, 0, 0) # Rotate the cone to point upwards
    # gluCylinder uses (quadric, base_radius, top_radius, height, slices, stacks)
    # For a cone, top_radius is 0.
    gluCylinder(gluNewQuadric(), 30, 0, 60, 20, 20)
    glPopMatrix()
    
    # --- Draw Arms ---
    # Left Arm
    glPushMatrix()
    glColor3f(0.3, 0.2, 0.8) # Robe color for upper arm
    # Upper arm (from shoulder to elbow)
    glPushMatrix()
    glTranslatef(-30, 20, 0)
    glScalef(1.5, 0.5, 0.5)
    glutSolidCube(20)
    glPopMatrix()
    # Forearm (from elbow forward)
    glPushMatrix()
    glTranslatef(-40, 20, 20)
    glScalef(0.5, 0.5, 1.5)
    glutSolidCube(20)
    glPopMatrix()
    # Fist
    glPushMatrix()
    glColor3f(0.9, 0.7, 0.6) # Skin color for fist
    glTranslatef(-40, 20, 35)
    glutSolidSphere(8, 10, 10)
    glPopMatrix()
    glPopMatrix()

    # Right Arm
    glPushMatrix()
    glColor3f(0.3, 0.2, 0.8) # Robe color for upper arm
    # Upper arm (from shoulder to elbow)
    glPushMatrix()
    glTranslatef(30, 20, 0)
    glScalef(1.5, 0.5, 0.5)
    glutSolidCube(20)
    glPopMatrix()
    # Forearm (from elbow forward)
    glPushMatrix()
    glTranslatef(40, 20, 20)
    glScalef(0.5, 0.5, 1.5)
    glutSolidCube(20)
    glPopMatrix()
    # Fist
    glPushMatrix()
    glColor3f(0.9, 0.7, 0.6) # Skin color for fist
    glTranslatef(40, 20, 35)
    glutSolidSphere(8, 10, 10)
    glPopMatrix()
    glPopMatrix()

    # --- Draw Legs ---
    glColor3f(0.2, 0.2, 0.2) # Dark grey for trousers/boots
    # Left Leg
    glPushMatrix()
    glTranslatef(-15, -45, 0) # Position to the left and below the body
    glScalef(0.6, 1.2, 0.6) # Make it look like a leg
    glutSolidCube(30)
    glPopMatrix()

    # Right Leg
    glPushMatrix()
    glTranslatef(15, -45, 0) # Position to the right and below the body
    glScalef(0.6, 1.2, 0.6) # Make it look like a leg
    glutSolidCube(30)
    glPopMatrix()

    glPopMatrix() # End of player model matrix

def keyboardListener(key, x, y):
    """
    Handles keyboard inputs for player movement, gun rotation, camera updates, and cheat mode toggles.
    """
    global game_state, camera_pos, camera_angle
    if game_state == "character_creation":
        if key == b'\r': # Enter key
            game_state = "playing"

    elif game_state == "playing":
        # --- FIX ---
        # The movement calculation must use the same angle as the visual rotation
        # in draw_player(), which includes the -90 degree offset. This ensures
        # "forward" is always in the direction the player model is facing.
        angle_rad = math.radians(player.rotation_angle-90)
        move_x = math.cos(angle_rad)
        move_y = math.sin(angle_rad)

        # Temporary new position for boundary check
        new_pos_x = player.position[0]
        new_pos_y = player.position[1]
        
        # W for forward movement
        if key == b'w':
            new_pos_x += move_x * player.speed
            new_pos_y += move_y * player.speed
        # S for backward movement
        if key == b's':
            new_pos_x -= move_x * player.speed
            new_pos_y -= move_y * player.speed
        
        # A to rotate left
        if key == b'a':
            player.rotation_angle += player.rotate_speed
        # D to rotate right
        if key == b'd':
            player.rotation_angle -= player.rotate_speed

        # Boundary check to keep the player within the walls
        bound = GRID_LENGTH - 40 # A small buffer from the wall edge
        if -bound <= new_pos_x <= bound and -bound <= new_pos_y <= bound:
            player.position[0] = new_pos_x
            player.position[1] = new_pos_y

def specialKeyListener(key, x, y):
    """
    Handles special key inputs (arrow keys) for adjusting the camera angle and height.
    """
    global camera_pos, camera_angle, game_state, selected_stat_index, available_points, final_x, final_y, final_z

    if game_state == "character_creation":
        if key == GLUT_KEY_UP:
            selected_stat_index = (selected_stat_index - 1 + len(stat_keys)) % len(stat_keys)
        elif key == GLUT_KEY_DOWN:
            selected_stat_index = (selected_stat_index + 1) % len(stat_keys)
        elif key == GLUT_KEY_RIGHT:
            if available_points > 0:
                stat_to_change = stat_keys[selected_stat_index]
                player.stats[stat_to_change] += 1
                available_points -= 1
        elif key == GLUT_KEY_LEFT:
            stat_to_change = stat_keys[selected_stat_index]
            # Prevent going below the base stat value
            if player.stats[stat_to_change] > player.base_stats[stat_to_change]:
                player.stats[stat_to_change] -= 1
                available_points += 1

    elif game_state == "playing":
        if key == GLUT_KEY_UP:
            final_z += 5
            
        if key == GLUT_KEY_DOWN:
            final_z -= 5
            
        if key == GLUT_KEY_RIGHT:
            camera_angle += 2
            r = math.sqrt(final_x**2 + final_y**2)
            final_x = r * math.cos(math.radians(camera_angle))
            final_y = r * math.sin(math.radians(camera_angle))
                
        if key == GLUT_KEY_LEFT:
            camera_angle -= 2
            r = math.sqrt(final_x**2 + final_y**2)
            final_x = r * math.cos(math.radians(camera_angle))
            final_y = r * math.sin(math.radians(camera_angle))
        
        camera_pos = (final_x, final_y, final_z)


def mouseListener(button, state, x, y):
    """
    Handles mouse inputs for firing bullets (left click) and toggling camera mode (right click).
    """
        # # Left mouse button fires a bullet
        # if button == GLUT_LEFT_BUTTON and state == GLUT_DOWN:

        # # Right mouse button toggles camera tracking mode
        # if button == GLUT_RIGHT_BUTTON and state == GLUT_DOWN:


def setupCamera():
    """
    Configures the camera's projection and view settings.
    Uses a perspective projection and positions the camera to look at the target.
    """
    glMatrixMode(GL_PROJECTION)  # Switch to projection matrix mode
    glLoadIdentity()  # Reset the projection matrix
    # Set up a perspective projection (field of view, aspect ratio, near clip, far clip)
    gluPerspective(fovY, 1.25, 0.1, 1500) # Think why aspect ration is 1.25?
    glMatrixMode(GL_MODELVIEW)  # Switch to model-view matrix mode
    glLoadIdentity()  # Reset the model-view matrix

    # Extract camera position and look-at target
    x, y, z = camera_pos
    # Position the camera and set its orientation
    gluLookAt(x, y, z,  # Camera position
              0, 0, 0,  # Look-at target
              0, 0, 1)  # Up vector (z-axis)


def idle():
    """
    Idle function that runs continuously:
    - Triggers screen redraw for real-time updates.
    """
    # Ensure the screen updates with the latest changes
    glutPostRedisplay()


def showScreen():
    """
    Display function to render the game scene:
    - Clears the screen and sets up the camera.
    - Draws everything of the screen
    """
    # Clear color and depth buffers
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glLoadIdentity()  # Reset modelview matrix
    glViewport(0, 0, 1000, 800)  # Set viewport size

    setupCamera()  # Configure camera perspective
def showScreen():
    """
    Display function to render the game scene:
    - Clears the screen and sets up the camera.
    - Draws everything of the screen
    """
    # Clear color and depth buffers
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glLoadIdentity()  # Reset modelview matrix
    glViewport(0, 0, 1000, 800)  # Set viewport size

    if game_state == "character_creation":
        draw_character_creation_screen()
    elif game_state == "playing":
        setupCamera()  # Configure camera perspective

        GRID_SIZE = 25  # The number of tiles in one dimension
        tile_size = (GRID_LENGTH * 2) / GRID_SIZE
        
        for row in range(GRID_SIZE):
            for col in range(GRID_SIZE):
                # Calculate the coordinates for the corners of the tile
                x1 = -GRID_LENGTH + (col * tile_size)
                x2 = x1 + tile_size
                y1 = -GRID_LENGTH + (row * tile_size)
                y2 = y1 + tile_size
                
                # Alternate colors for a checkerboard pattern
                if (row+col) % 2 == 0:
                    glColor3f(1.0, 1.0, 1.0) # White
                else:
                    glColor3f(0.7, 0.5, 0.95)  # Lavender
                
                glBegin(GL_QUADS)
                glVertex3f(x1, y1, 0)
                glVertex3f(x2, y1, 0)
                glVertex3f(x2, y2, 0)
                glVertex3f(x1, y2, 0)
                glEnd()
            
        w_height = 100 
        glColor3f(1, 1, 1) 
        glBegin(GL_QUADS)
        glVertex3f(-GRID_LENGTH, GRID_LENGTH, 0)
        glVertex3f(GRID_LENGTH, GRID_LENGTH, 0)
        glVertex3f(GRID_LENGTH, GRID_LENGTH, w_height)
        glVertex3f(-GRID_LENGTH, GRID_LENGTH, w_height)
        glEnd()

        glColor3f(0, 1, 1) 
        glBegin(GL_QUADS)
        glVertex3f(-GRID_LENGTH, -GRID_LENGTH, 0)
        glVertex3f(GRID_LENGTH, -GRID_LENGTH, 0)
        glVertex3f(GRID_LENGTH, -GRID_LENGTH, w_height)
        glVertex3f(-GRID_LENGTH, -GRID_LENGTH, w_height)
        glEnd()

        glColor3f(0, 0, 1) 
        glBegin(GL_QUADS)
        glVertex3f(GRID_LENGTH, -GRID_LENGTH, 0)
        glVertex3f(GRID_LENGTH, GRID_LENGTH, 0)
        glVertex3f(GRID_LENGTH, GRID_LENGTH, w_height)
        glVertex3f(GRID_LENGTH, -GRID_LENGTH, w_height)
        glEnd()

        glColor3f(0, 1, 0) 
        glBegin(GL_QUADS)
        glVertex3f(-GRID_LENGTH, -GRID_LENGTH, 0)
        glVertex3f(-GRID_LENGTH, GRID_LENGTH, 0)
        glVertex3f(-GRID_LENGTH, GRID_LENGTH, w_height)
        glVertex3f(-GRID_LENGTH, -GRID_LENGTH, w_height)
        glEnd()

        # --- Display Player Stats ---
        draw_text(10, 770, f"Level: {player.level} (XP: {player.xp}/{player.xp_to_next_level})")
        y_offset = 740
        for stat, value in player.stats.items():
            draw_text(10, y_offset, f"{stat}: {value}")
            y_offset -= 30
        
        # --- Draw the Player Model ---
        draw_player()

    # Swap buffers for smooth rendering (double buffering)
    glutSwapBuffers()


# Main function to set up OpenGL window and loop
def main():
    glutInit()
    glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB | GLUT_DEPTH)  # Double buffering, RGB color, depth test
    glutInitWindowSize(1000, 800)  # Window size
    glutInitWindowPosition(0, 0)  # Window position
    wind = glutCreateWindow(b"3D OpenGL Intro")  # Create the window

    glutDisplayFunc(showScreen)  # Register display function
    glutKeyboardFunc(keyboardListener)  # Register keyboard listener
    glutSpecialFunc(specialKeyListener)
    glutMouseFunc(mouseListener)
    glutIdleFunc(idle)  # Register the idle function to move the bullet automatically

    glutMainLoop()  # Enter the GLUT main loop

if __name__ == "__main__":
    main()
