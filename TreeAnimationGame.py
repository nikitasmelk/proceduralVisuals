import pygame
import sys
import random
import math
import colorsys

# ----------------------------------------------------
# Global Variables & Configurations
# ----------------------------------------------------
# Background & Fruit colors
BG_COLOR = (255, 255, 255)            # initial background color (white)
FRUIT_COLOR = (255, 0, 0)             # base fruit color (red)

# A few background “screens” you can cycle through:
SCREEN_COLORS = [(255, 255, 255), (240, 240, 255), (255, 240, 240)]
current_screen_index = 0

# Timing intervals for spawning new trees (in milliseconds)
SLOW_TREE_SPAWN_INTERVAL = 1000  # while initial tree is growing
FAST_TREE_SPAWN_INTERVAL = 200   # after initial tree is finished

# Fruit growth per frame (0..1 scale)
FRUIT_GROWTH_RATE = 0.01

# How fast fruits are converted to butterflies:
BUTTERFLY_TRANSFORM_INTERVAL = 100

# Global lists:
trees = []         # list of Tree objects
fruits = []        # list of Fruit objects
butterflies = []   # list of Butterfly objects
branch_points = [] # branch endpoints (for fruit attachment)

# Animation state:
# 0: Waiting to start
# 1: Tree growth animation
# 2: Fruit growth animation
# 3: Butterfly flight animation
state = 0

# Timers (initialized later in main loop)
last_tree_spawn_time = 0
last_fruit_spawn_time = 0
last_butterfly_transform_time = 0

# ----------------------------------------------------
# Helper Classes
# ----------------------------------------------------
class Branch:
    """
    A simple branch drawn as a trapezoid.
    It stores a starting point, an angle, a length, and two widths (bottom and top).
    """
    def __init__(self, start, angle, length, bottom_width, top_width):
        self.start = start
        self.angle = angle
        self.length = length
        self.bottom_width = bottom_width
        self.top_width = top_width

    def get_full_end(self):
        """Return the endpoint of the branch."""
        return (self.start[0] + self.length * math.cos(self.angle),
                self.start[1] + self.length * math.sin(self.angle))

    def draw(self, surface):
        """Draw the branch as a trapezoid."""
        end = self.get_full_end()
        # Compute a perpendicular (normal) vector:
        nx = -math.sin(self.angle)
        ny = math.cos(self.angle)
        start_left  = (self.start[0] + nx * self.bottom_width/2,
                       self.start[1] + ny * self.bottom_width/2)
        start_right = (self.start[0] - nx * self.bottom_width/2,
                       self.start[1] - ny * self.bottom_width/2)
        end_left    = (end[0] + nx * self.top_width/2,
                       end[1] + ny * self.top_width/2)
        end_right   = (end[0] - nx * self.top_width/2,
                       end[1] - ny * self.top_width/2)
        pygame.draw.polygon(surface, (0, 0, 0),
                            [start_left, end_left, end_right, start_right])

