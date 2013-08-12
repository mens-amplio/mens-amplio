import termios, sys, os
TERMIOS = termios
def getkey():
    fd = sys.stdin.fileno()
    old = termios.tcgetattr(fd)
    new = termios.tcgetattr(fd)
    new[3] = new[3] & ~TERMIOS.ICANON & ~TERMIOS.ECHO
    new[6][TERMIOS.VMIN] = 1
    new[6][TERMIOS.VTIME] = 0
    termios.tcsetattr(fd, TERMIOS.TCSANOW, new)
    c = None
    try:
        c = os.read(fd, 3)
    finally:
        termios.tcsetattr(fd, TERMIOS.TCSAFLUSH, old)
    return c

if __name__ == '__main__':
    print "press Q to exit, arrowkeys to adjust"
    attend = 50
    try:
        for line in open('attend', 'r'):
            attend = int(line)
    except IOError:
        pass

    meditate = 50
    try:
        for line in open('meditate', 'r'):
            meditate = int(line)
    except IOError:
        pass
    while 1:
        print("a:" + str( attend ) + " " + "m:" + str( meditate ) )
        c = getkey()
        if c == 'q':
            break
        if ord(c[0]) == 27:
            if c[2] == 'A':
                attend += 1
            if c[2] == 'C':
                meditate += 1
            if c[2] == 'B':
                attend -= 1
            if c[2] == 'D':
                meditate -= 1
        if attend < 0:
            attend = 0
        if attend > 100:
            attend = 100
        if meditate < 0:
            meditate = 0
        if meditate > 100:
            meditate = 100
        
        open('attend','w').write(str(attend))
        open('meditate','w').write(str(meditate))
