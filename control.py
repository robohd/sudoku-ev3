#!/usr/bin/python3

###
#
# MIT License
#
# Copyright (c) 2016 Daniela Kilian, Lea Reisinger, Martin Drawitsch
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
#
###

import ev3dev.ev3 as ev3
from time import sleep
from math import sqrt

from solve import Sudoku, solve


### GLOBAL VARIABLES

# Motor speeds
SPEED_X = 180
SPEED_Y = 55
SPEED_C = 40

# Factors that translate motor angles to fields
RX = 112
RY = 41

# Relative offsets that determine distance between color sensor and pen
OFF_X = 150
OFF_Y = -55

# Correction factors for physical biases
PEN_GX_CORR = 0  # Motor moving more in positive direction than in negative direction
#             # (This effect magically disappeared overnight, therefore now set to 0).
PEN_DOWN_CORR = 1  # Compensate for slightly sloping table

# Distance between pen points in numbers
PX = RX / 5
PY = RY / 4

PEN_IDLE_POS = 0
PEN_WRITE_POS = 6

MWT = 0.1  # Motor wait time (check interval for check if a motor is running)
PEN_DOT_TIME = 0.1  # Time that is spent with pen being down (more time -> bigger dot for marker)

# Map color numbers to color names
COLORTABLE = {
    0: 'white',
    1: 'yellow',
    2: 'dark green',
    3: 'baby blue',
    4: 'dark blue',
    5: 'black',
    6: 'red',
    7: 'pink',
    8: 'rose',
    9: 'orange',
}

## Example of a sudoku with its solution

EXAMPLE_PUZZLE_STR = """
0 3 0 0 5 0 0 4 0
0 0 8 0 1 0 5 0 0
4 6 0 0 0 0 0 1 2
0 7 0 5 0 2 0 8 0
0 0 0 6 0 3 0 0 0
0 4 0 1 0 9 0 3 0
2 5 0 0 0 0 0 9 8
0 0 1 0 2 0 6 0 0
0 8 0 0 6 0 0 2 0""".strip()

EXAMPLE_SOLUTION_STR = """
1 3 7 2 5 6 8 4 9
9 2 8 3 1 4 5 6 7
4 6 5 8 9 7 3 1 2
6 7 3 5 4 2 9 8 1
8 1 9 6 7 3 2 5 4
5 4 2 1 8 9 7 3 6
2 5 6 7 3 1 4 9 8
3 9 1 4 2 8 6 7 5
7 8 4 9 6 5 1 2 3""".strip()


## Reference sudoku that we have printed out (for error checking)

REF_PUZZLE_STR = """
3 0 0 8 0 5 0 0 6
0 0 4 0 0 0 1 0 0
1 5 0 2 0 6 0 7 8
0 0 0 1 5 9 0 0 0
0 0 7 0 0 0 9 0 0
0 0 0 6 3 7 0 0 0
9 1 0 3 0 4 0 0 2
0 0 6 0 0 0 8 0 0
2 0 0 0 0 8 0 0 3""".strip()

REF_SOLUTION_STR = """
3 7 2 8 1 5 4 9 6
6 8 4 7 9 3 1 2 5
1 5 9 2 4 6 3 7 8
4 2 3 1 5 9 6 8 7
5 6 7 4 8 2 9 3 1
8 9 1 6 3 7 2 5 4
9 1 8 3 7 4 5 6 2
7 3 6 5 2 1 8 4 9
2 4 5 9 6 8 7 1 3""".strip()


### I/O INITIALIZATION

# Initialize motors
a = ev3.LargeMotor('outA')  # Moves in y direction
b = ev3.LargeMotor('outB')  # Moves in x direction
c = ev3.MediumMotor('outC') # Rotates pen holder ("c direction")

# Initialize sensor
csensor = ev3.ColorSensor()
csensor.mode = 'RGB-RAW'


### FUNCTIONS, SUBROUTINES

## MOTOR CONTROL

def reset():
    """
    Reset every motor to its initial configuration. This does not move anything.
    """
    a.reset()
    b.reset()
    c.reset()
    a.position = 0
    b.position = 0
    c.position = 0
    a.speed_sp = SPEED_Y
    b.speed_sp = SPEED_X
    c.speed_sp = SPEED_C
    a.stop_action = 'brake'
    b.stop_action = 'brake'
    c.stop_action = 'brake'


def is_moving(check_stall=False):
    """
    Check if any motor is currently running.
    Necessary for blocking movement until the wanted position is reached.
    """
    motor_states = a.state + b.state + c.state
    if check_stall and 'stalled' in motor_states:
        print('\nWarning: At least one motor is stalled. Check speed_sp attributes. States:')
        print('A:', a.state)
        print('B:', b.state)
        print('C:', c.state)
    return 'running' in motor_states


def pen_down():
    """
    Move pen down to writing position.
    """
    xmod = round(PEN_DOWN_CORR * b.position / (RX * 9))
    c.run_to_abs_pos(position_sp=PEN_WRITE_POS+xmod)
    sleep(MWT)
    while is_moving():
        sleep(MWT)