class Tree:
    """
    A Tree is generated recursively but built (drawn) one branch (trapezoid) per frame.
    When a branch is a “leaf” (i.e. no children are generated), its endpoint is stored
    for later fruit attachment.
    """
    def __init__(self, base_position, initial_length, initial_width, max_depth):
        self.base_position = base_position
        self.drawn_branches = []    # branches already drawn
        self.pending_branches = []  # branches waiting to be added (one per frame)
        self.length = initial_length
        self.max_depth = max_depth

        # Create the trunk (grows upward from the base)
        trunk = Branch(base_position, -math.pi/2, initial_length, initial_width, initial_width * 0.3)
        self.pending_branches.append(trunk)
        # Recursively generate children; note: branch endpoints (leaves) are recorded.
        self.generate_children(trunk, max_depth)

    def generate_children(self, parent, depth):
        if depth <= 0:
            # A leaf branch – record its endpoint.
            branch_points.append(parent.get_full_end())
            return
        # For a sharper, more “pointy” look use small angle offsets.
        num_children = 2 if depth > 1 else 1
        for i in range(num_children):
            if num_children == 1:
                child_angle = parent.angle + random.uniform(-0.1, 0.1)
            else:
                # For two children, one goes slightly left and one right.
                if i == 0:
                    child_angle = parent.angle - random.uniform(0.1, 0.3)
                else:
                    child_angle = parent.angle + random.uniform(0.1, 0.3)
            child_length = parent.length * random.uniform(0.6, 0.8)
            child_width = parent.top_width * random.uniform(0.6, 0.8)
            child = Branch(parent.get_full_end(), child_angle, child_length, child_width, child_width * 0.3)
            self.pending_branches.append(child)
            self.generate_children(child, depth - 1)

    def update(self):
        """Each frame add (draw) at most one new branch from the pending list."""
        if self.pending_branches:
            branch = self.pending_branches.pop(0)
            self.drawn_branches.append(branch)
        return len(self.pending_branches) == 0  # Returns True if tree is finished

    def draw(self, surface):
        """Draw all branches that have been added so far."""
        for branch in self.drawn_branches:
            branch.draw(surface)

class Fruit:
    """
    A tiny fruit that appears at a branch endpoint.
    Its shape is chosen at random and its color becomes more saturated as it grows.
    """
    def __init__(self, position):
        self.position = position  # bottom–center of the fruit
        self.growth = 0.0         # from 0.0 to 1.0
        self.fully_grown = False
        self.size = 8             # final size (tiny)
        self.shape = random.choice(["trapezoid", "diamond", "triangle"])
        # Precompute the base HLS (for saturation adjustment) from FRUIT_COLOR:
        r, g, b = FRUIT_COLOR
        self.base_h, self.base_l, self.base_s = colorsys.rgb_to_hls(r/255.0, g/255.0, b/255.0)

    def update(self):
        if not self.fully_grown:
            self.growth += FRUIT_GROWTH_RATE
            if self.growth >= 1.0:
                self.growth = 1.0
                self.fully_grown = True

    def draw(self, surface):
        current_size = self.size * self.growth
        # Increase saturation from a low value (0.3) to nearly full (1.0) as the fruit grows.
        new_sat = 0.3 + 0.7 * self.growth
        r, g, b = colorsys.hls_to_rgb(self.base_h, self.base_l, new_sat)
        color = (int(r*255), int(g*255), int(b*255))
        x, y = self.position
        if self.shape == "trapezoid":
            bw = current_size
            tw = current_size * 0.8
            h = current_size * 0.5
            points = [(x - bw/2, y),
                      (x + bw/2, y),
                      (x + tw/2, y - h),
                      (x - tw/2, y - h)]
        elif self.shape == "diamond":
            points = [(x - current_size/2, y),
                      (x, y - current_size/2),
                      (x + current_size/2, y),
                      (x, y + current_size/2)]
        elif self.shape == "triangle":
            points = [(x - current_size/2, y),
                      (x + current_size/2, y),
                      (x, y - current_size)]
        else:
            points = []
        if points:
            pygame.draw.polygon(surface, color, points)

class Butterfly:
    """
    A tiny butterfly consisting only of two trapezoidal wings.
    Its wings flap rapidly.
    """
    def __init__(self, position):
        self.position = list(position)
        self.velocity = [random.uniform(-2, 2), random.uniform(-2, 2)]
        self.wing_flap_timer = 0.0

    def update(self, screen_width, screen_height):
        self.wing_flap_timer += 0.5  # faster flapping
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
        wing_size = 5  # tiny wings
        # Compute a flap offset (in degrees)
        flap = math.sin(self.wing_flap_timer) * 10
        # Two simple trapezoidal wings (no body)
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
        wing_color = (200, 100, 200)
        pygame.draw.polygon(surface, wing_color, left_wing)
        pygame.draw.polygon(surface, wing_color, right_wing)

