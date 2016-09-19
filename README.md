# sudoku-ev3
Sudoku solving robot built with Lego Mindstorms EV3 and ev3dev Python bindings

Using
* http://www.ev3dev.org/ (Debian 8 image)
* https://github.com/rhempel/ev3dev-lang-python (at commit def97386dc4123a4a668d6ebe35a3baf00980f71)
* Python 3.4 (Lower versions won't work).

To set up the main brick, ssh into it and run:

    $ sudo apt install python3-pip git # May take about an hour, be patient.
    $ git clone https://github.com/rhempel/ev3dev-lang-python
    $ cd ev3dev-lang-python
    $ git checkout def97386dc4123a4a668d6ebe35a3baf00980f71 # Newer commits may work, but are untested
    $ python3 -m pip install .
    $ python3 -m pip install ipython==4.2.1 # newer version are way too slow
    $ cd ..
    $ git clone https://github.com/robohd/sudoku-ev3
    $ cd sudoku-ev3

Then you should be ready to run the code in this repo. You can use
ipython3 to test the individual subroutines and move the robot to its
initial position:  
Color sensor directly in front of the leftmost (yellow) calibration field,
about 160 (control.OFF_X + 10) degrees to the right of the left cage border,
pen about 4mm above the paper.

After positioning the robot and making sure everything is aligned correctly,
you can just run the file control.py in this repo and the robot should begin
reading, solving and writing the sudoku fully automatically.
