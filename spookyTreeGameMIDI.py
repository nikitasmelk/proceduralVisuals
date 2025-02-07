import pygame
import pygame.midi
import sys
import random
import math
import colorsys

# ----------------------------------------------------
# Global Variables & Configurations
# ----------------------------------------------------
# Color configuration variables (change each element as desired):
BG_COLOR = (12, 0, 38)
FRUIT_COLOR = (198, 174, 255)
BUTTERFLY_COLOR = (200, 100, 250)

# Background screens to cycle through (not used in MIDI logic here)
SCREEN_COLORS = [
    (10, 10, 30),
    (30, 10, 30),
    (10, 30, 30)
]
current_screen_index = 0

# Tree parameters – now trees are smaller and shorter.
# They will spawn from any edge.
INITIAL_BRANCH_DELAY = 130   # initial delay (ms) between branch additions
DELAY_DECAY_FACTOR = 0.95    # each new branch reduces delay a bit
MIN_BRANCH_DELAY = 50

# Tree animation speeds (speed factor multiplies the effective branch delay)
TREE_SPEED_ANIM1 = 3.0
TREE_SPEED_ANIM2 = 0.5
TREE_SPEED_ANIM3 = 0.5

# New tree spawn intervals (in ms)
TREE_SPAWN_INTERVAL_PHASE1 = 2000
TREE_SPAWN_INTERVAL_PHASE23 = 15000

def get_random_tree_params():
    length = random.uniform(40, 160)
    width = random.uniform(5, 25)
    max_depth = random.choice([2, 6])
    return length, width, max_depth

# Fruit parameters:
FRUIT_GROWTH_SPEED = 0.005       # Growth rate (0.0 to 1.0)
FRUIT_SIZE = 12                  # Base size (will be scaled by growth)
FRUIT_SPAWN_INTERVAL = 1000      # Initial interval (ms) between fruit spawns
MIN_FRUIT_SPAWN_INTERVAL = 300   # Minimum allowed spawn interval
FRUIT_SPAWN_DECAY = 0.98         # Each spawn reduces the interval (more fruits over time)

# Butterfly parameters:
BUTTERFLY_TRANSFORM_INTERVAL = 100  # Interval (ms) between converting a fruit to a butterfly
BUTTERFLY_SCALE_FACTOR = 2.0          # Base butterfly size scale

# Global containers:
trees = []         # List of Tree objects
fruits = []        # List of Fruit objects
butterflies = []   # List of Butterfly objects
branch_points = [] # Recorded branch endpoints (for fruit attachment)

# Animation state:
# 0: Waiting to start
# 1: Animation 1 – Fast tree growth
# 2: Animation 2 – Fruit growth (trees keep growing, but slower)
# 3: Animation 3 – Butterfly flight (trees keep growing, but slower)
state = 0

last_tree_spawn_time = 0
last_fruit_spawn_time = 0
last_butterfly_transform_time = 0

# ----------------------------------------------------
# Helper Functions
# ----------------------------------------------------
def get_random_tree_spawn():
    """Return a random spawn position on one of the screen edges along with a default growth angle."""
    angle_offset = random.uniform(-0.2, 0.2)
    edge = random.choice(["top", "bottom", "left", "right"])
    if edge == "bottom":
        pos = (random.randint(0, screen_width), screen_height)
        angle = -math.pi/2 + angle_offset  # grow upward
    elif edge == "top":
        pos = (random.randint(0, screen_width), 0)
        angle = math.pi/2 + angle_offset   # grow downward
    elif edge == "left":
        pos = (0, random.randint(0, screen_height))
        angle = 0 + angle_offset           # grow rightward
    elif edge == "right":
        pos = (screen_width, random.randint(0, screen_height))
        angle = math.pi + angle_offset     # grow leftward
    return pos, angle

