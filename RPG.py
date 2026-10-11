from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
import math
import random
import time

# --- Time Management ---
last_time = time.time()
total_time = 0.0

# --- Game State and Player Stats ---
game_state = "character_creation" 
creation_step = "stats"
available_points = 5
selected_stat_index = 0
stat_keys = ["Strength", "Dexterity", "Intelligence"]
god_mode = False # Cheat mode flag

DEMONIC_GIBBERISH = [
    "Klatu... Verata... N... *cough*",
    "Ph'nglui mglw'nafh Cthulhu R'lyeh wgah'nagl fhtagn.",
    "Iä! Iä! Yog-Sothoth!",
    "(The air grows cold and a low growl reverberates in your skull.)"
]

# --- Visual Effects Management ---
vfx_timers = {}


# --- Dialogue and Interaction State ---
collided_npc = None
previous_camera_pos = None
dialogue_options = []
combat_log = [] # Stores messages during a fight
dialogue_text = "" # Stores the NPC's current dialogue line
interaction_range = 75.0 # The radius within which the player can interact with an NPC
combat_menu_state = "main"

# --- Spell Data ---
MANA_COSTS = {
    "Heal": 15, "Protection": 10, "Buff": 10,
    "Fireball": 20, "Reflect": 12
}

# --- Dropped Item Data ---
class DroppedItem:
    def __init__(self, position, item_type='loot', value=25):
        self.position = position
        self.collision_radius = 20.0
        self.item_type = item_type
        self.value = value # Used for XP amount

dropped_items = [] # A list to hold all items on the ground

class BossKey:
    def __init__(self, position):
        self.position = position
        self.collision_radius = 25.0

class BossDoor:
    def __init__(self, center_x, center_y):
        self.center = [center_x, center_y]
        self.state = 'hidden' 
        self.angle = 0.0
        self.animation_speed = 45.0  # Door opening speed
        self.key = BossKey([center_x, center_y - 100, 50]) # Key floats in front
        self.key_present = False

    def reveal(self):
        if self.state == 'hidden':
            self.state = 'revealed'
            self.key_present = True
            print("A mysterious door has been revealed!")

    def open(self):
        if self.state == 'revealed':
            self.state = 'opening'
            self.key_present = False
            # Add both the boss room AND the doorway connector to the walkable areas
            WALKABLE_RECTS.append(BOSS_ROOM_BOUNDS)
            WALKABLE_RECTS.append(BOSS_DOORWAY_RECT)
            spawn_boss()

    def update(self, delta_time):
        if self.state == 'opening':
            self.angle += self.animation_speed * delta_time
            if self.angle >= 90.0:
                self.angle = 180.0
                self.state = 'open'

    def draw_key(self):
        if not self.key_present:
            return
        glPushMatrix()
        bob_height = 10 * (1 + math.sin(total_time * 1.5))
        glTranslatef(self.key.position[0], self.key.position[1], self.key.position[2] + bob_height)
        glRotatef(total_time * 60, 0, 0, 1) # Rotate the key
        glScalef(0.4, 0.4, 0.4)
        
        # Key model
        glColor3f(0.9, 0.7, 0.1) # Gold color
        # Ring
        glutSolidTorus(5, 20, 10, 20)
        # Stem
        glPushMatrix()
        glScalef(0.2, 1.5, 0.2)
        glTranslatef(0, -25, 0)
        glutSolidCube(30)
        glPopMatrix()
        # Teeth
        glTranslatef(0, -60, 0)
        glScalef(0.6, 0.2, 0.2)
        glutSolidCube(25)
        glPopMatrix()

    def draw(self):
        if self.state == 'hidden':
            return

        self.draw_key()

        # Draw the grand door
        glPushMatrix()
        glTranslatef(self.center[0], self.center[1], DOOR_HEIGHT / 2)
        # Hinge is on the left side, so we translate to it, rotate, then translate back
        glTranslatef(-DOOR_WIDTH / 2, 0, 0)
        glRotatef(self.angle, 0, 0, 1)
        glTranslatef(DOOR_WIDTH / 2, 0, 0)
        
        glScalef(DOOR_WIDTH, 15, DOOR_HEIGHT) # Make it thick and imposing
        
        # Base color
        glColor3f(0.1, 0.05, 0.05)
        glutSolidCube(1)
        
        # Decorative trim
        glColor3f(0.8, 0.6, 0.1) # Gold trim
        glPushMatrix()
        glScalef(1.01, 1.01, 1.01)
        glutWireCube(1)
        glPopMatrix()
        
        glPopMatrix()

boss_door = BossDoor(0, 1200) # Centered on the front wall

# --- Manor Layout Definitions ---
# Main grid size now represents the entire manor extent
GRID_LENGTH = 1300
CENTRAL_HALL_WIDTH = 200
WING_WIDTH = 500
WING_LENGTH = 400
WALL_HEIGHT = 250
DOOR_WIDTH = 250
DOOR_HEIGHT = 220

# Define the boundaries for each wing for NPC spawning and prop placement
# (x_min, x_max, y_min, y_max)
WING_BOUNDS = [
    # Right Wings
    (CENTRAL_HALL_WIDTH, CENTRAL_HALL_WIDTH + WING_WIDTH, 800, 800 + WING_LENGTH), # Front-Right
    (CENTRAL_HALL_WIDTH, CENTRAL_HALL_WIDTH + WING_WIDTH, -200, 200),             # Middle-Right
    (CENTRAL_HALL_WIDTH, CENTRAL_HALL_WIDTH + WING_WIDTH, -1200, -800),           # Back-Right
    # Left Wings
    (-CENTRAL_HALL_WIDTH - WING_WIDTH, -CENTRAL_HALL_WIDTH, 800, 800 + WING_LENGTH), # Front-Left
    (-CENTRAL_HALL_WIDTH - WING_WIDTH, -CENTRAL_HALL_WIDTH, -200, 200),             # Middle-Left
    (-CENTRAL_HALL_WIDTH - WING_WIDTH, -CENTRAL_HALL_WIDTH, -1200, -800),           # Back-Left
]
BOSS_ROOM_BOUNDS = (-CENTRAL_HALL_WIDTH, CENTRAL_HALL_WIDTH, 1200, 1200 + WING_LENGTH)

# Define walkable areas for player collision detection
PLAYER_COLLISION_BUFFER = 20 # Half of player's width

DOORWAY_Y_CENTERS = [1000, 0, -1000]
DOORWAY_RECTS = []
for y_center in DOORWAY_Y_CENTERS:
    y_min_door = y_center - DOOR_WIDTH / 2
    y_max_door = y_center + DOOR_WIDTH / 2
    # Right doorways connecting hall to right wings
    DOORWAY_RECTS.append((
        CENTRAL_HALL_WIDTH - PLAYER_COLLISION_BUFFER, 
        CENTRAL_HALL_WIDTH + 1, # Span the wall, +1 to include wing start
        y_min_door, 
        y_max_door
    ))
    # Left doorways connecting hall to left wings
    DOORWAY_RECTS.append((
        -CENTRAL_HALL_WIDTH - 1, 
        -CENTRAL_HALL_WIDTH + PLAYER_COLLISION_BUFFER, # Span the wall, -1 to include wing end
        y_min_door, 
        y_max_door
    ))

# Define a specific walkable rectangle for the boss doorway
BOSS_DOORWAY_RECT = (
    -DOOR_WIDTH / 2, 
    DOOR_WIDTH / 2, 
    1200 - PLAYER_COLLISION_BUFFER, 
    1200 + PLAYER_COLLISION_BUFFER
)

