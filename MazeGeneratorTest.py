from pygame.locals import *
import pygame, sys
import spritesheet
import random

DIRS = N, NE, E, SE, S, SW, W, NW = 0, 1, 2, 3, 4, 5, 6, 7

def GenerateMaze(initialPos = None):
    for row in grid:
        for tile in row:
            tile.walkable = False
    
    if initialPos != None:
        grid[initialPos[0]][initialPos[1]].walkable = True    
        walls = grid[initialPos[0]][initialPos[1]].getNeighbourWalls()    
    else:
        grid[0][0].walkable = True    
        walls = grid[0][0].getNeighbourWalls()

    while len(walls) > 0:
        currentWall = random.choice(walls)
        if currentWall.getNumberOfNotWalls() == 1:
            currentWall.walkable = True
            walls.extend(currentWall.getNeighbourWalls())
        
        walls.remove(currentWall)  

    if not grid[-1][-1].walkable: GenerateMaze((-1, -1))



def ScreenToGrid(x, y):
    return (x // nodeSize, max(y - gridRect.y, 0) // nodeSize)
    
def GridToScreen(x, y):
    return ((x + .5) * nodeSize, gridRect.y + (y + .5) * nodeSize)

isClickingGrid = False
draggingValue = False
def EventHandling():    
    global mouse, isClickingGrid, draggingValue
    mouse = pygame.mouse.get_pos()
    p = ScreenToGrid(mouse[0], mouse[1])

    for event in pygame.event.get():
        if event.type == QUIT:
            pygame.quit()
            sys.exit()
        if event.type == pygame.MOUSEBUTTONDOWN:
            GenerateMaze()
            return
            isClickingGrid = True
            draggingValue = not grid[p[0]][p[1]].walkable
        if event.type == pygame.MOUSEBUTTONUP:
            isClickingGrid = False

    if isClickingGrid:
        possibleWall = grid[p[0]][p[1]]
        possibleWall.walkable = draggingValue


def DrawTiles():
    screen.fill(gridBackgroundColor)

    for x in range(gridWidth):
        for y in range(gridHeight):
            rect = pygame.Rect(x * nodeSize, gridRect.y + y * nodeSize, nodeSize, nodeSize)
            pygame.draw.rect(screen, gridLinesColor, rect, 1)
            
            if not grid[x][y].walkable:
                grid[x][y].tileImage(rect)

class Node:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.walkable = True        

    def outOfBounds(self, x, y):
        return x < 0 or x >= gridWidth or y < 0 or y >= gridHeight    

    def getNeighbourWalls(self):
        vecinosParedes = []

        m = (-1, 0, 1)
        for x in m:
            for y in m:
                if (x, y) == (0, 0): continue
                i = x + self.x
                j = y + self.y
                if not self.outOfBounds(i, j):
                    tile = grid[i][j]
                    if not tile.walkable:
                        vecinosParedes.append(tile)
        
        return vecinosParedes

    def getNumberOfNotWalls(self):
        vecinosNoParedes = 0

        m = (-1, 0, 1)
        for x in m:
            for y in m:
                if (x, y) == (0, 0): continue
                i = x + self.x
                j = y + self.y
                if not self.outOfBounds(i, j):
                    if grid[i][j].walkable:
                        vecinosNoParedes += 1
        
        return vecinosNoParedes

    def setupVecinos(self):
        x = self.x
        y = self.y        

        self.vecinos = [edgeTile for d in DIRS]
        
        possibilities = ((N, 0, -1), (NE, 1, -1), (E, 1, 0), (SE, 1, 1), (S, 0, 1), (SW, -1, 1), (W, -1, 0), (NW, -1, -1))
        
        for pos in possibilities:
            i = x + pos[1]
            j = y + pos[2]
            if not self.outOfBounds(i, j):
                self.vecinos[pos[0]] = grid[i][j]
    

    def tileImage(self, rect):
        
        for i in range(0, 4):
            vecinosWalkable = [self.vecinos[(dir + i * 2) % 8].walkable for dir in DIRS]

            if not vecinosWalkable[N]: 
                screen.blit(variations[1][i], rect.topleft)
                if not vecinosWalkable[E]:
                    if not vecinosWalkable[NE]: screen.blit(variations[2][i], rect.topleft)
                    else: screen.blit(variations[3][i], rect.topleft)
        
        screen.blit(variations[0][0], rect.topleft)

if __name__ == "__main__":
    edgeTile = Node(-15, -15)
    edgeTile.walkable = False

    gridBackgroundColor = (179, 198, 255)
    gridLinesColor = (82, 86, 250)

    pygame.init()

    clock = pygame.time.Clock()
    size = width, height = 1350, 700
    screen = pygame.display.set_mode(size) 

    ss = spritesheet.spritesheet('spritesheet.png')

    images = ss.load_strip((1, 1, 16, 16), 4, 3, colorkey=(255, 255, 255))
    variations = [[img for x in range(4)] for img in images]

    for i in range(0, len(images)):
        images[i] = pygame.transform.scale(images[i], (32, 32))        
        images[i].convert()
        variations[i][0] = images[i]  

        if i is not 0:
            for j in range(1, 4): variations[i][j] = pygame.transform.rotate(images[i], (4 - j) * 90)  

    gridRect = Rect(0, 0, width, height)
    nodeSize = 32
    gridSize = gridWidth, gridHeight = gridRect.width // nodeSize, gridRect.height // nodeSize

    grid = [[Node(x, y) for y in range(gridHeight)] for x in range(gridWidth)]

    for rows in grid:
        for tile in rows:
            tile.setupVecinos()

    GenerateMaze()

    while True:
        EventHandling()

        DrawTiles()

        pygame.display.update()
        clock.tick(60)