# ----------------------------------------------------
# Pygame Setup
# ----------------------------------------------------
pygame.init()
infoObject = pygame.display.Info()
screen_width = infoObject.current_w
screen_height = infoObject.current_h
screen = pygame.display.set_mode((screen_width, screen_height), pygame.FULLSCREEN)
pygame.display.set_caption("Simplified Tree, Fruit & Butterfly Animation")
clock = pygame.time.Clock()

# Initialize timers:
last_tree_spawn_time = pygame.time.get_ticks()
last_fruit_spawn_time = pygame.time.get_ticks()
last_butterfly_transform_time = pygame.time.get_ticks()

# ----------------------------------------------------
# Main Loop
# ----------------------------------------------------
running = True
while running:
    current_time = pygame.time.get_ticks()
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                running = False
            elif event.key == pygame.K_n:
                # Advance to the next animation phase:
                if state == 0:
                    state = 1
                    # Start with one tree growing slowly from the center-bottom.
                    center_tree = Tree((screen_width // 2, screen_height), 80, 16, 4)
                    trees.append(center_tree)
                elif state == 1:
                    state = 2
                elif state == 2:
                    state = 3
            elif event.key == pygame.K_s:
                # Cycle through background screens.
                current_screen_index = (current_screen_index + 1) % len(SCREEN_COLORS)
                BG_COLOR = SCREEN_COLORS[current_screen_index]
            elif event.key == pygame.K_c:
                # Clear the canvas (reset everything).
                trees = []
                fruits = []
                butterflies = []
                branch_points = []
                state = 0

    # Fill background
    screen.fill(BG_COLOR)

    # --------------------------
    # Animation 1: Tree Growth
    # --------------------------
    if state == 1:
        for tree in trees:
            tree.update()   # each tree adds at most one branch per frame
            tree.draw(screen)
        # After the initial (center) tree is finished, spawn new trees quickly.
        if trees and trees[0].pending_branches == []:
            if current_time - last_tree_spawn_time > FAST_TREE_SPAWN_INTERVAL:
                x = random.randint(50, screen_width - 50)
                new_tree = Tree((x, screen_height),
                                random.uniform(50, 100),
                                random.uniform(12, 20),
                                random.randint(2, 4))
                trees.append(new_tree)
                last_tree_spawn_time = current_time
        else:
            # (Optional) While the initial tree is still growing, you may spawn trees slowly.
            if current_time - last_tree_spawn_time > SLOW_TREE_SPAWN_INTERVAL and len(trees) < 1:
                x = screen_width // 2
                new_tree = Tree((x, screen_height),
                                random.uniform(50, 100),
                                random.uniform(12, 20),
                                random.randint(2, 4))
                trees.append(new_tree)
                last_tree_spawn_time = current_time

    # --------------------------
    # Animation 2: Fruit Growth
    # --------------------------
    elif state == 2:
        # Draw the (completed) trees.
        for tree in trees:
            tree.draw(screen)
        # Every so often, plant a new fruit at an available branch point.
        if current_time - last_fruit_spawn_time > 500:
            available_points = [pt for pt in branch_points
                                if not any(math.hypot(pt[0] - f.position[0],
                                                      pt[1] - f.position[1]) < 5 for f in fruits)]
            if available_points:
                pt = random.choice(available_points)
                new_fruit = Fruit(pt)
                fruits.append(new_fruit)
            last_fruit_spawn_time = current_time
        for fruit in fruits:
            fruit.update()
            fruit.draw(screen)

    # --------------------------
    # Animation 3: Butterfly Flight
    # --------------------------
    elif state == 3:
        # Draw trees and remaining fruits.a
        for tree in trees:
            tree.draw(screen)
        for fruit in fruits:
            fruit.draw(screen)
        # Gradually convert fruits into butterflies.
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

pygame.quit()
sys.exit()