WALKABLE_RECTS = [
    # Central Hall
    (-CENTRAL_HALL_WIDTH + PLAYER_COLLISION_BUFFER, CENTRAL_HALL_WIDTH - PLAYER_COLLISION_BUFFER, -1200 + PLAYER_COLLISION_BUFFER, 1200 - PLAYER_COLLISION_BUFFER),
    # Wings
    *WING_BOUNDS,
    # Boss Room
    BOSS_ROOM_BOUNDS,
    # Doorway connectors to bridge the gap
    *DOORWAY_RECTS
]


# A helper function for player collision
def is_valid_position(x, y):
    """Checks if the player's target position is within a walkable area."""
    for rect in WALKABLE_RECTS:
        # Check if the point is inside any of the walkable rectangles
        if (rect[0] <= x <= rect[1] and
            rect[2] <= y <= rect[3]):
            return True
    return False


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
        self.position = [0, 0, 0] 
        self.rotation_angle = 0.0 
        self.speed = 10.0
        self.rotate_speed = 5.0
        self.main_quests = ["Get out of this world"]
        self.weapon = "Sword" # Default weapon
        self.weapon_options = ["Sword", "Magic Staff"]
        self.protection_turns = 0
        self.buff_turns = 0
        self.reflect_turns = 0
        self.debuff_turns = 0
        self.inventory = {"Healing Potion": 1, "Mana Potion": 1, "Mysterious Potion": 0} # Start with one of each
        self.collision_radius = 20.0



player = Player()

# --- NPC Data ---
class NPC:
    def __init__(self, position, composition, z_offset, animation_params, is_rogue, has_quest, enemy_type=None):
        self.position = position
        self.composition = composition
        self.z_offset = z_offset
        self.animation_params = animation_params
        self.is_rogue = is_rogue
        self.has_quest = has_quest
        self.enemy_type = enemy_type
        self.stats = { "Health": 50, "Strength": 5 }
        self.has_given_quest = False
        self.has_given_help = False
        self.xp_awarded = False
        self.is_revealed = False


npcs = [] # A list to hold all the NPC objects in the world

# --- NPC Part Pools ---
# Blueprint for a body part.
torso_pool = [
    {'shape': 'cube', 'params': (60,), 'scale': (1.0, 1.5, 0.8)},
    {'shape': 'sphere', 'params': (40, 20, 20), 'scale': (1.2, 1.0, 1.2)},
]
head_pool = [
    {'shape': 'sphere', 'params': (20, 20, 20), 'position': (0, 65, 0)},
    {'shape': 'cube', 'params': (30,), 'position': (0, 60, 0)},
]
legs_pool = [
    {'shape': 'cube', 'params': (30,), 'scale': (0.6, 1.5, 0.6)},
    {'shape': 'cone', 'params': (15, 60, 10, 5), 'scale': (1.0, 1.0, 1.0)},
]

ENEMY_CATALOG = {
    "Slime": {
        "stats": {"Health": 30, "Strength": 3},
        "dialogue": "Gloop... glorp... (It seems hostile!)",
        "composition": [
            # A slime is just a single, large sphere body.
            {'shape': 'sphere', 'params': (50, 20, 20), 'scale': (1.2, 0.8, 1.2), 'color': (0.435, 0.635, 0.815), 'position': (0,0,-45)}
        ]
    },
    "Goblin": {
        "stats": {"Health": 50, "Strength": 6},
        "dialogue": "You'll make a fine meal for my clan!",
        "composition": [
            # Goblins are short and blocky
            {'shape': 'cube', 'params': (40,), 'scale': (1.0, 1.2, 1.0), 'color': (0.1, 0.5, 0.1), 'position': (0,0,0)}, # Torso
            {'shape': 'sphere', 'params': (15, 20, 20), 'color': (0.2, 0.6, 0.2), 'position': (0, 45, 0)}, # Head
            {'shape': 'cube', 'params': (20,), 'scale': (0.6, 1.8, 0.6), 'color': (0.1, 0.4, 0.1), 'position': (-15, -40, 0)}, # Left Leg
            {'shape': 'cube', 'params': (20,), 'scale': (0.6, 1.8, 0.6), 'color': (0.1, 0.4, 0.1), 'position': (15, -40, 0)}, # Right Leg
        ]
    },
    "Orc": {
        "stats": {"Health": 80, "Strength": 10},
        "dialogue": "RAAARGH! You interrupted my brooding!",
        "composition": [
            # Orcs are tall and very blocky
            {'shape': 'cube', 'params': (60,), 'scale': (1.2, 1.6, 1.0), 'color': (0.4, 0.3, 0.1), 'position': (0,0,0)}, # Torso
            {'shape': 'cube', 'params': (35,), 'color': (0.5, 0.4, 0.2), 'position': (0, 70, 0)}, # Head
            {'shape': 'cube', 'params': (30,), 'scale': (0.8, 1.5, 0.8), 'color': (0.3, 0.2, 0.1), 'position': (-25, -65, 0)}, # Left Leg
            {'shape': 'cube', 'params': (30,), 'scale': (0.8, 1.5, 0.8), 'color': (0.3, 0.2, 0.1), 'position': (25, -65, 0)}, # Right Leg
        ]
    },
    
    "Archdemon": {
        "stats": {"Health": 250, "Strength": 15},
        "dialogue": "You dare trespass into my sanctum? Your soul is forfeit!",
        "composition": [
            # Main Body (Larger and more imposing)
            {'shape': 'cube', 'params': (80,), 'scale': (1.2, 1.8, 1.0), 'color': (0.6, 0.1, 0.1), 'position': (0,0,0)}, # Torso
            # Head
            {'shape': 'sphere', 'params': (25, 20, 20), 'color': (0.5, 0.1, 0.1), 'position': (0, 90, 0)},
            # Legs
            {'shape': 'cube', 'params': (40,), 'scale': (0.8, 1.8, 0.8), 'color': (0.4, 0.1, 0.1), 'position': (-30, -90, 0)},
            {'shape': 'cube', 'params': (40,), 'scale': (0.8, 1.8, 0.8), 'color': (0.4, 0.1, 0.1), 'position': (30, -90, 0)},
            # Horns (Cones)
            {'shape': 'cone', 'params': (10, 50, 10, 5), 'color': (0.3, 0.3, 0.3), 'position': (-20, 110, 20), 'rotation': (0, 0, -30)},
            {'shape': 'cone', 'params': (10, 50, 10, 5), 'color': (0.3, 0.3, 0.3), 'position': (20, 110, 20), 'rotation': (0, 0, 30)},
        ]
    }
}

# List of standard enemies, excluding the boss
STANDARD_ENEMIES = [enemy for enemy in ENEMY_CATALOG if enemy != "Archdemon"]

# Camera-related variables
camera_pos = (0,500,500)
camera_angle = 90

final_x, final_y, final_z = camera_pos

fovY = 120  # Field of view

def reset_game():
    """Resets all game variables to their initial state for a new game."""
    global player, npcs, dropped_items, boss_door, game_state, creation_step, available_points, selected_stat_index, combat_log
    
    # Reset player and game objects
    player = Player()
    npcs.clear()
    dropped_items.clear()
    boss_door = BossDoor(0, 1200)
    combat_log.clear()
    
    # Reset character creation and game state
    available_points = 5
    selected_stat_index = 0
    creation_step = "stats"
    game_state = "character_creation"
    
    print("Game has been reset.")

def draw_game_over_screen():
    """Draws the game over screen."""
    draw_spooky_background()
    glClear(GL_DEPTH_BUFFER_BIT)
    draw_text(420, 500, "GAME OVER", GLUT_BITMAP_TIMES_ROMAN_24)
    draw_text(380, 400, "Your journey ends here...")
    draw_text(370, 200, "Press ENTER to Restart")

