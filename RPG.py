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
game_state = "character_creation" # Can be "character_creation" or "playing"
creation_step = "stats"
available_points = 5
selected_stat_index = 0
stat_keys = ["Strength", "Dexterity", "Intelligence"]

# --- Dialogue and Interaction State ---
collided_npc = None
previous_camera_pos = None
dialogue_options = []
combat_log = [] # Stores messages during a fight
dialogue_text = "" # NEW: Stores the NPC's current dialogue line
interaction_range = 75.0 # The radius within which the player can interact with an NPC

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
        # --- NEW: Quest Log ---
        self.main_quests = ["Get out of this world"]
        # --- NEW: Player's chosen weapon ---
        self.weapon = "Sword" # Default weapon
        self.weapon_options = ["Sword", "Magic Staff"]


player = Player()

# --- NPC Data ---
class NPC:
    def __init__(self, position, composition, z_offset, animation_params, is_rogue, has_quest, enemy_type=None):
        self.position = position
        self.composition = composition
        self.z_offset = z_offset
        self.animation_params = animation_params
        self.is_rogue = is_rogue
        # A flag to determine if the NPC has a quest
        self.has_quest = has_quest
        # NEW: Store the potential enemy type
        self.enemy_type = enemy_type
        self.stats = { "Health": 50, "Strength": 5 }
        # --- NEW: Variables to track one-time interactions ---
        self.has_given_quest = False
        self.has_given_help = False
        self.xp_awarded = False


npcs = [] # A list to hold all the NPC objects in the world

# --- NPC Part Pools ---
# Each dictionary defines a blueprint for a body part.
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
    }
}


# Camera-related variables
camera_pos = (0,500,500)
camera_angle = 90

final_x, final_y, final_z = camera_pos

fovY = 120  # Field of view
GRID_LENGTH = 600  # Length of grid lines


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
    if creation_step == "stats":
        draw_text(350, 700, "Create Your Character", GLUT_BITMAP_TIMES_ROMAN_24)
        draw_text(250, 650, "Use UP/DOWN to select a stat. Use LEFT/RIGHT to change values.")
        draw_text(400, 550, f"Points to Spend: {available_points}")
        y_offset = 450
        for i, stat in enumerate(stat_keys):
            prefix = "> " if i == selected_stat_index else "  "
            draw_text(400, y_offset, f"{prefix}{stat}: {player.stats[stat]}")
            y_offset -= 40
        draw_text(380, 200, "Press ENTER to Continue")
    elif creation_step == "weapon":
        draw_text(380, 700, "Choose Your Weapon", GLUT_BITMAP_TIMES_ROMAN_24)
        draw_text(250, 650, "Use LEFT/RIGHT to select a weapon.")
        weapon_display = f"< {player.weapon} >"
        draw_text(420, 500, weapon_display)
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
    draw_text(50, 750, f"Player HP: {player.stats['Health']}")
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

    # SUGGESTION: Draw NPC dialogue text at the top left
    draw_text(50, 750, dialogue_text)
    
    # SUGGESTION: Draw player options at the bottom left
    y_offset = 150
    for i, option in enumerate(dialogue_options):
        draw_text(50, y_offset, f"{i+1}. {option}")
        y_offset -= 40
    
def generate_and_spawn_npc(is_rogue):
    """Generates a composite NPC from the pools and spawns it on the map."""
    composition = []
    # 1. Choose a torso and assign its color
    torso = random.choice(torso_pool).copy()
    torso['position'] = (0, 0, 0) # Torso is the center
    torso['color'] = (random.random(), random.random(), random.random())
    composition.append(torso)
    
    # 2. Choose a head and assign its color
    head = random.choice(head_pool).copy()
    head['color'] = (random.random(), random.random(), random.random())
    composition.append(head)

    # 3. Choose legs, assign a color, and create a left and right version
    leg_blueprint = random.choice(legs_pool).copy()
    leg_color = (random.random(), random.random(), random.random())
    
    # --- FIX ---
    # The leg's Y position has been raised from -60 to -45 to connect with the torso.
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
    right_leg['color'] = leg_color # Both legs share the same color
    composition.append(right_leg)
    
    # Determine if NPC is rogue, but don't change its appearance
    has_quest = False
    enemy_type = None

    if is_rogue:
        # SUGGESTION: If the NPC is a rogue, pick a random enemy type from the catalog
        enemy_type = random.choice(list(ENEMY_CATALOG.keys()))
    elif random.random() < 0.4: # 40% chance for a friendly NPC to have a quest
        has_quest = True

    # 4. Get a random position on the map
    x = random.uniform(-GRID_LENGTH + 50, GRID_LENGTH - 50)
    y = random.uniform(-GRID_LENGTH + 50, GRID_LENGTH - 50)
    position = [x, y, 0]

    # --- NEW: Generate and store unique animation parameters for this NPC ---
    animation_params = {
        'phase_offset': random.uniform(0, 2 * math.pi), # Random start point in the animation cycle
        'scale_factor': random.uniform(0.05, 0.1), 
        'scale_speed': random.uniform(2.0, 4.0)
    }
    
    # 5. Create the NPC instance, passing the calculated offset
    new_npc = NPC(position, composition, z_offset, animation_params, is_rogue, has_quest, enemy_type)
    npcs.append(new_npc)

