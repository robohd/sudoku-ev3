#!/usr/bin/env python3

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


# All possible valid entries of a solved sudoku
all_numbers = {1, 2, 3, 4, 5, 6, 7, 8, 9}

class Sudoku(list):
    """
    List subclass with a pretty Sudoku string representation.

    Constructor can either take an 81-character
    sudoku string or a list (or Sudoku object) of 81 values.
    """
    def __init__(self, content):
        list.__init__(self, [int(i) for i in content.split()]
                             if isinstance(content, str) else content)
    def __str__(self):
        return '\n'.join(' '.join(  # Join rows per newline and join numbers in them per space
            [(str(x) if x != 0 else '-') for x in self[row * 9 : (row + 1) * 9]])  # numbers in row
             for row in range(9))


def solve(sudoku):
    """
    Takes an unsolved Sudoku object (or equivalent list) and returns a
    valid solution to it as a new Sudoku object.

    This does not check the validity of the sudoku,
    so make sure it is actually solvable first.
    """

    #if len(sudoku) != 81:
        #print('Something went wrong. The sudoku should have 81 entries, not {}.'
              #.format(len(sudoku)), flush=True)
        #exit()

    try:
        u = sudoku.index(0)  # Find first unknown field
    except ValueError:
        # No zeros found -> Already solved. Return solution.
        return Sudoku(sudoku)

    # Will contain all numbers that cannot appear in this field due to sudoku rules.
    excluded = set()

    for j in range(81):
        in_column = (u - j) % 9 == 0
        in_row = u // 9 == j // 9
        in_block = (u // 27 == j // 27) and ((u % 9) // 3 == (j % 9) // 3)
        if in_column or in_row or in_block:
            excluded.add(sudoku[j])


    if excluded == all_numbers:  # -> No possible solution in this branch
        return None  # Discard this branch

    candidates = all_numbers - excluded

    for c in candidates:
        # Try every possible solution with the non-excluded numbers at index u.
        # If a wrong number is assumed in this step, the current recursion branch
        # eventually ends up returning None, but for every valid sudoku, at least
        # one branch leads to a correct solution.
        r = solve(sudoku[:u] + [c] + sudoku[u+1:])
        if r is not None:
            return r


def solve_file(filename='sudoku.txt'):
    with open(filename) as f:
        sudoku_str = f.read()
    result = solve(Sudoku(sudoku_str))
    return result


if __name__ == '__main__':

    # First test:

    problem1 = Sudoku("""
        5 3 0 0 7 0 0 0 0
        6 0 0 1 9 5 0 0 0
        0 9 8 0 0 0 0 6 0
        8 0 0 0 6 0 0 0 3
        4 0 0 8 0 3 0 0 1
        7 0 0 0 2 0 0 0 6
        0 6 0 0 0 0 2 8 0
        0 0 0 4 1 9 0 0 5
        0 0 0 0 8 0 0 7 9
        """)

    solution1 = Sudoku("""
        5 3 4 6 7 8 9 1 2
        6 7 2 1 9 5 3 4 8
        1 9 8 3 4 2 5 6 7
        8 5 9 7 6 1 4 2 3
        4 2 6 8 5 3 7 9 1
        7 1 3 9 2 4 8 5 6
        9 6 1 5 3 7 2 8 4
        2 8 7 4 1 9 6 3 5
        3 4 5 2 8 6 1 7 9
        """)

    result1 = Sudoku(solve(problem1))

    print('Puzzle 1:\n{}\n\nSolution 1:\n{}'.format(problem1, result1))

    assert(result1 == solution1)

    print('\n')

    # Second test:

    problem2 = Sudoku("""
        3 0 0 8 0 5 0 0 6
        0 0 4 0 0 0 1 0 0
        1 5 0 2 0 6 0 7 8
        0 0 0 1 5 9 0 0 0
        0 0 7 0 0 0 9 0 0
        0 0 0 6 3 7 0 0 0
        9 1 0 3 0 4 0 0 2
        0 0 6 0 0 0 8 0 0
        2 0 0 0 0 8 0 0 3""".strip())

    solution2 = Sudoku("""
        3 7 2 8 1 5 4 9 6
        6 8 4 7 9 3 1 2 5
        1 5 9 2 4 6 3 7 8
        4 2 3 1 5 9 6 8 7
        5 6 7 4 8 2 9 3 1
        8 9 1 6 3 7 2 5 4
        9 1 8 3 7 4 5 6 2
        7 3 6 5 2 1 8 4 9
        2 4 5 9 6 8 7 1 3""".strip())

    result2 = Sudoku(solve(problem2))

    print('Puzzle 2:\n{}\n\nSolution 2:\n{}'.format(problem2, result2))

    assert(result2 == solution2)