def draw_victory_background():
    """Draws a triumphant background for the victory screen."""
    glMatrixMode(GL_PROJECTION); glPushMatrix(); glLoadIdentity()
    gluOrtho2D(0, 1000, 0, 800)
    glMatrixMode(GL_MODELVIEW); glPushMatrix(); glLoadIdentity()
    
    # Gold gradient background
    glBegin(GL_QUADS)
    glColor3f(0.1, 0.1, 0.1) # Dark grey 
    glVertex2f(0, 0); glVertex2f(1000, 0)
    glColor3f(0.9, 0.7, 0.1) # Bright gold
    glVertex2f(1000, 800); glVertex2f(0, 800)
    glEnd()

    glPopMatrix(); glMatrixMode(GL_PROJECTION); glPopMatrix(); glMatrixMode(GL_MODELVIEW)

def draw_victory_screen():
    """Draws the victory screen."""
    draw_victory_background()
    glClear(GL_DEPTH_BUFFER_BIT)
    draw_text(430, 500, "VICTORY", GLUT_BITMAP_TIMES_ROMAN_24)
    draw_text(320, 400, "You have escaped the Restricted World.")
    draw_text(370, 200, "Press ENTER to Play Again")

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

def draw_spooky_background():
    """Draws an animated spooky background for the character creation screen."""
    glMatrixMode(GL_PROJECTION); glPushMatrix(); glLoadIdentity()
    gluOrtho2D(0, 1000, 0, 800)
    glMatrixMode(GL_MODELVIEW); glPushMatrix(); glLoadIdentity()
    
    # Dark gradient background
    glBegin(GL_QUADS)
    glColor3f(0.0, 0.0, 0.0) # Black 
    glVertex2f(0, 0); glVertex2f(1000, 0)
    glColor3f(0.8, 0.1, 0.1) # Dark purple 
    glVertex2f(1000, 800); glVertex2f(0, 800)
    glEnd()


    glPopMatrix(); glMatrixMode(GL_PROJECTION); glPopMatrix(); glMatrixMode(GL_MODELVIEW)

def draw_character_creation_screen():
    draw_spooky_background()
    glClear(GL_DEPTH_BUFFER_BIT)
    if creation_step == "stats":
        draw_text(390, 700, "Restricted World", GLUT_BITMAP_TIMES_ROMAN_24)
        draw_text(390, 650, "Prepare Your Escape")
        draw_text(400, 550, f"Points to Spend: {available_points}")
        y_offset = 450
        for i, stat in enumerate(stat_keys):
            prefix = "> " if i == selected_stat_index else "  "; draw_text(400, y_offset, f"{prefix}{stat}: {player.stats[stat]}"); y_offset -= 40
        draw_text(380, 200, "Press ENTER to Continue")
    elif creation_step == "weapon":
        draw_text(380, 700, "Choose Your Weapon", GLUT_BITMAP_TIMES_ROMAN_24)
        draw_text(390, 650, "Prepare Your Escape")
        draw_text(420, 500, f"< {player.weapon} >")
        draw_text(380, 200, "Press ENTER to Start Game")

def draw_quests():
    """Draws the main quest list on the top right of the screen."""
    draw_text(750, 770, "Main Quests:", font=GLUT_BITMAP_HELVETICA_18)
    y_offset = 740
    for quest in player.main_quests:
        draw_text(750, y_offset, f"- {quest}")
        y_offset -= 30

def draw_combat_screen():
    """Draws the UI for the combat state."""
    if not collided_npc: return
    draw_text(50, 750, f"Player HP: {player.stats['Health']} | Mana: {player.stats['Mana']}")
    draw_text(700, 750, f"{collided_npc.enemy_type} HP: {collided_npc.stats['Health']}")
    y_offset = 150
    for i, option in enumerate(dialogue_options):
        draw_text(50, y_offset, f"{i+1}. {option}"); y_offset -= 40
    y_offset = 500
    for message in combat_log[-5:]:
        draw_text(50, y_offset, message); y_offset -= 30

def draw_dialogue_screen():
    """Draws the UI for the dialogue state."""
    if not collided_npc:
        return

    # NPC dialogue at the top left
    draw_text(50, 750, dialogue_text)
    
    # player options at the bottom left
    y_offset = 150
    for i, option in enumerate(dialogue_options):
        draw_text(50, y_offset, f"{i+1}. {option}")
        y_offset -= 40
    
def generate_and_spawn_npc(is_rogue, wing_bounds):
    """Generates a composite NPC from the pools and spawns it on the map."""
    composition = []
    # Choose a torso and assign its color
    torso = random.choice(torso_pool).copy()
    torso['position'] = (0, 0, 0) # Torso is the center
    torso['color'] = (random.random(), random.random(), random.random())
    composition.append(torso)
    
    # Choose a head and assign its color
    head = random.choice(head_pool).copy()
    head['color'] = (random.random(), random.random(), random.random())
    composition.append(head)

    # Choose legs, assign a color, and create a left and right version
    leg_blueprint = random.choice(legs_pool).copy()
    leg_color = (random.random(), random.random(), random.random())
    
    # Raised the leg's Y position to connect with the torso.
    leg_y_position = -45
    
    # --- Calculate height offset based on chosen legs ---
    lowest_y_point = leg_y_position  # Base position of legs
    leg_shape = leg_blueprint['shape']
    if leg_shape == 'cube':
        scaled_height = leg_blueprint['params'][0] * leg_blueprint['scale'][1]
        lowest_y_point -= scaled_height / 2.0
    elif leg_shape == 'cone':
        scaled_height = leg_blueprint['params'][1] * leg_blueprint['scale'][1]
        lowest_y_point -= scaled_height
    
    z_offset = abs(lowest_y_point) * 0.5
    
    left_leg = leg_blueprint.copy()
    left_leg['position'] = (-20, leg_y_position, 0)
    left_leg['color'] = leg_color
    composition.append(left_leg)
    
    right_leg = leg_blueprint.copy()
    right_leg['position'] = (20, leg_y_position, 0)
    right_leg['color'] = leg_color
    composition.append(right_leg)
    
    # Determine if NPC is rogue
    has_quest = False
    enemy_type = None #NOT USED

    if is_rogue:
        # If the NPC is a rogue, pick a random enemy type from the catalog
        enemy_type = random.choice(STANDARD_ENEMIES)
    elif random.random() < 0.4: 
        has_quest = True #NOT USED

    # Get a random position within the specified wing
    x_min, x_max, y_min, y_max = wing_bounds
    x = random.uniform(x_min + 50, x_max - 50)
    y = random.uniform(y_min + 50, y_max - 50)
    position = [x, y, 0]

    # Generate and store unique animation parameters for this NPC ---
    animation_params = {
        'phase_offset': random.uniform(0, 2 * math.pi), # Random start point in the animation cycle
        'scale_factor': random.uniform(0.05, 0.1), 
        'scale_speed': random.uniform(2.0, 4.0)
    }
    
    # Create the NPC instance, passing the calculated offset
    new_npc = NPC(position, composition, z_offset, animation_params, is_rogue, has_quest, enemy_type)
    npcs.append(new_npc)


def draw_dropped_item(item):
    """Draws a 3D model for a dropped item."""
    glPushMatrix()
    # Position the item and make it bob up and down
    bob_height = 10 * (1 + math.sin(total_time * 2))
    glTranslatef(item.position[0], item.position[1], 10 + bob_height)
    glScalef(0.3, 0.3, 0.3)
    glRotatef(total_time * 50, 0, 0, 1)
    glRotatef(90, 1, 0, 0)
    
    if item.item_type == 'loot':
        # Model for a loot bag
        glColor3f(0.5, 0.3, 0.1) # Brown
        glutSolidSphere(20, 10, 10)
        glTranslatef(0, 0, 15)
        glColor3f(0.8, 0.8, 0.2) # Gold tie
        glutSolidCube(15)
    
    elif item.item_type == 'xp':
        # Model for an XP Orb
        glColor3f(0.2, 0.5, 1.0) # Bright Blue
        glutSolidSphere(25, 15, 15)
        # glow effect
        pulse_scale = 1.0 + 0.1 * math.sin(total_time * 4)
        glScalef(pulse_scale, pulse_scale, pulse_scale)
        glColor4f(0.5, 0.8, 1.0, 0.5)
        glutSolidSphere(28, 15, 15)

    glPopMatrix()

