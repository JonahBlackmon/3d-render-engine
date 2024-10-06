import numpy as np
import re
import pygame
import math
import sys
from moviepy.editor import ImageSequenceClip
from functions.pathConfig import get_default
from functions.stlGen import GPTQuestion
import time

DEFAULT_PATH = f"{get_default()}/3DRender/"
FILE_PATH = f"{DEFAULT_PATH}stlfile.txt"

with open(FILE_PATH, 'w') as file:
    file.write(GPTQuestion("Make me a Trapezoidal prism"))
time.sleep(3)

# Size of pygame wiwndow
WINDOW_SIZE = 800
# Scale applied to points
SCALE = 100
window = pygame.display.set_mode( (WINDOW_SIZE, WINDOW_SIZE) )
clock = pygame.time.Clock()

# Matrix to determine x, y position of x, y, z position in a 2d plane
PROJECTION_MATRIX = np.array([[1, 0, 0],
                              [0, 1, 0],
                              [0, 0, 0]])

# Extracts all vertices from stl file in ASCII format
def extract_vertices(filename):
    with open(filename, 'r') as file:
        content = file.read()

    # Regex pattern to find content between 'outerloop' and 'endloop'
    pattern = r'outer loop(.*?)endloop'
    
    # Find all matches
    matches = re.findall(pattern, content, re.DOTALL)

    # Process matches if needed (e.g., strip whitespace)
    extracted_strings = [match.strip() for match in matches]
    
    return extracted_strings
# Extracts all positions from line in stl file and returns list
def extract_positions(input_string):
    # Regex pattern to find positions separated by spaces
    pattern = r'\b\d+(?:\.\d+)?\b'

    # Find all matches in the input string
    positions = re.findall(pattern, input_string)
    # Convert matched strings to integers
    numbers = []

    for match in positions:
        numbers.append(float(match))
    return numbers

# Removes all duplicate vertices from faces
def deduplicate_vertices(faces):
    vertex_map = {}
    unique_vertices = []
    
    for vertex in faces:
        for vert in vertex:
            # Convert the list or numpy array into a tuple for hashing
            vert_tuple = tuple([v[0] for v in vert])
            
            if vert_tuple not in vertex_map:
                vertex_map[vert_tuple] = len(unique_vertices)
                unique_vertices.append(vert)
    
    return vertex_map

# Takes all valid vertices and maps all connections between vertices stopping only when a vertex is connected to 2 other vertices
def generate_connections(vertices):
    edges = []
    logged = []
    num_vertices = len(vertices)
    # Initial loop, establishes connections based on proximity
    for i in range(num_vertices):
        for j in range(i + 1, num_vertices):
            # Check if two vertices differ by exactly one coordinate (implies they are adjacent in 3D space)
            differences = np.sum(vertices[i] != vertices[j])
            
            if differences == 1:
                logged.append((vertices[i], vertices[j]))
                edges.append((i, j))
    detached = []
    # Finds all vertices that have less than 3 connections to other vertices
    for i in range(len(vertices)):
        count = 0
        for log in logged:
            if ((np.array_equal(vertices[i], log[0])) or (np.array_equal(vertices[i], log[1]) )):
                count += 1
        if count != 3:
            detached.append((vertices[i], count))
    new_connections = []
    tracker = []
    for d in detached:
        for l in detached:
            tracker.append((d[0], l[0]))
            newPass = False
            for t in tracker:
                if (t[0].all() == d[0].all() and t[1].all() == l[0].all()):
                    newPass = True
            if ((d is not l) and (newPass)):
                for i in range(num_vertices):
                    for j in range(num_vertices):
                        if (np.where(vertices[i] == d[0]) and np.where(vertices[j] == l[0])):
                            differences = np.sum(vertices[i] != vertices[j])
                            if differences != 0:
                                new_connections.append((differences, i, j, d[1], l[1]))
    # removes duplicate vertices
    new_connections = removeDuplicates(new_connections)
    # sets list to only the vertices that require new connections
    new_connections = filter_connections(new_connections, edges)
    # adds new connections to edges
    for i in range(len(new_connections)):
        edges.append((new_connections[i][1], new_connections[i][2]))

    return edges

# Removes all duplicates from new_connections based on the second and third index, which
# represent the index of the vertex in the list of vertices
def removeDuplicates(arr):
    unique_list = []
    seen_pairs = set()  # To keep track of pairs (second, third)

    for item in arr:
        second, third = item[1], item[2]
        if (second, third) not in seen_pairs:
            unique_list.append(item)
            seen_pairs.add((second, third))

    return unique_list