# ----------------------------------------------------
# Classes
# ----------------------------------------------------
class Branch:
    """
    A branch is drawn as a thick trapezoid.
    """
    def __init__(self, start, angle, length, bottom_width, top_width):
        self.start = start
        self.angle = angle
        self.length = length
        self.bottom_width = bottom_width
        self.top_width = top_width

    def get_full_end(self):
        return (self.start[0] + self.length * math.cos(self.angle),
                self.start[1] + self.length * math.sin(self.angle))

    def draw(self, surface):
        end = self.get_full_end()
        # Compute perpendicular vector for thickness:
        nx = -math.sin(self.angle)
        ny = math.cos(self.angle)
        start_left  = (self.start[0] + nx * self.bottom_width / 2,
                       self.start[1] + ny * self.bottom_width / 2)
        start_right = (self.start[0] - nx * self.bottom_width / 2,
                       self.start[1] - ny * self.bottom_width / 2)
        end_left    = (end[0] + nx * self.top_width / 2,
                       end[1] + ny * self.top_width / 2)
        end_right   = (end[0] - nx * self.top_width / 2,
                       end[1] - ny * self.top_width / 2)
        pygame.draw.polygon(surface, (252, 250, 255),
                            [start_left, end_left, end_right, start_right])

class Tree:
    """
    A tree grows by adding one branch at a time.
    The trunk is created using the given initial angle.
    """
    def __init__(self, base_position, initial_angle, length, width, max_depth, branch_delay=INITIAL_BRANCH_DELAY):
        self.base_position = base_position
        self.initial_angle = initial_angle
        self.pending_branches = []  # Branches waiting to be added
        self.drawn_branches = []    # Branches already drawn
        self.max_depth = max_depth
        self.branch_growth_delay = branch_delay
        self.last_branch_growth_time = pygame.time.get_ticks()
        # Create the trunk.
        trunk = Branch(base_position, initial_angle, length, width, width * 0.8)
        self.pending_branches.append(trunk)
        self.generate_children(trunk, max_depth)

    def generate_children(self, parent, depth):
        if depth <= 0:
            branch_points.append(parent.get_full_end())
            return
        if depth > 1:
            # Two children with very chaotic angle offsets.
            left_offset = random.uniform(-1.5, -0.2)
            right_offset = random.uniform(0.2, 1.5)
            for angle in [parent.angle + left_offset, parent.angle + right_offset]:
                child_length = parent.length * random.uniform(0.6, 0.9)
                child_width = parent.top_width * random.uniform(0.6, 0.9)
                child = Branch(parent.get_full_end(), angle, child_length, child_width, child_width * 0.8)
                self.pending_branches.append(child)
                self.generate_children(child, depth - 1)
        else:
            # Single child with a very random offset.
            child_angle = parent.angle + random.uniform(-1.0, 1.0)
            child_length = parent.length * random.uniform(0.6, 0.9)
            child_width = parent.top_width * random.uniform(0.6, 0.9)
            child = Branch(parent.get_full_end(), child_angle, child_length, child_width, child_width * 0.8)
            self.pending_branches.append(child)
            self.generate_children(child, depth - 1)

    def update(self, current_time, speed_factor=1.0):
        effective_delay = self.branch_growth_delay / speed_factor
        if self.pending_branches and (current_time - self.last_branch_growth_time >= effective_delay):
            branch = self.pending_branches.pop(0)
            self.drawn_branches.append(branch)
            self.last_branch_growth_time = current_time
            self.branch_growth_delay = max(self.branch_growth_delay * DELAY_DECAY_FACTOR, MIN_BRANCH_DELAY)
        return len(self.pending_branches) == 0

    def draw(self, surface):
        for branch in self.drawn_branches:
            branch.draw(surface)