# --- Weapon Drawing Functions ---
def draw_sword(override_color=None):
    glPushMatrix()
    glColor3f(*(override_color if override_color else (0.7, 0.7, 0.8))); glPushMatrix(); glScalef(0.2, 1.5, 0.1); glutSolidCube(50); glPopMatrix()
    glColor3f(*(override_color if override_color else (0.6, 0.4, 0.2))); glPushMatrix(); glTranslatef(0, -45, 0); glScalef(0.5, 0.2, 0.2); glutSolidCube(30); glPopMatrix()
    glPushMatrix(); glTranslatef(0, -55, 0); glScalef(0.15, 0.4, 0.15); glutSolidCube(40); glPopMatrix()
    glColor3f(*(override_color if override_color else (0.8, 0.8, 0.2))); glPushMatrix(); glTranslatef(0, -70, 0); glutSolidSphere(7, 10, 10); glPopMatrix()
    glPopMatrix()

def draw_magic_staff(override_color=None):
    glPushMatrix()
    glColor3f(*(override_color if override_color else (0.5, 0.3, 0.1))); glPushMatrix(); glScalef(0.1, 2.5, 0.1); glutSolidCube(60); glPopMatrix()
    glColor3f(*(override_color if override_color else (0.2, 0.8, 1.0))); glPushMatrix(); glTranslatef(0, 80, 0); glutSolidSphere(12, 20, 20); glPopMatrix()
    glPopMatrix()

def draw_npc(npc, is_in_dialogue=False, override_color=None):
    """Draws a single composite NPC."""
    glPushMatrix()

    # Calculate the animation scale first, so it can be used in both states.
    phase_offset = npc.animation_params['phase_offset']
    scale_factor = npc.animation_params['scale_factor']
    scale_speed = npc.animation_params['scale_speed']
    breathing_scale = 1.0 + scale_factor * math.sin(total_time * scale_speed + phase_offset)

    if is_in_dialogue:
        glTranslatef(800, 180, 0)
        # Applied the breathing_scale
        glScalef(1.2 * breathing_scale, 1.2 * breathing_scale, 1.2 * breathing_scale)
        glRotatef(-90, 0, 0, 1)
    else:
        # Used the pre-calculated z_offset
        glTranslatef(npc.position[0], npc.position[1], npc.z_offset)
        
        # Applied rotation to face the player
        dx = player.position[0] - npc.position[0]
        dy = player.position[1] - npc.position[1]
        angle_to_player = math.degrees(math.atan2(dy, dx))
        glRotatef(angle_to_player - 90, 0, 0, 1)
        # Applied the breathing_scale
        glScalef(0.5 * breathing_scale, 0.5 * breathing_scale, 0.5 * breathing_scale)
    
        if npc.enemy_type == "Archdemon":
            glScalef(2, 2, 2)
    
    glRotatef(90, 1, 0, 0)

    # Iterate and draw each part of the NPC's body
    for part in npc.composition:
        glPushMatrix()
        glColor3f(*(override_color if override_color else part['color']))
        if 'position' in part:
            glTranslatef(*part['position'])
        if 'rotation' in part:
            glRotatef(part['rotation'][2], 0, 0, 1) # Z-axis rotation for horns
        if 'scale' in part:
            glScalef(*part['scale'])
        if part['shape'] == 'cube':
            glutSolidCube(*part['params'])
        elif part['shape'] == 'sphere':
            glutSolidSphere(*part['params'])
        elif part['shape'] == 'cone':
            glPushMatrix()
            glRotatef(90, 1, 0, 0) # Orient the cone to point up
            gluCylinder(gluNewQuadric(), part['params'][0], 0, part['params'][1], part['params'][2], part['params'][3])
            glPopMatrix()
        glPopMatrix()

    glPopMatrix()

def draw_player_hand_and_weapon(override_color=None):
    """Draws a first-person view of the player's weapon on the right."""
    glPushMatrix()
    # Positioned on the right side of the screen
    glTranslatef(700, 110, 10)
    
    # Weapon
    glPushMatrix()
    # Scale the weapon
    glScalef(1.2, 1.2, 1.2)
    glRotatef(110, 1, 0, 0)
    if player.weapon == "Sword":
        draw_sword(override_color)
    elif player.weapon == "Magic Staff":
        draw_magic_staff(override_color=None)
    glPopMatrix()
    
    glPopMatrix()

def draw_player():
    """Draws a wizard-like player model using basic shapes."""
    glPushMatrix()
    
    glTranslatef(player.position[0], player.position[1], 37.5)

    glRotatef(player.rotation_angle, 0, 0, 1)
    
    glScalef(0.5, 0.5, 0.5)

    glRotatef(90, 1, 0, 0)

    # --- Draw Wizard Robe (Body) ---
    glColor3f(0.3, 0.2, 0.8) # Dark purple
    glPushMatrix()
    glScalef(1, 1.5, 0.7)
    glutSolidCube(50)
    glPopMatrix()

    # --- Draw Head ---
    glColor3f(0.9, 0.7, 0.6) # A skin-like color
    glPushMatrix()
    glTranslatef(0, 55, 0) 
    glutSolidSphere(20, 20, 20) 
    glPopMatrix()

    # --- Draw Wizard Hat ---
    glColor3f(0.2, 0.1, 0.6) # Even darker purple for the hat
    glPushMatrix()
    glTranslatef(0, 65, 0) # Position hat on top of the head
    glRotatef(-90, 1, 0, 0) # Rotate the cone to point upwards

    gluCylinder(gluNewQuadric(), 30, 0, 60, 20, 20)
    glPopMatrix()
    
    # --- Draw Arms ---
    # Arms
    glPushMatrix(); glColor3f(0.3, 0.2, 0.8) # Right
    glPushMatrix(); glTranslatef(-35, 20, 0); glScalef(1.0, 0.4, 0.4); glutSolidCube(30); glPopMatrix()
    glPushMatrix(); glTranslatef(-45, 20, 15); glScalef(0.4, 0.4, 1.0); glutSolidCube(30); glPopMatrix()
    glPushMatrix(); glColor3f(0.9, 0.7, 0.6); glTranslatef(-45, 20, 35); glutSolidSphere(8, 10, 10); glPopMatrix()
    glPopMatrix()

    glPushMatrix(); glColor3f(0.3, 0.2, 0.8) # LEft
    glPushMatrix(); glTranslatef(35, 20, 0); glScalef(1.0, 0.4, 0.4); glutSolidCube(30); glPopMatrix() # Upper
    glPushMatrix(); glTranslatef(45, 20, 15); glScalef(0.4, 0.4, 1.0); glutSolidCube(30); glPopMatrix() # Lower
    glPushMatrix(); glColor3f(0.9, 0.7, 0.6); glTranslatef(45, 20, 35); glutSolidSphere(8, 10, 10); glPopMatrix() # Fist
    
    # Weapon
    glPushMatrix()
    glTranslatef(-45, 20, 35)
    glRotatef(45, 1, 0, 0); glRotatef(-25, 0, 1, 0)
    if player.weapon == "Sword": 
        glTranslatef(0, 30, 0); glScalef(0.6, 0.6, 0.6); draw_sword()
    elif player.weapon == "Magic Staff": 
        glTranslatef(0, 40, 0); glScalef(0.5, 0.5, 0.5); draw_magic_staff()
    glPopMatrix()
    glPopMatrix()

    # --- Draw Legs ---
    glColor3f(0.2, 0.2, 0.2) # Dark grey
    # Left Leg
    glPushMatrix()
    glTranslatef(-15, -45, 0) 
    glScalef(0.6, 1.2, 0.6) 
    glutSolidCube(30)
    glPopMatrix()

    # Right Leg
    glPushMatrix()
    glTranslatef(15, -45, 0)
    glScalef(0.6, 1.2, 0.6) 
    glutSolidCube(30)
    glPopMatrix()

    glPopMatrix() 

