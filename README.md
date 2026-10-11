# Restricted World

A 3D turn-based role-playing game built from scratch in Python with PyOpenGL and
GLUT. There is no game engine: every model, scene, animation and menu is drawn
with immediate-mode OpenGL.

You wake up trapped inside a haunted manor. Talk to its residents, find out
which ones are hostile, defeat them, and face the Archdemon that guards the way
out.

## Gameplay

1. **Create a character.** Spend 5 points across Strength, Dexterity and
   Intelligence, then choose a Sword or a Magic Staff.
2. **Explore the manor.** It is a multi-wing house with a wooden floor and wall
   collision. Six NPCs are spawned, one in each wing.
3. **Talk to NPCs.** Each conversation gives four choices: *Who are you?*,
   *How to get out of this place?*, *Can you help me?*, and *Leave*. Some
   NPCs give quests or help, such as buffs and items.
4. **Unmask the rogues.** Three of the six NPCs are hidden enemies (Slime,
   Goblin or Orc). Talking to them reveals them and starts a fight.
5. **Fight in turns.** Each turn you can Attack, Cast Magic, Use Item or Flee.
   - Spells: Heal, Protection, Buff, Fireball and Reflect, each with a mana
     cost.
   - Items: Healing Potion, Mana Potion and Mysterious Potion.
   - Enemies drop loot and XP orbs. XP raises your level.
6. **Fight the boss.** When every rogue is defeated, a hidden door appears.
   Pick up the floating key, walk through the door as it swings open, and fight
   the Archdemon.

You win by defeating the Archdemon. Press Enter on the victory or game-over
screen to start again.

## Controls

| Key | Action |
|---|---|
| `↑` / `↓` | Select a stat (character creation) |
| `←` / `→` | Remove or add a point; choose a weapon |
| `Enter` | Confirm / continue / restart |
| `W` / `S` | Move forward / back |
| `A` / `D` | Turn left / right |
| `I` | Talk to the nearest NPC (within range) |
| `1`–`4` | Choose a dialogue, combat, spell or item option |
| `C` | Toggle god mode (cheat) |

## Technical highlights

- **Procedural NPCs:** each NPC's body is put together at random from pools of
  torso, head and leg shapes (cubes, spheres, cones), with an idle "breathing"
  animation.
- **Game state machine:** the game moves through character creation,
  exploration, dialogue, combat, game over and victory. Each state has its own
  input handling and rendering.
- **Third-person camera:** the camera follows the player's position and facing
  direction.
- **Animated world objects:** the boss door rotates open over time, the key
  floats, and visual effects run on timers. All animation uses frame-time
  (delta-time) updates.
- **Collision:** circle-based collision for items, the key and NPC interaction
  range, and region-based walkability for the manor's wings and the boss
  room.
- **On-screen UI:** dialogue boxes, combat log, quest list and stats are drawn
  with GLUT bitmap fonts.

## Requirements and running

- Python 3.8+
- PyOpenGL 3.1.7 and freeglut

**Windows:** nothing to install. A copy of PyOpenGL 3.1.7 is bundled in
`OpenGL/` together with the freeglut DLLs. The PyPI version of PyOpenGL does
not include these DLLs, so the bundled copy is what lets the game run without
extra setup.

```bash
python RPG.py
```

**Linux / macOS:** install freeglut through your package manager (for example,
`sudo apt install freeglut3-dev` on Debian or Ubuntu), then:

```bash
pip install -r requirements.txt
python RPG.py
```

## Project structure

```
RPG.py            the whole game: state, entities, rendering, input, game loop
OpenGL/           bundled PyOpenGL 3.1.7 with freeglut / GLE DLLs for Windows
requirements.txt  PyOpenGL version for Linux / macOS installs
```