# returns a list of which connections to be made that is created in order
# based on the number of connections a vertex needs to make
# and the proximity of a vertex to another vertex, only connecting 
# the closest vertices that need a pair that are not already connected
def filter_connections(arr, existing_connections):
    # Dictionary to track how many connections each vertex has
    connection_count = {}
    
    # Set to track existing connections (both pre-existing and new ones)
    connections = set()
    
    # Add all existing connections to the connections set
    for conn in existing_connections:
        vertex1, vertex2 = conn
        connections.add((vertex1, vertex2))
        connections.add((vertex2, vertex1))  # Track both directions for easy lookup

        # Initialize the connection counts for pre-existing vertices
        if vertex1 not in connection_count:
            connection_count[vertex1] = 1
        else:
            connection_count[vertex1] += 1

        if vertex2 not in connection_count:
            connection_count[vertex2] = 1
        else:
            connection_count[vertex2] += 1

    # List to store the final connections
    result = []

    # Sort the array by the first element (distance) to prioritize smaller distances
    arr.sort(key=lambda x: x[0])

    # Process each list, ensuring each vertex has no more than 3 connections
    for item in arr:
        _, vertex1, vertex2, count1, count2 = item
        
        # Initialize the connection counts if not already in the dictionary
        if vertex1 not in connection_count:
            connection_count[vertex1] = count1
        if vertex2 not in connection_count:
            connection_count[vertex2] = count2

        # Check if both vertices can still be connected (less than 3 connections)
        # and if they are not already connected to each other
        if connection_count[vertex1] < 3 and connection_count[vertex2] < 3:
            if (vertex1, vertex2) not in connections and (vertex2, vertex1) not in connections:
                # Add the connection to the result list
                result.append(item)

                # Update the connection counts
                connection_count[vertex1] += 1
                connection_count[vertex2] += 1

                # Record the connection in both directions
                connections.add((vertex1, vertex2))
                connections.add((vertex2, vertex1))

    return result

# draws line of connected points in pygame
def connect_points(i, j, edges):
    pygame.draw.line(window, (255, 255, 255), ( edges[i][0], edges[i][1] ), ( edges[j][0], edges[j][1] ))


stl_content = extract_vertices(FILE_PATH)

faces = []
# Loop to organize all vertices into a format that can be used in numpy matrix multiplication
for content in stl_content:
    vertices = []
    for line in content.splitlines():
        points = []
        for point in extract_positions(line):
            temp_array = [point + 1]
            points.append(temp_array)
        vertices.append(points)
        
    faces.append(vertices)

parsed_verts = deduplicate_vertices(faces)
converted_verts = []

for key, value in parsed_verts.items():
    keys = []
    for k in key:
        keys.append([k])
    converted_verts.append(keys)

converted_verts = np.array(converted_verts)

angle_x = angle_y = angle_z = 0
edge_pairs = generate_connections(converted_verts)
count = 0
frames = []

while True:
    # resets window every pass through
    window.fill((0, 0, 0))
    # matrices that determine the projection of the point based on the rotation applied for
    # the x, y, and z coordinates
    rotation_x = [[1, 0, 0],
                  [0, math.cos(angle_x), -math.sin(angle_x)],
                  [0, math.sin(angle_x), math.cos(angle_x)]]
    rotation_y = [[math.cos(angle_y), 0, math.sin(angle_y)],
                  [0, 1, 0],
                  [-math.sin(angle_y), 0, math.cos(angle_y)]]
    rotation_z = [[math.cos(angle_z), -math.sin(angle_z), 0],
                  [math.sin(angle_z), math.cos(angle_z), 0],
                  [0, 0, 1]]
    # controls the rotational speed of animation
    angle_x += 0.01
    angle_y += 0.01
    angle_z += 0.01
    clock.tick(60)
    edges = [0 for _ in range(len(converted_verts))]
    i = 0
    # animates the point in the window
    for point in converted_verts:
        rotate_x = np.matmul(rotation_x, point)
        rotate_y = np.matmul(rotation_y, rotate_x)
        rotate_z = np.matmul(rotation_z, rotate_y)

        point_2d = np.matmul(PROJECTION_MATRIX, rotate_z)
        
        x = (point_2d[0][0] * SCALE) + WINDOW_SIZE/3
        y = (point_2d[1][0] * SCALE) + WINDOW_SIZE/3
        edges[i] = (x, y)
        i += 1
        pygame.draw.circle(window, (255, 0, 0), (x, y), 5)
    if (count == 0):
        count += 1
    for i in range(len(edge_pairs)):
        connect_points(edge_pairs[i][0], edge_pairs[i][1], edges)
    frame = pygame.surfarray.array3d(pygame.display.get_surface())
    frames.append(frame)
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
    if len(frames) >= 785: # for ~13 seconds at 60 fps
        break
    pygame.display.update()

# Convert the frames into a format suitable for moviepy
frames = [np.transpose(frame, (1, 0, 2)) for frame in frames]  # Transpose to (height, width, 3)

# Create a video clip from the frames
clip = ImageSequenceClip(frames, fps=60)

# Write the video to a file
clip.write_videofile(f'{DEFAULT_PATH}animation.mp4', codec='libx264')