def spawn_boss():
    """Creates and spawns the final boss."""
    boss_template = ENEMY_CATALOG["Archdemon"]
    
    # Position the boss in the oblivion
    position = [0, 1500, 0] 
    
    animation_params = {
        'phase_offset': 0, 
        'scale_factor': 0.03, 
        'scale_speed': 1.0
    }
    
    z_offset = (40 * 1.8) / 2 
    
    boss_npc = NPC(
        position, 
        boss_template["composition"], 
        z_offset, 
        animation_params, 
        is_rogue=True, 
        has_quest=False, 
        enemy_type="Archdemon"
    )
    
    # Manually set stats from the catalog
    boss_npc.stats = boss_template["stats"].copy()
    
    npcs.append(boss_npc)
    print("The Archdemon has appeared!")

def get_nearest_npc():
    """Finds the NPC closest to the player."""
    closest_npc = None
    min_dist = float('inf')
    for npc in npcs:
        dist = math.sqrt((player.position[0] - npc.position[0])**2 + (player.position[1] - npc.position[1])**2)
        if dist < min_dist:
            min_dist = dist
            closest_npc = npc
    return closest_npc, min_dist

def check_for_rogue_defeat():
    """Checks if all rogue NPCs are defeated and reveals the boss door if so."""
    global boss_door
    # Count how many rogue NPCs are left
    rogues_remaining = sum(1 for npc in npcs if npc.is_rogue)
    if rogues_remaining == 0 and boss_door.state == 'hidden':
        boss_door.reveal()

def check_item_collision():
    """Checks for and handles collision with dropped items."""
    global dropped_items, boss_door
    
    # Check for boss key collision first
    if boss_door.key_present:
        dist = math.sqrt((player.position[0] - boss_door.key.position[0])**2 + (player.position[1] - boss_door.key.position[1])**2)
        if dist < player.collision_radius + boss_door.key.collision_radius:
            print("You found the key! The grand door is opening...")
            boss_door.open()
            return
        
    for item in dropped_items[:]: # Iterate over a copy
        dist = math.sqrt((player.position[0] - item.position[0])**2 + (player.position[1] - item.position[1])**2)
        if dist < player.collision_radius + item.collision_radius:
            if item.item_type == 'loot':
                item_found = random.choice(["Healing Potion", "Mana Potion", "Mysterious Potion"])
                player.inventory[item_found] += 1
                print(f"You picked up a {item_found}!") #
            elif item.item_type == 'xp':
                player.xp += item.value
                print(f"You absorbed an XP orb! +{item.value} XP!")
            dropped_items.remove(item)
            break # Pick up one item per frame

def initialize_pickups():
    """Spawns loot and XP items across the manor wings."""
    num_items = 7 # No. of items to spawn
    for i in range(num_items):
        # Choose a random wing
        wing_bounds = random.choice(WING_BOUNDS)
        x_min, x_max, y_min, y_max = wing_bounds
        
        # Get a random position within the wing
        x = random.uniform(x_min + 50, x_max - 50)
        y = random.uniform(y_min + 50, y_max - 50)
        position = [x, y, 0]

        # Randomly decide item type
        if random.random() < 0.6: # 60% chance for loot
            item_type = 'loot'
            new_item = DroppedItem(position, item_type=item_type)
        else: # 40% chance for XP
            item_type = 'xp'
            xp_value = random.choice([10, 25, 50])
            new_item = DroppedItem(position, item_type=item_type, value=xp_value)
            
        dropped_items.append(new_item)


