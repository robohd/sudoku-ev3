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

from solve import Sudoku, solve, solve_file


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

CGX_CORR = 0
CDOWN_CORR = 1

# Distance between pen points in numbers
PX = RX / 5
PY = RY / 4

PEN_IDLE_POS = 0
PEN_WRITE_POS = 6

MWT = 0.1  # Motor wait time (check interval for check if a motor is running)
PEN_DOT_TIME = 0.1  # Time that is spent with pen being down (more time -> bigger dot for marker)

# Map color numbers to color namese
COLTABLE = {
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

## Example of a Sudoku with its solution

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
    Reset eveRY motor to its initial configuration. This does not move anything.
    """
    a.reset()
    b.reset()
    c.reset()
    a.position = 0
    b.position = 0
    #c.position = 0
    a.speed_sp = SPEED_Y
    b.speed_sp = SPEED_X
    c.speed_sp = SPEED_C
    a.stop_action = 'brake'
    b.stop_action = 'brake'
    c.stop_action = 'brake'


def is_moving(check_stall=False):
    motor_states = a.state + b.state + c.state
    if check_stall and 'stalled' in motor_states:
        print('\nWarning: At least one motor is stalled. Check speed_sp attributes. States:')
        print('A:', a.state)
        print('B:', b.state)
        print('C:', c.state)
    return 'running' in motor_states

def cdown():
    """
    Move pen down to writing position.
    """
    xmod = round(CDOWN_CORR * b.position / (RX*9))
    c.run_to_abs_pos(position_sp=PEN_WRITE_POS+xmod)
    sleep(MWT)
    while is_moving():
        sleep(MWT)

def cup():
    """
    Move pen up to neutral position.
    """
    c.run_to_abs_pos(position_sp=PEN_IDLE_POS)
    sleep(MWT)
    while is_moving():
        sleep(MWT)

def cdot():
    """
    Make a dot with the pen at the current position.
    """
    cdown()
    sleep(PEN_DOT_TIME)
    cup()


# HOW TO WRITE NUMBERS ON PAPER

def one():
    cdot()

def two():
    cdot()
    mx(-PX)
    cdot()
    mx(PX)

def three():
    cdot()
    mx(-PX)
    cdot()
    mx(-PX)
    cdot()
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
    """ move n fields """
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
    """ move to field (nx, ny) """
    fy = ny*RY
    fx = nx*RX
    if fy != a.position:
        a.run_to_abs_pos(position_sp=fy)
    if fx != b.position:
        b.run_to_abs_pos(position_sp=fx)
    sleep(MWT)
    while is_moving():
        sleep(MWT)


def cgfield(nx=0, ny=0, off_x=OFF_X, off_y=OFF_Y):
    xmod = -round(CGX_CORR * b.position/(RX*9))
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
    fy = y
    fx = x
    if y != a.position:
        a.run_to_abs_pos(position_sp=y)
    if x != b.position:
        b.run_to_abs_pos(position_sp=x)
    sleep(MWT)
    while is_moving():
        sleep(MWT)

#def gx(x=0):
    #goto(x=x)

#def gy(y=0):
    #goto(y=y)

def origin():
    goto(0, 0)


## COLOR CONTROL

def calibcols(filename='refcolors.txt'):
    """
    Calibrate the color sensor, starting in the white space
    in front of the yellow field on the calibration strip.
    """
    refcols = []
    with open(filename, 'w') as f:

        def save_color(index, print_info=True):
            """
            Write current RGB value to the opened file f.
            """
            # Write to file
            print(csensor.value(0), csensor.value(1), csensor.value(2), file=f, flush=True)
            if print_info:  # Write to stdout
                print(COLTABLE[index], csensor.value(0), csensor.value(1), csensor.value(2), flush=True)

            refcols.append([csensor.value(0), csensor.value(1), csensor.value(2)])

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

    return refcols


def getrefcols(filename='refcolors.txt'):
    with open(filename) as rf:
        content = rf.read().splitlines()
        #print(content)
        refcols = []
        for line in content:
            if not line.strip() == '':
                refcols.append([int(n) for n in line.split()])
    return refcols


def minus(x, y):
    c = []
    for a, b in zip(x, y):
        c.append(a - b)
    return c

def norm(x):
    return abs(sqrt(sum([a**2 for a in x])))

def dst(x,y):
    return norm(minus(x, y))

def knn(x, refs, verbose=False, ultraverbose=False):
    """
    Classify RGB value as a color number using a color table (refs)
    and the k-nearest-neighbors algorithm (where k == 1 here)
    """
    dl = []
    for ref in refs:
        dl.append([ref, dst(x,ref)])
    dl.sort(key=lambda x: x[1])
    if ultraverbose:
        return refs.index(dl[0][0]), dl
    if verbose:
        return refs.index(dl[0][0]), dl[0]
    return refs.index(dl[0][0])


def getrgb():
    return [csensor.value(0), csensor.value(1), csensor.value(2)]

def getcol():
    mcol = [csensor.value(0), csensor.value(1), csensor.value(2)]
    return knn(mcol, getrefcols())

def getcolname():
    return COLTABLE[getcol()]

def printcolname():
    print(getcolname)

def printcolor():
    c = getcol()
    print(c, COLTABLE[c])


def getnumber():
    return getcol()

def col():
    return getcolname()

def scol():
    ev3.Sound.speak(getcolname())

def scolw():
    ev3.Sound.speak(getcolname()).wait()

def pcol():
    print(col())


## HIGH-LEVEL SUDOKU SOLVING ROUTINES

def scan_sudoku(n=9):
    clist = []
    clist2d = []
    #current_color = col()
    #clist.append(current_color)
    #print(current_color)
    for y in range(n):
        for x in range(n):
            if y % 2 == 1:
                gfield(n - x - 1, y)
            else:
                gfield(x, y)
            current_number = getnumber()
            clist.append(current_number)
            print(current_number)
            #scolw()
            pcol()

    for y in range(n):
        if y % 2 == 1:
            clist2d.append(clist[y*n:(y+1)*n][::-1])
        else:
            clist2d.append(clist[y*n:(y+1)*n])
        #print(clist[i*n:(i+1)*n])

    #print(clist)
    #return clist

    #print(clist2d)
    sudokustring = '\n'.join(' '.join([str(x) for x in l]) for l in clist2d)
    return sudokustring


def check_ref_puzzle_str(puzzle, ref_puzzle=REF_PUZZLE_STR):
    correct = True
    puzzle_compact = str(puzzle).replace('-', '0').replace(' ', '')
    ref_puzzle_compact = str(ref_puzzle).replace('-', '0').replace(' ', '')
    for i in range(len(puzzle_compact)):
        if puzzle_compact[i] != ref_puzzle_compact[i]:
            print('Mismatch at row', i // 9, 'row', i % 9)
            print('Read', puzzle_compact[i], COLTABLE[int(puzzle_compact[i])])
            print('Expected', ref_puzzle_compact[i], COLTABLE[int(ref_puzzle_compact[i])])
            correct = False
    if correct:
        print('Everything OK.')
    return correct

def write_solution(puzzle=Sudoku(EXAMPLE_PUZZLE_STR), solution=Sudoku(EXAMPLE_SOLUTION_STR)):
    # Create compact rows of the sudoku representation. Their elements are always castable to int.
    puzzle_rows = [row.replace('-', '0').replace(' ', '') for row in str(puzzle).splitlines()]
    solution_rows = [row.replace(' ', '') for row in str(solution).splitlines()]
    unknown_indices = [[i for i, j in enumerate(row) if int(j) == 0] for row in puzzle_rows]
    for y, x_values in enumerate(unknown_indices):
        for x in x_values:
            cgfield(x, y)
            write_number(int(solution_rows[y][x]))


# Shortcuts for interactive use
o = origin
x = mx
y = my

reset()  # This needs to stay here to initialize motors with speeds


if __name__ == '__main__':
    calibcols()
    reset()
    puzzle_raw = scan_sudoku()
    puzzle = Sudoku(puzzle_raw)
    with open('sudoku.txt', 'w') as f:
        print(puzzle, file=f)

    #input('Sudoku saved. Press Enter to continue with solving...')
    #puzzle, result = solve_file('sudoku.txt')

    #solution_raw = solve_file('sudoku.txt')
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
    my(-500) # push out
    ev3.Sound.speak('eeeeeeeeeeeeeeeeeeeeeeeeeee').wait()