def pen_up():
    """
    Move pen up to neutral position.
    """
    c.run_to_abs_pos(position_sp=PEN_IDLE_POS)
    sleep(MWT)
    while is_moving():
        sleep(MWT)


def pen_dot():
    """
    Make a dot with the pen at the current position.
    """
    pen_down()
    sleep(PEN_DOT_TIME)
    pen_up()


# HOW TO WRITE NUMBERS ON PAPER

def one():
    pen_dot()


def two():
    pen_dot()
    mx(-PX)
    pen_dot()
    mx(PX)


def three():
    pen_dot()
    mx(-PX)
    pen_dot()
    mx(-PX)
    pen_dot()
    mx(2*PX)


def four():
    two()
    my(PY)
    two()


def five():
    three()
    my(PY)
    two()


def six():
    three()
    my(PY)
    three()


def seven():
    three()
    my(PY)
    three()
    my(PY)
    one()


def eight():
    three()
    my(PY)
    three()
    my(PY)
    two()


def nine():
    three()
    my(PY)
    three()
    my(PY)
    three()


def write_number(n):
    """
    Make n dots at the current position.

    The position should be adjusted before by pen_gfield().
    """
    {
        1: one,
        2: two,
        3: three,
        4: four,
        5: five,
        6: six,
        7: seven,
        8: eight,
        9: nine
    }[n]()


def move(dx=0, dy=0):
    """
    Turn motors b and a by (dx, dy) degrees.
    """
    if dy != 0:
        a.run_to_rel_pos(position_sp=dy)
    if dx != 0:
        b.run_to_rel_pos(position_sp=dx)
    sleep(MWT)
    while is_moving():
        sleep(MWT)


def mx(dx=0):
    move(dx=dx)


def my(dy=0):
    move(dy=dy)


def mfield(nx=0, ny=0):
    """ move (nx, ny) fields """
    fy = ny*RY
    fx = nx*RX
    if fy != a.position:
        a.run_to_rel_pos(position_sp=ny*RY)
    if fx != b.position:
        b.run_to_rel_pos(position_sp=nx*RX)
    sleep(MWT)
    while is_moving():
        sleep(MWT)


def gfield(nx=0, ny=0):
    """ Move  color sensor to field (nx, ny) """
    fy = ny*RY
    fx = nx*RX
    if fy != a.position:
        a.run_to_abs_pos(position_sp=fy)
    if fx != b.position:
        b.run_to_abs_pos(position_sp=fx)
    sleep(MWT)
    while is_moving():
        sleep(MWT)


def pen_gfield(nx=0, ny=0, off_x=OFF_X, off_y=OFF_Y):
    """
    Move the pen above field (nx, ny) so we can begin writing a number in this field.

    (off_x, off_y) is the relative offset between the color sensor and the pen (in motor angles).
    """
    xmod = -round(PEN_GX_CORR * b.position / (RX * 9))
    fy = ny*RY + off_y
    fx = nx*RX + off_x + xmod
    if fy != a.position:
        a.run_to_abs_pos(position_sp=fy)
    if fx != b.position:
        b.run_to_abs_pos(position_sp=fx)
    sleep(MWT)
    while is_moving():
        sleep(MWT)


def goto(x=0, y=0):
    """
    Move motors to absolute position (x, y) (in angles, not fields).
    """
    fy = y
    fx = x
    if fy != a.position:
        a.run_to_abs_pos(position_sp=y)
    if fx != b.position:
        b.run_to_abs_pos(position_sp=x)
    sleep(MWT)
    while is_moving():
        sleep(MWT)


def origin():
    goto(0, 0)


## COLOR CONTROL

def calibrate_colors(filename='refcolors.txt'):
    """
    Calibrate the color sensor, starting in the white space
    in front of the yellow field on the calibration strip.
    """
    refcolors = []
    with open(filename, 'w') as f:

        def save_color(index, print_info=True):
            """
            Write current RGB value to the opened file f.
            """
            # Write to file
            print(csensor.value(0), csensor.value(1), csensor.value(2), file=f, flush=True)
            if print_info:  # Write to stdout
                print(COLORTABLE[index], csensor.value(0), csensor.value(1), csensor.value(2), flush=True)

            refcolors.append([csensor.value(0), csensor.value(1), csensor.value(2)])

        # White
        save_color(0)
        my(44)  # Move from white to first field in the color strip
        # Yellow
        save_color(1)
        # Colors betwen 2 (dark green) and 9 (orange)
        for i in range(8):
            mfield(-1, 0) # Go to next field
            save_color(i + 2)
    my(73/42 * RY)  # Move to first sudoku field

    return refcolors


def getrefcolors(filename='refcolors.txt'):
    """
    Read ordered reference color values from a file that was written in the calibration step (calibrate_colors()).
    """
    with open(filename) as rf:
        content = rf.read().splitlines()
        refcolors = []
        for line in content:
            if not line.strip() == '':
                refcolors.append([int(n) for n in line.split()])
    return refcolors