def keyboardListener(key, x, y):
    """
    Handles keyboard inputs for player movement, gun rotation, camera updates, and cheat mode toggles.
    """
    global game_state, camera_pos, camera_angle, collided_npc, previous_camera_pos, dialogue_options, dialogue_text, creation_step, combat_log, combat_menu_state, vfx_timers
    if game_state == "character_creation":
        if key == b'\r':
            if creation_step == "stats":
                creation_step = "weapon"
            else:
                # Spwan NPCS and start game
                game_state = "playing"
                total_npcs, num_rogues = 6, 3
                spawn_list = [True] * num_rogues + [False] * (total_npcs - num_rogues)
                random.shuffle(spawn_list)
                for i, is_rogue in enumerate(spawn_list): 
                    generate_and_spawn_npc(is_rogue, WING_BOUNDS[i])
                initialize_pickups()
    
    elif game_state == "game_over":
        if key == b'\r': 
            reset_game()
    
    elif game_state == "victory":
        if key == b'\r': 
            reset_game()

    elif game_state == "playing": # Normal gameplay state
        # Player movement and rotation
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
        
        # C to toggle god mode
        if key == b'c':
            global god_mode
            god_mode = not god_mode
            if god_mode:
                print("God Mode Activated!")
            else:
                print("God Mode Deactivated!")
            return
        
        # I to interact with nearest NPC
        if key == b'i':
            npc_to_interact, dist = get_nearest_npc()
            if npc_to_interact and dist <= interaction_range:
                if npc_to_interact.is_rogue and npc_to_interact.is_revealed:
                    game_state, collided_npc, dialogue_text = "combat", npc_to_interact, ""
                    combat_log = [f"The {collided_npc.enemy_type} is still hostile!"]
                    dialogue_options = ["Attack", "Cast Magic", "Use Item", "Flee"]
                else:
                    game_state, collided_npc, dialogue_text = "dialogue", npc_to_interact, "..."
                    dialogue_options = ["Who are you?", "How to get out of this place?", "Can you help me?", "Leave"]
                return
            
        
        # Boundary check using the new system
        if is_valid_position(new_pos_x, new_pos_y):
            player.position[0] = new_pos_x
            player.position[1] = new_pos_y
        
        # Check for collisions with items
        check_item_collision()
    
    elif game_state == "dialogue": # Dialogue state with NPC

        if collided_npc and collided_npc.enemy_type == "Archdemon":
            if key == b'1': # "Who are you?"
                dialogue_text = ENEMY_CATALOG["Archdemon"]["dialogue"]
                game_state = "combat"
            elif key in [b'2', b'3', b'4']: # Any other option
                dialogue_text = random.choice(DEMONIC_GIBBERISH)
            
            if game_state != "combat":
                dialogue_options = ["Who are you?", "How to get out of this place?", "Can you help me?", "Leave"]
            else:
                combat_log = [random.choice(DEMONIC_GIBBERISH)]
                dialogue_options = ["Attack", "Cast Magic", "Use Item", "Flee"]
            
            return
        
        # Handle dialogue options based on key presses
        if key == b'1': # Who are you? OR Attack
            if dialogue_options and dialogue_options[0] == "Who are you?":
                if collided_npc.is_rogue:
                    enemy_blueprint = ENEMY_CATALOG[collided_npc.enemy_type]
                    collided_npc.composition, collided_npc.stats, dialogue_text = enemy_blueprint["composition"], enemy_blueprint["stats"].copy(), enemy_blueprint["dialogue"]
                    collided_npc.is_revealed = True
                    game_state = "combat"; combat_log = [f"A {collided_npc.enemy_type} appears!"]
                    dialogue_options = ["Attack", "Cast Magic", "Use Item", "Flee"] 
                else: 
                    dialogue_text = "Just a humble traveler, like you."
            
            elif dialogue_options and dialogue_options[0] == "Attack":
                player_damage = player.stats["Strength"] + random.randint(1, 6)
                collided_npc.stats["Health"] -= player_damage
                combat_log.append(f"You hit for {player_damage} damage.")
                if collided_npc.stats["Health"] <= 0:
                    player.xp += 50; print(f"You defeated the {collided_npc.enemy_type}! +50 XP"); npcs.remove(collided_npc); game_state = "playing"
                    return
                enemy_damage = collided_npc.stats["Strength"] + random.randint(1, 3)
                player.stats["Health"] -= enemy_damage
                combat_log.append(f"Enemy hits for {enemy_damage} damage.")
                if player.stats["Health"] <= 0: combat_log.append("You have been defeated!"); game_state = "playing"
        
        elif key == b'2': # How to get out of this place?
            if len(dialogue_options) > 1 and dialogue_options[1] == "Try to flee":
                game_state = "playing"
            elif len(dialogue_options) > 1 and dialogue_options[1] == "How to get out of this place?":
                if collided_npc.has_given_quest and not collided_npc.is_rogue:
                    dialogue_text = "I've already told you what I know."
                elif collided_npc.is_rogue or collided_npc.has_given_quest:
                    dialogue_text = random.choice(["I dunno.", "Who knows?"])
                else:
                    collided_npc.has_given_quest = True
                    rogue_npcs = [npc for npc in npcs if npc.is_rogue]
                    quest_hints = [ "You must find the hidden door.", "A key is needed to unlock the way." ]
                    if rogue_npcs:
                        quest_target_npc = random.choice(rogue_npcs)
                        enemy_to_kill = quest_target_npc.enemy_type
                        quest_hints.append(f"A powerful {enemy_to_kill} guards the exit.")
                    
                    quest_hint_text = random.choice(quest_hints)
                    dialogue_text = f"They whisper, '{quest_hint_text}'"
                    quest_objective = ""
                    
                    if "door" in quest_hint_text: 
                        quest_objective = "Find the hidden door"
                    elif "key" in quest_hint_text: 
                        quest_objective = "Find the key"
                    else: 
                        quest_objective = f"Defeat the {enemy_to_kill}"
                    if quest_objective not in player.main_quests:
                        player.main_quests.append(quest_objective)
            
            elif len(dialogue_options) > 1 and dialogue_options[1] == "Use Item":
                combat_log.append("You have no items!")

        elif key == b'3': # Can you help me?
            if len(dialogue_options) > 2 and dialogue_options[2] == "Can you help me?":
                if collided_npc.has_given_help and not collided_npc.is_rogue:
                    dialogue_text = "I have already done what I can for you."
                elif collided_npc.has_given_help and  collided_npc.is_rogue:
                    dialogue_text = "Back for more are you? Begone!"
                else:
                    collided_npc.has_given_help = True
                    buffable_stats = ["Strength", "Dexterity", "Intelligence"]
                    stat_to_change = random.choice(buffable_stats)
                    if collided_npc.is_rogue:
                        change_amount = -3
                        player.stats[stat_to_change] += change_amount
                        dialogue_text = f"You feel a chill... ({stat_to_change} {change_amount})"
                    else:
                        change_amount = 5
                        player.stats[stat_to_change] += change_amount
                        dialogue_text = f"You feel stronger! ({stat_to_change} +{change_amount})"
            elif len(dialogue_options) > 2 and dialogue_options[2] == "Flee":
                if random.random() < 0.5: combat_log.append("You fled successfully!"); game_state = "playing"
                else:
                    combat_log.append("You failed to flee!")
                    enemy_damage = collided_npc.stats["Strength"] + random.randint(1, 3); player.stats["Health"] -= enemy_damage
                    combat_log.append(f"Enemy hits for {enemy_damage} damage.")
        
        elif key == b'4': # Leave
            if len(dialogue_options) > 3 and dialogue_options[3] == "Leave":
                game_state = "playing"
        
        # Check for XP reward after every interaction with a friendly NPC
        if not collided_npc.is_rogue and not collided_npc.xp_awarded:
            if collided_npc.has_given_quest and collided_npc.has_given_help:
                xp_gain = 25
                player.xp += xp_gain
                collided_npc.xp_awarded = True
                print(f"Gained {xp_gain} XP!")
    elif game_state == "combat":
        if combat_menu_state == "main":
            if key == b'1': # Attack
                vfx_timers['attack_flash'] = 0.2
                if god_mode and collided_npc.enemy_type != "Archdemon":
                    player_damage = 9999 # Insta-kill damage
                elif player.weapon == "Sword": player_damage = player.stats["Strength"] + random.randint(1, 6)
                else: player_damage = player.stats["Intelligence"] + random.randint(1, 4)
                if player.buff_turns > 0 and not god_mode:
                    bonus_damage = 10; player_damage += bonus_damage
                    combat_log.append(f"Your buff adds {bonus_damage} damage!")
                collided_npc.stats["Health"] -= player_damage
                combat_log.append(f"You attack for {player_damage} damage.")
                
                # Check for enemy defeat immediately after the attack.(GOD MODE)
                if collided_npc.stats["Health"] <= 0:
                    if collided_npc.enemy_type == "Archdemon":
                        game_state = "victory"
                        return
                    player.xp += 50
                    combat_log.append(f"You defeated the {collided_npc.enemy_type}! +50 XP")
                    if collided_npc.is_rogue:
                        npcs.remove(collided_npc)
                        check_for_rogue_defeat() # Check after a rogue is defeated
                    else:
                        npcs.remove(collided_npc)
                    
                    # Loot Drop Logic
                    if random.random() < 0.8: # 80% chance to drop an item
                        new_item = DroppedItem(collided_npc.position, item_type='loot')
                        dropped_items.append(new_item)
                        print("The enemy dropped a loot bag!")
                    
                    game_state = "playing"
                    return # Exit before the enemy gets a turn
                else:
                    # If the enemy is not defeated, it takes its turn.
                    enemy_turn()
            elif key == b'2': # Cast Magic
                combat_menu_state = "magic"
                if player.weapon == "Sword": dialogue_options = ["Heal", "Protection", "Buff", "Back"]
                else: dialogue_options = ["Heal", "Fireball", "Reflect", "Back"]
            elif key == b'3': # Use Item
                combat_menu_state = "item"
                dialogue_options = [f"{item} (x{count})" for item, count in player.inventory.items() if count > 0]
                dialogue_options.append("Back")
            elif key == b'4': # Flee
                if collided_npc and collided_npc.enemy_type == "Archdemon":
                    combat_log.append("There is no escape!")
                    enemy_turn() # The demon attacks as punishment
                    return
                if random.random() < 0.5: 
                    combat_log.append("You fled successfully!"); game_state = "playing"
                else: 
                    combat_log.append("You failed to flee!"); enemy_turn()
        elif combat_menu_state == "magic":
            spell_name = ""
            if key == b'1': spell_name = dialogue_options[0]
            elif key == b'2': spell_name = dialogue_options[1]
            elif key == b'3': spell_name = dialogue_options[2]
            elif key == b'4': combat_menu_state = "main"; dialogue_options = ["Attack", "Cast Magic", "Use Item", "Flee"]; return
            if spell_name:
                mana_cost = MANA_COSTS.get(spell_name, 0)
                if player.stats["Mana"] >= mana_cost or (god_mode and collided_npc.enemy_type != "Archdemon"):
                    if not (god_mode and collided_npc.enemy_type != "Archdemon"):
                        player.stats["Mana"] -= mana_cost
                    if spell_name == "Heal":
                        heal_amount = player.stats["Intelligence"] * 3 + random.randint(5,10)
                        player.stats["Health"] = min(100, player.stats["Health"] + heal_amount); combat_log.append(f"You heal for {heal_amount} HP."); vfx_timers['heal'] = 0.5
                    elif spell_name == "Protection": 
                        player.protection_turns = 2; combat_log.append("A magical shield surrounds you!")
                    elif spell_name == "Buff": 
                        player.buff_turns = 2; combat_log.append("You feel your strength increase!")
                    elif spell_name == "Fireball":
                        damage = player.stats["Intelligence"] * 2 + random.randint(10, 20)
                        collided_npc.stats["Health"] -= damage; combat_log.append(f"Fireball hits for {damage} damage.")
                        vfx_timers['fireball'] = {'duration': 0.3, 'max_duration': 0.3, 'pos': collided_npc.position}; vfx_timers['attack_flash'] = 0.2
                    elif spell_name == "Reflect": player.reflect_turns = 1; combat_log.append("You are surrounded by a shimmering aura!")
                    combat_menu_state = "main"; dialogue_options = ["Attack", "Cast Magic", "Use Item", "Flee"]; enemy_turn()
                else: combat_log.append("Not enough mana!")
             
        elif combat_menu_state == "item":
            item_name_to_use = None
            available_items = [item for item, count in player.inventory.items() if count > 0]
            if key == b'1' and len(available_items) >= 1: item_name_to_use = available_items[0]
            elif key == b'2' and len(available_items) >= 2: item_name_to_use = available_items[1]
            elif key == b'3' and len(available_items) >= 3: item_name_to_use = available_items[2]
            elif (key == b'1' and len(available_items) == 0) or \
                 (key == b'2' and len(available_items) == 1) or \
                 (key == b'3' and len(available_items) == 2) or \
                 key == b'4': # Back
                combat_menu_state = "main"; dialogue_options = ["Attack", "Cast Magic", "Use Item", "Flee"]; return
            
            if item_name_to_use:
                player.inventory[item_name_to_use] -= 1
                if item_name_to_use == "Healing Potion":
                    player.stats["Health"] = 100; combat_log.append("You drink a Healing Potion. HP fully restored!")
                elif item_name_to_use == "Mana Potion":
                    player.stats["Mana"] = 50; combat_log.append("You drink a Mana Potion. Mana fully restored!")
                elif item_name_to_use == "Mysterious Potion":
                    if random.random() < 0.5: # Buff
                        stat_to_buff = random.choice(stat_keys)
                        player.base_stats[stat_to_buff] += 2; player.stats[stat_to_buff] += 2
                        combat_log.append(f"The potion was a blessing! Permanent +2 {stat_to_buff}!")
                    else: # Debuff
                        player.debuff_turns = 3; combat_log.append("The potion was a curse! You feel weaker.")
                combat_menu_state = "main"; dialogue_options = ["Attack", "Cast Magic", "Use Item", "Flee"]; enemy_turn()