class Fruit:
    """
    A fruit now appears as a complex figure made from 2 or 3 stacked trapezoids.
    Its color saturates as it grows.
    """
    def __init__(self, position):
        self.position = position  # Bottom–center of the fruit.
        self.growth = 0.0         # 0.0 to 1.0
        self.fully_grown = False
        self.size = FRUIT_SIZE
        self.parts = random.choice([2, 3])  # Number of stacked trapezoids.
        r, g, b = FRUIT_COLOR
        self.base_h, self.base_l, self.base_s = colorsys.rgb_to_hls(r/255.0, g/255.0, b/255.0)

    def update(self):
        if not self.fully_grown:
            self.growth += FRUIT_GROWTH_SPEED
            if self.growth >= 1.0:
                self.growth = 1.0
                self.fully_grown = True

    def draw(self, surface):
        current_size = self.size * self.growth
        new_sat = 0.3 + 0.7 * self.growth
        r, g, b = colorsys.hls_to_rgb(self.base_h, self.base_l, new_sat)
        color = (int(r * 255), int(g * 255), int(b * 255))
        x, y = self.position
        num_parts = self.parts
        part_height = current_size / num_parts
        for i in range(num_parts):
            bottom_width = current_size * (1 - 0.1 * i)
            top_width = current_size * (1 - 0.1 * (i + 1))
            y_bottom = y - i * part_height
            y_top = y - (i + 1) * part_height
            points = [
                (x - bottom_width/2, y_bottom),
                (x + bottom_width/2, y_bottom),
                (x + top_width/2, y_top),
                (x - top_width/2, y_top)
            ]
            pygame.draw.polygon(surface, color, points)

class Butterfly:
    """
    A butterfly made of two trapezoidal wings.
    Its wings flap rapidly.
    """
    def __init__(self, position):
        self.position = list(position)
        self.velocity = [random.uniform(-2, 2), random.uniform(-2, 2)]
        self.wing_flap_timer = 0.0
        self.scale = BUTTERFLY_SCALE_FACTOR * random.uniform(0.8, 1.2)

    def update(self, screen_width, screen_height):
        self.wing_flap_timer += 1.0
        self.position[0] += self.velocity[0]
        self.position[1] += self.velocity[1]
        self.velocity[0] += random.uniform(-0.1, 0.1)
        self.velocity[1] += random.uniform(-0.1, 0.1)
        speed = math.hypot(self.velocity[0], self.velocity[1])
        max_speed = 3
        if speed > max_speed:
            self.velocity[0] = (self.velocity[0] / speed) * max_speed
            self.velocity[1] = (self.velocity[1] / speed) * max_speed
        if self.position[0] < 0 or self.position[0] > screen_width:
            self.velocity[0] *= -1
        if self.position[1] < 0 or self.position[1] > screen_height:
            self.velocity[1] *= -1

    def draw(self, surface):
        x, y = self.position
        wing_size = 4 * self.scale
        flap = math.sin(self.wing_flap_timer) * 10
        left_wing = [
            (x, y),
            (x - wing_size, y - wing_size/2 + flap),
            (x - wing_size, y - wing_size + flap),
            (x, y - wing_size/2)
        ]
        right_wing = [
            (x, y),
            (x + wing_size, y - wing_size/2 + flap),
            (x + wing_size, y - wing_size + flap),
            (x, y - wing_size/2)
        ]
        pygame.draw.polygon(surface, BUTTERFLY_COLOR, left_wing)
        pygame.draw.polygon(surface, BUTTERFLY_COLOR, right_wing)

# ----------------------------------------------------
# Pygame and MIDI Setup
# ----------------------------------------------------
pygame.init()
pygame.midi.init()
midi_input_id = pygame.midi.get_default_input_id()
print("Default MIDI Input ID:", midi_input_id)
midi_input = pygame.midi.Input(midi_input_id)

infoObject = pygame.display.Info()
screen_width = infoObject.current_w
screen_height = infoObject.current_h
screen = pygame.display.set_mode((screen_width, screen_height), pygame.FULLSCREEN)
pygame.display.set_caption("Trippy, Spooky, Chaotic Trees, Fruits & Butterflies")
clock = pygame.time.Clock()

last_tree_spawn_time = pygame.time.get_ticks()
last_fruit_spawn_time = pygame.time.get_ticks()
last_butterfly_transform_time = pygame.time.get_ticks()