def draw_quest_indicator():
    """Draws a yellow exclamation mark in the NPC's local space."""
    glPushMatrix()
    # Position it high above the NPC's head
    glTranslatef(0, 110, 0) 
    glColor3f(1.0, 0.0, 0.0) # Red

    # Draw the main bar of the '!'
    glPushMatrix()
    glRotatef(-90, 1, 0, 0)
    gluCylinder(gluNewQuadric(), 5, 5, 25, 10, 5)
    glPopMatrix()

    # Draw the dot of the '!'
    glPushMatrix()
    glTranslatef(0, -15, 0)
    glutSolidSphere(6, 10, 10)
    glPopMatrix()
    
    glPopMatrix()

# --- NEW: Weapon Drawing Functions ---
def draw_sword():
    glPushMatrix()
    glColor3f(0.7, 0.7, 0.8) # Silver blade
    glPushMatrix(); glScalef(0.2, 1.5, 0.1); glutSolidCube(50); glPopMatrix() # Blade
    glColor3f(0.6, 0.4, 0.2) # Brown hilt
    glPushMatrix(); glTranslatef(0, -45, 0); glScalef(0.5, 0.2, 0.2); glutSolidCube(30); glPopMatrix() # Guard
    glPushMatrix(); glTranslatef(0, -55, 0); glScalef(0.15, 0.4, 0.15); glutSolidCube(40); glPopMatrix() # Handle
    glColor3f(0.8, 0.8, 0.2) # Gold pommel
    glPushMatrix(); glTranslatef(0, -70, 0); glutSolidSphere(7, 10, 10); glPopMatrix() # Pommel
    glPopMatrix()

def draw_magic_staff():
    glPushMatrix()
    glColor3f(0.5, 0.3, 0.1) # Brown wood
    glPushMatrix(); glScalef(0.1, 2.5, 0.1); glutSolidCube(60); glPopMatrix() # Staff shaft
    glColor3f(0.2, 0.8, 1.0) # Glowing blue gem
    glPushMatrix(); glTranslatef(0, 80, 0); glutSolidSphere(12, 20, 20); glPopMatrix() # Gem
    glPopMatrix()

def draw_npc(npc, is_in_dialogue=False):
    """Draws a single composite NPC."""
    glPushMatrix()

    # SUGGESTION: Calculate the animation scale first, so it can be used in both states.
    phase_offset = npc.animation_params['phase_offset']
    scale_factor = npc.animation_params['scale_factor']
    scale_speed = npc.animation_params['scale_speed']
    breathing_scale = 1.0 + scale_factor * math.sin(total_time * scale_speed + phase_offset)

    if is_in_dialogue:
        glTranslatef(800, 180, 0)
        # SUGGESTION: Apply the breathing_scale to the dialogue portrait's base scale.
        glScalef(1.2 * breathing_scale, 1.2 * breathing_scale, 1.2 * breathing_scale)
        glRotatef(-90, 0, 0, 1)
    else:
        # Use the pre-calculated z_offset for this specific NPC
        glTranslatef(npc.position[0], npc.position[1], npc.z_offset)
        
        # Calculate and apply rotation to face the player
        dx = player.position[0] - npc.position[0]
        dy = player.position[1] - npc.position[1]
        angle_to_player = math.degrees(math.atan2(dy, dx))
        glRotatef(angle_to_player - 90, 0, 0, 1)

        # Apply the animation scale on top of the base scale
        glScalef(0.5 * breathing_scale, 0.5 * breathing_scale, 0.5 * breathing_scale)
    
    glRotatef(90, 1, 0, 0)

    # --- NEW: Draw the quest indicator if the NPC has one ---
    # This is drawn after scaling so it pulses with the NPC
    if npc.has_quest and not is_in_dialogue:
        draw_quest_indicator()

    # Iterate through and draw each part of the NPC's body
    for part in npc.composition:
        glPushMatrix()
        glColor3f(*part['color'])
        
        if 'position' in part:
            glTranslatef(*part['position'])
        if 'scale' in part:
            glScalef(*part['scale'])

        if part['shape'] == 'cube':
            glutSolidCube(*part['params'])
        elif part['shape'] == 'sphere':
            glutSolidSphere(*part['params'])
        elif part['shape'] == 'cone':
            glPushMatrix()
            glRotatef(90, 1, 0, 0)
            gluCylinder(gluNewQuadric(), part['params'][0], 0, part['params'][1], part['params'][2], part['params'][3])
            glPopMatrix()
            
        glPopMatrix()

    glPopMatrix()