def enemy_turn():
    """Logic for the enemy's action in combat."""
    global dropped_items, game_state
    if god_mode and (not collided_npc or collided_npc.enemy_type != "Archdemon"):
        return # Player is invincible unless fighting the Archdemon
    if collided_npc.stats["Health"] <= 0:
        player.xp += 50
        print(f"You defeated the {collided_npc.enemy_type}! +50 XP")
        if collided_npc.enemy_type == "Archdemon":
            game_state = "victory"
            return
        
        if collided_npc.is_rogue:
            npcs.remove(collided_npc)
            check_for_rogue_defeat() # Check after a rogue is defeated
        else:
            npcs.remove(collided_npc)

        # Loot Drop Logic
        if random.random() < 0.8: # 80% chance to drop an item
            new_item = DroppedItem(collided_npc.position, item_type='loot')
            dropped_items.append(new_item)
            print("The enemy dropped a loot bag!")
        
        game_state = "playing"
        return
    
    enemy_damage = collided_npc.stats["Strength"] + random.randint(1, 3)
    if player.debuff_turns > 0: enemy_damage = int(enemy_damage * 1.5)

    if player.reflect_turns > 0:
        collided_npc.stats["Health"] -= enemy_damage; combat_log.append(f"You reflect {enemy_damage} damage back!")
        vfx_timers['attack_flash'] = 0.2
        if collided_npc.stats["Health"] <= 0:
            player.xp += 50; combat_log.append(f"The {collided_npc.enemy_type} was defeated by its own attack! +50 XP")
            npcs.remove(collided_npc); game_state = "playing"
        player.reflect_turns -= 1; return
    if player.protection_turns > 0:
        combat_log.append("Your shield blocks all damage!")
    else:
        player.stats["Health"] -= enemy_damage; combat_log.append(f"The {collided_npc.enemy_type} hits you for {enemy_damage} damage.")
    if player.protection_turns > 0: player.protection_turns -= 1
    if player.buff_turns > 0:
        player.buff_turns -= 1
        if player.buff_turns == 0: combat_log.append("Your attack buff has worn off.")
    if player.debuff_turns > 0:
        player.debuff_turns -= 1
        if player.debuff_turns == 0: combat_log.append("The curse has lifted.")
    if player.stats["Health"] <= 0:
        combat_log.append("You have been defeated!")
        game_state = "game_over" 

def specialKeyListener(key, x, y):
    """
    Navigate stat allocation or weapon selection
    """
    global game_state, selected_stat_index, available_points
    if game_state == "character_creation":
        
        if creation_step == "stats":
            if key == GLUT_KEY_UP: selected_stat_index = (selected_stat_index - 1 + len(stat_keys)) % len(stat_keys)
            elif key == GLUT_KEY_DOWN: selected_stat_index = (selected_stat_index + 1) % len(stat_keys)
            elif key == GLUT_KEY_RIGHT and available_points > 0:
                stat = stat_keys[selected_stat_index]; player.stats[stat] += 1; available_points -= 1
            elif key == GLUT_KEY_LEFT:
                stat = stat_keys[selected_stat_index]
                if player.stats[stat] > player.base_stats[stat]: player.stats[stat] -= 1; available_points += 1
        
        elif creation_step == "weapon":
            current_weapon_index = player.weapon_options.index(player.weapon)
            if key == GLUT_KEY_LEFT: new_index = (current_weapon_index - 1 + len(player.weapon_options)) % len(player.weapon_options)
            elif key == GLUT_KEY_RIGHT: new_index = (current_weapon_index + 1) % len(player.weapon_options)
            else: return
            player.weapon = player.weapon_options[new_index]


def mouseListener(button, state, x, y):
    """
    Handles mouse inputs for firing bullets (left click) and toggling camera mode (right click).
    """
        # # Left mouse button fires a bullet
        # if button == GLUT_LEFT_BUTTON and state == GLUT_DOWN:

        # # Right mouse button toggles camera tracking mode
        # if button == GLUT_RIGHT_BUTTON and state == GLUT_DOWN:


def setupCamera():
    """Configures the camera's projection and view settings."""
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    
    if game_state == "dialogue" or game_state == "combat" and collided_npc:
        gluPerspective(30, 1.25, 0.1, 2000)
    else:
        gluPerspective(fovY, 1.25, 0.1, 2000)
        
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()
    
    if game_state == "dialogue" or game_state == "combat" and collided_npc:
        gluLookAt(300, 200, 150, 
                  800, 200, 0, 
                  0, 0, 1)
    else:
        # --- Third-Person Camera Logic ---
        camera_distance = 80.0  # How far behind the player the camera is
        camera_height = 130.0     # How high above the player the camera is

        angle_rad = math.radians(player.rotation_angle - 90)

        offset_x = -camera_distance * math.cos(angle_rad)
        offset_y = -camera_distance * math.sin(angle_rad)


        cam_x = player.position[0] + offset_x
        cam_y = player.position[1] + offset_y
        cam_z = player.position[2] + camera_height 
        look_at_x = player.position[0]
        look_at_y = player.position[1]
        look_at_z = player.position[2] + 40.0 

        gluLookAt(cam_x, cam_y, cam_z,
                  look_at_x, look_at_y, look_at_z,
                  0, 0, 1) 