# ----------------------------------------------------
# Main Loop (MIDI CC-Based State Transitions)
# ----------------------------------------------------
running = True
while running:
    current_time = pygame.time.get_ticks()
    
    # Process standard Pygame events (only ESC to quit)
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                running = False

    # Process MIDI events.
    if midi_input.poll():
        midi_events = midi_input.read(10)  # Read up to 10 events
        for event in midi_events:
            data = event[0]  # Data format: [status, cc_number, cc_value, _]
            status, cc_number, cc_value, _ = data
            print("MIDI Event - Status: {}, CC#: {}, Value: {}".format(status, cc_number, cc_value))
            # Check for a Control Change message (masking the lower 4 bits) on any channel.
            if (status & 0xF0) == 176 and cc_number == 18 and cc_value > 64:
                # Use CC 18 to cycle through states.
                if state == 0:
                    state = 1
                    pos, angle = get_random_tree_spawn()
                    length, width, max_depth = get_random_tree_params()
                    trees.append(Tree(pos, angle, length, width, max_depth))
                    print("Switching to state 1: Starting tree growth.")
                elif state == 1:
                    state = 2
                    print("Switching to state 2: Fruit growth.")
                elif state == 2:
                    state = 3
                    print("Switching to state 3: Butterfly flight.")
                # (Once in state 3, further CC events on 18 do not change the state.)

    screen.fill(BG_COLOR)

    # ----------------------------------------------------
    # Animation Logic
    # ----------------------------------------------------
    if state == 1:
        # Animation 1: Fast tree growth.
        for tree in trees:
            tree.update(current_time, speed_factor=TREE_SPEED_ANIM1)
            tree.draw(screen)
        if trees and len(trees[0].pending_branches) == 0:
            if current_time - last_tree_spawn_time > TREE_SPAWN_INTERVAL_PHASE1:
                pos, angle = get_random_tree_spawn()
                length, width, max_depth = get_random_tree_params()
                new_tree = Tree(pos, angle, length, width, max_depth)
                trees.append(new_tree)
                last_tree_spawn_time = current_time
    elif state in (2, 3):
        # In animations 2 & 3, trees continue growing, but slower.
        speed = TREE_SPEED_ANIM2 if state == 2 else TREE_SPEED_ANIM3
        for tree in trees:
            tree.update(current_time, speed_factor=speed)
            tree.draw(screen)
        if current_time - last_tree_spawn_time > TREE_SPAWN_INTERVAL_PHASE23:
            pos, angle = get_random_tree_spawn()
            length, width, max_depth = get_random_tree_params()
            new_tree = Tree(pos, angle, length, width, max_depth)
            trees.append(new_tree)
            last_tree_spawn_time = current_time

        if state == 2:
            # Fruit growth phase.
            if current_time - last_fruit_spawn_time > FRUIT_SPAWN_INTERVAL:
                available_points = [pt for pt in branch_points
                                    if not any(math.hypot(pt[0] - f.position[0],
                                                          pt[1] - f.position[1]) < 5 for f in fruits)]
                if available_points:
                    pt = random.choice(available_points)
                    new_fruit = Fruit(pt)
                    fruits.append(new_fruit)
                    FRUIT_SPAWN_INTERVAL = max(MIN_FRUIT_SPAWN_INTERVAL, FRUIT_SPAWN_INTERVAL * FRUIT_SPAWN_DECAY)
                last_fruit_spawn_time = current_time
            for fruit in fruits:
                fruit.update()
                fruit.draw(screen)
        elif state == 3:
            # Butterfly flight phase.
            for fruit in fruits:
                fruit.draw(screen)
            if fruits and current_time - last_butterfly_transform_time > BUTTERFLY_TRANSFORM_INTERVAL:
                fruit = fruits.pop(0)
                new_butterfly = Butterfly(fruit.position)
                butterflies.append(new_butterfly)
                last_butterfly_transform_time = current_time
            for butterfly in butterflies:
                butterfly.update(screen_width, screen_height)
                butterfly.draw(screen)

    pygame.display.flip()
    clock.tick(60)

# Cleanup: close MIDI input and quit.
midi_input.close()
pygame.midi.quit()
pygame.quit()
sys.exit()