def draw_player_hand_and_weapon():
    """Draws a first-person view of the player's weapon on the right."""
    glPushMatrix()
    # Positioned on the right side of the screen, adjusted for a better view
    glTranslatef(700, 110, 10)
    
    # Weapon
    glPushMatrix()
    # Scale the weapon to be more prominent in the first-person view
    glScalef(1.2, 1.2, 1.2)
    glRotatef(110, 1, 0, 0)
    if player.weapon == "Sword":
        draw_sword()
    elif player.weapon == "Magic Staff":
        draw_magic_staff()
    glPopMatrix()
    
    glPopMatrix()

def draw_player():
    """Draws a wizard-like player model using basic shapes."""
    glPushMatrix()
    
    # Position the entire player model in the world.
    # The floor is at z=0. The robe's height is 75, and it's drawn around the origin.
    # We lift the model by half the robe's height (37.5) on the Z-axis to make it sit on the floor.
    glTranslatef(player.position[0], player.position[1], 37.5)

    # Input rotation of the player to face the correct direction
    glRotatef(player.rotation_angle, 0, 0, 1)
    
    # --- NEW ---
    # Scale the entire player model down to 50% of its original size.
    glScalef(0.5, 0.5, 0.5)

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
    # Arms
    glPushMatrix(); glColor3f(0.3, 0.2, 0.8) # Right
    glPushMatrix(); glTranslatef(-35, 20, 0); glScalef(1.0, 0.4, 0.4); glutSolidCube(30); glPopMatrix()
    glPushMatrix(); glTranslatef(-45, 20, 15); glScalef(0.4, 0.4, 1.0); glutSolidCube(30); glPopMatrix()
    glPushMatrix(); glColor3f(0.9, 0.7, 0.6); glTranslatef(-45, 20, 35); glutSolidSphere(8, 10, 10); glPopMatrix()
    glPopMatrix()
    # FIX: left arm and weapon rendering logic updated for correct positioning.
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

def keyboardListener(key, x, y):
    """
    Handles keyboard inputs for player movement, gun rotation, camera updates, and cheat mode toggles.
    """
    global game_state, camera_pos, camera_angle, collided_npc, previous_camera_pos, dialogue_options, dialogue_text, creation_step, combat_log
    if game_state == "character_creation":
        if key == b'\r':
            if creation_step == "stats":
                creation_step = "weapon"
            else:
                game_state = "playing"
                total_npcs, num_rogues = 6, 3
                spawn_list = [True] * num_rogues + [False] * (total_npcs - num_rogues)
                random.shuffle(spawn_list)
                for is_rogue in spawn_list: generate_and_spawn_npc(is_rogue)

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
        
        if key == b'i':
            npc_to_interact, dist = get_nearest_npc()
            if npc_to_interact and dist <= interaction_range:
                game_state = "dialogue"
                collided_npc = npc_to_interact
                dialogue_text = "..."
                dialogue_options = ["Who are you?", "How to get out of this place?", "Can you help me?", "Leave"]
                return
            
        # Boundary check to keep the player within the walls
        bound = GRID_LENGTH - 40 # A small buffer from the wall edge
        if -bound <= new_pos_x <= bound and -bound <= new_pos_y <= bound:
            player.position[0] = new_pos_x
            player.position[1] = new_pos_y
    
    elif game_state == "dialogue" or game_state == "combat":
        if key == b'1':
            if dialogue_options and dialogue_options[0] == "Who are you?":
                if collided_npc.is_rogue:
                    enemy_blueprint = ENEMY_CATALOG[collided_npc.enemy_type]
                    collided_npc.composition, collided_npc.stats, dialogue_text = enemy_blueprint["composition"], enemy_blueprint["stats"].copy(), enemy_blueprint["dialogue"]
                    game_state = "combat"; combat_log = [f"A {collided_npc.enemy_type} appears!"]; dialogue_options = ["Attack", "Use Item", "Flee"] 
                else: 
                    dialogue_text = "Just a humble traveler, like you."
            elif dialogue_options and dialogue_options[0] == "Attack":
                player_damage = player.stats["Strength"] + random.randint(1, 6)
                collided_npc.stats["Health"] -= player_damage
                combat_log.append(f"You hit for {player_damage} damage.")
                if collided_npc.stats["Health"] <= 0:
                    player.xp += 50; combat_log.append(f"You defeated the {collided_npc.enemy_type}! +50 XP"); npcs.remove(collided_npc); game_state = "playing"; return
                enemy_damage = collided_npc.stats["Strength"] + random.randint(1, 3)
                player.stats["Health"] -= enemy_damage
                combat_log.append(f"Enemy hits for {enemy_damage} damage.")
                if player.stats["Health"] <= 0: combat_log.append("You have been defeated!"); game_state = "playing"
        
        elif key == b'2': # How to get out of this place? OR Try to flee
            if len(dialogue_options) > 1 and dialogue_options[1] == "Try to flee":
                game_state = "playing"
            elif len(dialogue_options) > 1 and dialogue_options[1] == "How to get out of this place?":
                if collided_npc.has_given_quest and not collided_npc.is_rogue:
                    dialogue_text = "I've already told you what I know."
                elif collided_npc.is_rogue or collided_npc.has_given_quest:
                    dialogue_text = random.choice(["I dunno.", "Who knows?"])
                else:
                    collided_npc.has_given_quest = True
                    enemy_to_kill = random.choice(list(ENEMY_CATALOG.keys())); quest_hints = [f"A powerful {enemy_to_kill} guards the exit.", "You must find the hidden door.", "A key is needed to unlock the way."]; quest_hint_text = random.choice(quest_hints)
                    quest_objective = f"Defeat the {enemy_to_kill}" if "guards" in quest_hint_text else "Find the hidden door" if "door" in quest_hint_text else "Find the key"
                    if quest_objective not in player.main_quests: player.main_quests.append(quest_objective)
                    dialogue_text = f"They whisper, '{quest_hint_text}'"
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

        
        