def idle():
    """Idle function that runs continuously and calculates delta time."""
    global last_time, total_time
    now = time.time()
    delta_time = now - last_time
    last_time = now
    total_time += delta_time # elapsed time

    # boss door animation
    boss_door.update(delta_time)

    # Update VFX timers
    for effect in list(vfx_timers.keys()):
        if isinstance(vfx_timers[effect], dict): 
            vfx_timers[effect]['duration'] -= delta_time
            if vfx_timers[effect]['duration'] <= 0: del vfx_timers[effect]
        else:
            vfx_timers[effect] -= delta_time
            if vfx_timers[effect] <= 0: del vfx_timers[effect]
    
    glutPostRedisplay()

# --- Manor Drawing Functions ---
def draw_wood_floor():
    """Draws a dark wood plank floor."""
    plank_width = 150
    # cover the entire new manor layout
    num_planks_x = int((GRID_LENGTH * 2) / plank_width)
    num_planks_y = int((GRID_LENGTH * 2) / plank_width)

    for i in range(num_planks_x):
        for j in range(num_planks_y):
            x = -GRID_LENGTH + i * plank_width
            y = -GRID_LENGTH + j * plank_width
            
            if (i + j) % 2 == 0:
                glColor3f(0.3, 0.15, 0.05) # Dark brown
            else:
                glColor3f(0.25, 0.1, 0.0) # Even darker brown

            glBegin(GL_QUADS)
            glVertex3f(x, y, 0)
            glVertex3f(x + plank_width, y, 0)
            glVertex3f(x + plank_width, y + plank_width, 0)
            glVertex3f(x, y + plank_width, 0)
            glEnd()

def draw_wall_segment(x1, y1, x2, y2, height, color):
    """Draws a single rectangular wall segment."""
    glColor3f(*color)
    glBegin(GL_QUADS)
    glVertex3f(x1, y1, 0)
    glVertex3f(x2, y2, 0)
    glVertex3f(x2, y2, height)
    glVertex3f(x1, y1, height)
    glEnd()

def draw_manor_layout():
    """Draws the entire manor structure including all wings and doorways."""
    wall_color = (0.2, 0.2, 0.25)
    
    # --- Central Hall Walls ---
    hall_x = CENTRAL_HALL_WIDTH
    door_y_centers = [1000, 0, -1000] # Y-centers for the doorways

    # Left Wall 
    draw_wall_segment(-hall_x, 1200, -hall_x, door_y_centers[0] + DOOR_WIDTH/2, WALL_HEIGHT, wall_color)
    draw_wall_segment(-hall_x, door_y_centers[0] - DOOR_WIDTH/2, -hall_x, door_y_centers[1] + DOOR_WIDTH/2, WALL_HEIGHT, wall_color)
    draw_wall_segment(-hall_x, door_y_centers[1] - DOOR_WIDTH/2, -hall_x, door_y_centers[2] + DOOR_WIDTH/2, WALL_HEIGHT, wall_color)
    draw_wall_segment(-hall_x, door_y_centers[2] - DOOR_WIDTH/2, -hall_x, -1200, WALL_HEIGHT, wall_color)

    # Right Wall
    draw_wall_segment(hall_x, 1200, hall_x, door_y_centers[0] + DOOR_WIDTH/2, WALL_HEIGHT, wall_color)
    draw_wall_segment(hall_x, door_y_centers[0] - DOOR_WIDTH/2, hall_x, door_y_centers[1] + DOOR_WIDTH/2, WALL_HEIGHT, wall_color)
    draw_wall_segment(hall_x, door_y_centers[1] - DOOR_WIDTH/2, hall_x, door_y_centers[2] + DOOR_WIDTH/2, WALL_HEIGHT, wall_color)
    draw_wall_segment(hall_x, door_y_centers[2] - DOOR_WIDTH/2, hall_x, -1200, WALL_HEIGHT, wall_color)
    
    # Back and Front walls of the hall
    draw_wall_segment(-hall_x, -1200, hall_x, -1200, WALL_HEIGHT, wall_color)
    draw_wall_segment(-hall_x, 1200, hall_x, 1200, WALL_HEIGHT, wall_color)

    
    # --- Wing Walls ---
    for bounds in WING_BOUNDS:
        x_min, x_max, y_min, y_max = bounds
        # Far wall
        if x_min < 0: # Left wings
            draw_wall_segment(x_min, y_min, x_min, y_max, WALL_HEIGHT, wall_color)
        else: # Right wings
            draw_wall_segment(x_max, y_min, x_max, y_max, WALL_HEIGHT, wall_color)
        # Side walls
        draw_wall_segment(x_min, y_min, x_max, y_min, WALL_HEIGHT, wall_color)
        draw_wall_segment(x_min, y_max, x_max, y_max, WALL_HEIGHT, wall_color)


def draw_manor_environment():
    """Draws the complete spooky manor environment."""
    
    draw_wood_floor()
    draw_manor_layout()
    boss_door.draw()

def showScreen():
    """
    Display function to render the game scene:
    """
    glClearColor(0.05, 0.05, 0.1, 1.0)
    # Clear color and depth buffers
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glLoadIdentity()  # Reset modelview matrix
    glViewport(0, 0, 1000, 800)  # Set viewport size

    if game_state == "character_creation":
        draw_character_creation_screen()
    
    elif game_state == "game_over":
        draw_game_over_screen()
    
    elif game_state == "victory":
        draw_victory_screen()
    
    elif game_state == "playing":
        setupCamera()  # Configure camera perspective

        # --- Draw the manor environment ---
        draw_manor_environment()

        if god_mode:
            draw_text(10, 770, "GOD MODE ACTIVE")
            draw_text(10, 740, "Health: INFINITE")
            draw_text(10, 710, "Mana: INFINITE")
        else:
            draw_text(10, 770, f"Level: {player.level} (XP: {player.xp}/{player.xp_to_next_level})")
            y_offset = 740
            for stat, value in player.stats.items():
                draw_text(10, y_offset, f"{stat}: {value}")
                y_offset -= 30
        
        # --- Draw the Player Model ---
        draw_player()

        for npc in npcs: # Draw all the NPCs in the list
            draw_npc(npc)
        for item in dropped_items: draw_dropped_item(item)

        draw_quests()
    
    elif game_state == "dialogue" or game_state == "combat":
        setupCamera()
        glClear(GL_DEPTH_BUFFER_BIT)
        attack_flash_color = (1, 0.2, 0.2) if 'attack_flash' in vfx_timers else None
        # --- Draw first-person view in dialogue ---
        if collided_npc: 
            draw_npc(collided_npc, is_in_dialogue=True, override_color=attack_flash_color)
        draw_player_hand_and_weapon(override_color=attack_flash_color)
        
        if game_state == "dialogue": 
            draw_dialogue_screen()
        else: 
            draw_combat_screen()

    glutSwapBuffers()


def main():
    glutInit()
    glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB | GLUT_DEPTH)  # Double buffering, RGB color, depth test
    glutInitWindowSize(1000, 800)  # Window size
    glutInitWindowPosition(0, 0)  # Window position
    wind = glutCreateWindow(b"Restricted World")  
    glEnable(GL_DEPTH_TEST)  
    glutDisplayFunc(showScreen)  
    glutKeyboardFunc(keyboardListener)  
    glutSpecialFunc(specialKeyListener)
    glutMouseFunc(mouseListener)
    glutIdleFunc(idle) 

    glutMainLoop()

if __name__ == "__main__":
    main()