def minus(x, y):
    """
    Elementwise substraction of two lists of numbers (vectors).
    """
    c = []
    for a, b in zip(x, y):
        c.append(a - b)
    return c


def norm(x):
    """
    Compute euclidian norm of a list of numbers (vector)
    """
    return abs(sqrt(sum([a**2 for a in x])))


def dst(x, y):
    """
    Compute euclidian distance of two lists of numbers (vectors).
    """
    return norm(minus(x, y))


def nearest_neighbor(color, refcolors):
    """
    Classify RGB value as a color number using a reference color list (refcolors)
    and the k-nearest-neighbors algorithm (where k == 1).
    """
    color_distances = []
    for ref in refcolors:
        # Store reference color with its euclidian distance to the currently examined color
        color_distances.append([ref, dst(color, ref)])
    color_distances.sort(key=lambda x: x[1])  # Sort by distance -> First element is the nearest neighbor.
    return refcolors.index(color_distances[0][0])  # Return index (= number) of nearest color.


def getrgb():
    """
    Output currently measured raw RGB value in the form [red, green, blue].
    """
    return [csensor.value(0), csensor.value(1), csensor.value(2)]


def read_number():
    """
    Read color value and classify it using one of the reference colors by finding the nearest neighbor.
    """
    mcol = [csensor.value(0), csensor.value(1), csensor.value(2)]
    return nearest_neighbor(mcol, getrefcolors())


def getcolorname():
    return COLORTABLE[read_number()]


def scolw():
    ev3.Sound.speak(getcolorname()).wait()


## HIGH-LEVEL SUDOKU SOLVING ROUTINES

def scan_sudoku(n=9, print_output=True):
    """
    Scans the sudoku by moving to all fields, measuring their color values and classifying them as numbers.
    Returns a string representation of the sudoku.

    If n != 9, scanning will work in a smaller/larger square, but solving will be impossible of course.
    """
    clist = []
    clist2d = []
    for y in range(n):
        for x in range(n):
            # Reverse scan direction in every odd line to reduce unnecessary movements
            if y % 2 == 1:
                gfield(n - x - 1, y)
            else:
                gfield(x, y)
            current_number = read_number()
            clist.append(current_number)
            if print_output:
                print(current_number)
                print(getcolorname())

    for y in range(n):
        if y % 2 == 1:
            clist2d.append(clist[y*n:(y+1)*n][::-1])
        else:
            clist2d.append(clist[y*n:(y+1)*n])

    sudokustring = '\n'.join(' '.join([str(x) for x in l]) for l in clist2d)
    return sudokustring


def check_ref_puzzle_str(puzzle, ref_puzzle=REF_PUZZLE_STR):
    """
    Check if the read puzzle is the same as the saved reference puzzle.
    """
    correct = True
    puzzle_compact = str(puzzle).replace('-', '0').replace(' ', '')
    ref_puzzle_compact = str(ref_puzzle).replace('-', '0').replace(' ', '')
    for i in range(len(puzzle_compact)):
        if puzzle_compact[i] != ref_puzzle_compact[i]:
            print('Mismatch at row', i // 9, 'row', i % 9)
            print('Read', puzzle_compact[i], COLORTABLE[int(puzzle_compact[i])])
            print('Expected', ref_puzzle_compact[i], COLORTABLE[int(ref_puzzle_compact[i])])
            correct = False
    if correct:
        print('Everything OK.')
    return correct


def write_solution(puzzle=Sudoku(EXAMPLE_PUZZLE_STR), solution=Sudoku(EXAMPLE_SOLUTION_STR)):
    """
    Writes a solution down on the sheet of paper by making dots representing numbers.

    "puzzle" and "solution" are both either strings or solve.Sudoku objects (the latter ones are
    automatically converted to strings).

    The "puzzle" parameter has to be passed to show where the unknown numbers were.
    """
    # Create compact rows of the sudoku representation. Their elements are always castable to int.
    puzzle_rows = [row.replace('-', '0').replace(' ', '') for row in str(puzzle).splitlines()]
    solution_rows = [row.replace(' ', '') for row in str(solution).splitlines()]
    unknown_indices = [[i for i, j in enumerate(row) if int(j) == 0] for row in puzzle_rows]
    for y, x_values in enumerate(unknown_indices):
        for x in x_values:
            pen_gfield(x, y)
            write_number(int(solution_rows[y][x]))


# Shortcuts for interactive use
o = origin
x = mx
y = my

reset()  # This needs to stay here to initialize motors with speeds


if __name__ == '__main__':
    calibrate_colors()
    reset()
    puzzle_raw = scan_sudoku()
    puzzle = Sudoku(puzzle_raw)
    with open('sudoku.txt', 'w') as f:
        print(puzzle, file=f)

    solution = solve(puzzle)

    puzzle = str(puzzle)
    solution = str(solution)

    print(puzzle)
    print('\n Solution:\n')
    print(solution)
    if not check_ref_puzzle_str(puzzle):
        print('Sudoku could not be solved :(')
    else:
        write_solution(puzzle, solution)
    my(-500)  # push sheet out