def specialKeyListener(key, x, y):
    """
    Handles special key inputs (arrow keys) for adjusting the camera angle and height.
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
        # --- SUGGESTION: New Third-Person Camera Logic ---
        camera_distance = 80.0  # How far behind the player the camera is
        camera_height = 130.0     # How high above the player the camera is

        # Calculate camera position based on player's rotation and position
        angle_rad = math.radians(player.rotation_angle - 90)
        
        # Calculate the offset from the player
        offset_x = -camera_distance * math.cos(angle_rad)
        offset_y = -camera_distance * math.sin(angle_rad)

        # Final camera position
        cam_x = player.position[0] + offset_x
        cam_y = player.position[1] + offset_y
        cam_z = player.position[2] + camera_height 

        # The point the camera looks at (player's head/torso area)
        look_at_x = player.position[0]
        look_at_y = player.position[1]
        look_at_z = player.position[2] + 40.0 # Look slightly above the player's feet

        gluLookAt(cam_x, cam_y, cam_z,
                  look_at_x, look_at_y, look_at_z,
                  0, 0, 1) # World's up vector is Z


def idle():
    """Idle function that runs continuously and calculates delta time."""
    global last_time, total_time
    now = time.time()
    delta_time = now - last_time
    last_time = now
    total_time += delta_time # Keep a running total of elapsed time
    
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

        for npc in npcs: # Draw all the NPCs in the list
            draw_npc(npc)
        
        draw_quests()
    
    elif game_state == "dialogue" or game_state == "combat":
        setupCamera()
        if collided_npc:
            draw_npc(collided_npc, is_in_dialogue=True)
        
        glClear(GL_DEPTH_BUFFER_BIT)

        # --- NEW: Draw first-person view in dialogue ---
        draw_player_hand_and_weapon()
        if game_state == "dialogue": 
            draw_dialogue_screen()
        else: draw_combat_screen()
        
    # Swap buffers for smooth rendering (double buffering)
    glutSwapBuffers()


# Main function to set up OpenGL window and loop
def main():
    glutInit()
    glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB | GLUT_DEPTH)  # Double buffering, RGB color, depth test
    glutInitWindowSize(1000, 800)  # Window size
    glutInitWindowPosition(0, 0)  # Window position
    wind = glutCreateWindow(b"3D OpenGL Intro")  # Create the window
    glEnable(GL_DEPTH_TEST)  # Enable depth testing for 3D
    glutDisplayFunc(showScreen)  # Register display function
    glutKeyboardFunc(keyboardListener)  # Register keyboard listener
    glutSpecialFunc(specialKeyListener)
    glutMouseFunc(mouseListener)
    glutIdleFunc(idle)  # Register the idle function to move the bullet automatically

    glutMainLoop()  # Enter the GLUT main loop

if __name__ == "__main__":
    main()
