# region Setup

from collections import namedtuple
from numpy import Infinity
from pygame.locals import *
import sys, pygame, random
import spritesheet

DIRS = N, NE, E, SE, S, SW, W, NW = 0, 1, 2, 3, 4, 5, 6, 7

pygame.init()

WHITE = (255, 255, 255)
RED = (255, 0, 0)

hoverButtonColor = (255, 126, 5)
normalButtonColor = (224, 67, 0)
panelColor = (82, 86, 250)
textColor = (82, 86, 250)

gridBackgroundColor = (179, 198, 255)
gridLinesColor = (82, 86, 250)

normalStartColor = (250, 30, 100)
hoverStartColor = (255, 87, 171)

normalGoalColor = (143, 23, 255)
hoverGoalColor = (151, 87, 255)

position = namedtuple('position', ['x', 'y'])
currentPath = []

isDijkistra = False

# endregion

fastGeneration = False
def GenerateMaze(carveMaze = None):
    x = 0
    y = 0

    if carveMaze is None:
        carveMaze = False

        x = startDragable.node.pos[0]
        y = startDragable.node.pos[1] 
               
        for row in grid:
            for tile in row:
                tile.walkable = False
    else:
        carveMaze = True

        x = goalDragable.node.pos[0]
        y = goalDragable.node.pos[1] 

    grid[x][y].walkable = True
    walls = grid[x][y].getNeighbourWalls()   

    while len(walls) > 0:
        randomIndex = random.randint(0, len(walls) - 1)
        currentWall = walls[randomIndex]
        nWalls = currentWall.getNumberOfNotWalls()
        if nWalls == 1 or (carveMaze and nWalls <= 3):
            currentWall.walkable = True
            walls.extend(currentWall.getNeighbourWalls())
            if not fastGeneration:
                for event in pygame.event.get():
                    if event.type == QUIT:
                        pygame.quit()
                        sys.exit()

                DrawUI()
                DrawGrid(evaluatedTile= currentWall)         

                pygame.display.update()
                clock.tick(60)
        
        del walls[randomIndex]   

    for row in grid:
        for tile in row:
            if tile.getNumberOfNotWalls() == 0 and not tile.walkable:
                walls.append(tile)

    if not grid[goalDragable.node.pos[0]][goalDragable.node.pos[1]].walkable:
        GenerateMaze(carveMaze= True)

# region Pathfinding
def InScreenRange(value, minimum, maximum):
    return min(max(value - minimum, 0), maximum - nodeSize / 2)

def ScreenToGrid(screenPosition):
    return (int(InScreenRange(screenPosition.x, gridRect.x, gridRect.width) // nodeSize), int(InScreenRange(screenPosition.y, gridRect.y, gridRect.height) // nodeSize))

def GridToScreen(gridPosition):
    return ((gridPosition.x + .5) * nodeSize, gridRect.y + (gridPosition.y + .5) * nodeSize)

def InitPathFinding():
    ResetAllNodes()
    if not AStar(startDragable.node, goalDragable.node, isDijkistra):
        global currentPath
        currentPath = []
    FindPath(goalDragable.node)

def Distance(a, b):
    dx = abs(a.x - b.x)
    dy = abs(a.y - b.y)
    m = min(dx, dy)
    d = 14 * m + 10 * (max(dx, dy) - m)
    return d

def ResetWallsAndPath():
    global currentPath, grid
    currentPath = []
    for y in grid:
        for x in y:
            x.reset()
            x.walkable = True

def ResetAllNodes():
    global grid
    for y in grid:
        for x in y: x.reset()

def FindPath(goal):
    global currentPath
    goal.partOfPath = True
    if goal.parent is not None:
        currentPath = FindPath(goal.parent) + [goal]
        return currentPath
    else:
        return [goal]

def AStar(start, goal, dijkstra = None):
    if dijkstra is None: dijkstra = False
    global currentPath

    start.g = 0
    start.calculateH(goal, dijkstra)
    start.calculateF()

    openSet = [start]
    closedSet = []

    while openSet:

        current = openSet[0]
        for node in openSet:
            if node.f < current.f: current = node

        if current is goal:
            return True

        openSet.remove(current)
        closedSet.append(current)
        for v in current.calculateVecinos():
            if not v.walkable or closedSet.__contains__(v):
                continue

            tentativeGScore = current.g + Distance(current.pos, v.pos)
            if tentativeGScore < v.g:
                v.parent = current
                v.g = tentativeGScore
                v.calculateH(goal, dijkstra)
                v.calculateF()
                if not openSet.__contains__(v):
                    openSet.append(v)
        
        for event in pygame.event.get():
            if event.type == QUIT:
                pygame.quit()
                sys.exit()
        FindPath(current)
        DrawUI()
        DrawGrid(openSet, closedSet)
        for n in currentPath: n.partOfPath = False 

        pygame.display.update()
        clock.tick(60)

    return False
# endregion

# region Node
class Node:
    def __init__(self, pos):
        self.pos = pos
        self.walkable = True
        self.reset()

    def reset(self):
        self.parent = None
        self.vecinos = None
        self.g = Infinity
        self.f = Infinity
        self.partOfPath = False

    def calculateF(self):
        self.f = self.h + self.g
        return self.f

    def calculateH(self, goal, dijkistra):
        if dijkistra: self.h = 0
        else: self.h = Distance(self.pos, goal.pos)
        return self.h

    def calculateVecinos(self):
        if self.vecinos is None:
            self.vecinos = []
            for y in range(self.pos.y - 1, self.pos.y + 2):
                if y >= 0 and y < gridHeight:
                    for x in range(self.pos.x - 1, self.pos.x + 2):
                        if x >= 0 and x < gridWidth:
                            v = grid[x][y]
                            if v is not self:
                                self.vecinos.append(grid[x][y])               

        return self.vecinos
    
    def outOfBounds(self, x, y):
        return x < 0 or x >= gridWidth or y < 0 or y >= gridHeight    

    def setupVecinos(self):
        x = self.pos[0]
        y = self.pos[1]        

        self.graphicVecinos = [edgeTile for d in DIRS]
        
        possibilities = ((N, 0, -1), (NE, 1, -1), (E, 1, 0), (SE, 1, 1), (S, 0, 1), (SW, -1, 1), (W, -1, 0), (NW, -1, -1))
        
        for pos in possibilities:
            i = x + pos[1]
            j = y + pos[2]
            if not self.outOfBounds(i, j):
                self.graphicVecinos[pos[0]] = grid[i][j]
    
    def tileImage(self, rect):
        
        for i in range(0, 4):
            vecinosWalkable = [self.graphicVecinos[(dir + i * 2) % 8].walkable for dir in DIRS]

            if not vecinosWalkable[N]: 
                screen.blit(variations[1][i], rect.topleft)
                if not vecinosWalkable[E]:
                    if not vecinosWalkable[NE]: screen.blit(variations[2][i], rect.topleft)
                    else: screen.blit(variations[3][i], rect.topleft)
        
        screen.blit(variations[0][0], rect.topleft)
    
    def getNeighbourWalls(self):
        vecinosParedes = []

        m = (-1, 0, 1)
        for x in m:
            for y in m:
                if (x, y) == (0, 0): continue
                i = x + self.pos[0]
                j = y + self.pos[1]
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
                i = x + self.pos[0]
                j = y + self.pos[1]
                if not self.outOfBounds(i, j):
                    if grid[i][j].walkable:
                        vecinosNoParedes += 1
        
        return vecinosNoParedes


# endregion

# region Button
class Button():
    def __init__(self, rect, text, onClick):
        self.rect = rect
        self.text = text
        self.onClick = onClick

    def InBounds(self):
        return (self.rect.left <= mouse[0] <= self.rect.right and self.rect.top <= mouse[1] <= self.rect.bottom)

    def Draw(self):
        textRect = self.text.get_rect()
        c = normalButtonColor
        if self.InBounds():
            c = hoverButtonColor
        
        pygame.draw.rect(screen, c, self.rect)
        screen.blit(self.text, (self.rect.center[0] - textRect.width / 2, self.rect.center[1] - textRect.height / 2))

class ToggableButton(Button):
    def __init__(self, rect, text, trueText):        
        self.falseText = text
        self.trueText = trueText
        self.toggled = False
        super().__init__(rect, text, None)
    
    def Toggle(self):
        global isDijkistra

        self.toggled = not self.toggled
        if self.toggled: self.text = self.trueText
        else: self.text = self.falseText
        isDijkistra = self.toggled
        

# endregion

# region Dragable

class Dragable():
    def __init__(self, radius, normalColor, hoverColor, node):
        self.radius = radius
        self.normalColor = normalColor
        self.hoverColor = hoverColor
        self.node = node
        self.moving = False
    
    def InBounds(self, pos):
        screenPos = GridToScreen(self.node.pos)
        return (screenPos[0] - nodeSize / 2 <= pos[0] <= screenPos[0] + nodeSize / 2 and screenPos[1] - nodeSize / 2 <= pos[1] <= screenPos[1] + nodeSize / 2)

    def Draw(self):
        c = self.normalColor
        if self.InBounds(mouse) or self.moving:
            c = self.hoverColor
        
        pygame.draw.circle(screen, c, GridToScreen(self.node.pos), self.radius)

    def Move(self):
        pos = ScreenToGrid(position(mouse[0], mouse[1]))
        to = grid[pos[0]][pos[1]]
        if to.walkable and goalDragable.node != to != startDragable.node:
            self.node = to

# endregion

# region Draw and Event Handling
def DrawGrid(openSet = None, closedSet = None, evaluatedTile = None):
    findingPath = False
    if closedSet is not openSet is not None:
        findingPath = True

    pygame.draw.rect(screen, gridBackgroundColor, gridRect)

    if len(currentPath) > 1: pygame.draw.lines(screen, gridLinesColor, False, [GridToScreen(n.pos) for n in currentPath], 15)
    for x in range(gridWidth):
        for y in range(gridHeight):
            rect = pygame.Rect(x * nodeSize, gridRect.y + y * nodeSize, nodeSize, nodeSize)
            pygame.draw.rect(screen, gridLinesColor, rect, 1)
            current = grid[x][y]
            currentPos = (x, y)

            if current.partOfPath:
                pygame.draw.circle(screen, gridLinesColor, GridToScreen(position(currentPos[0], currentPos[1])), 10)
            if currentPos == startDragable.node.pos:
                startDragable.Draw()
            if currentPos == goalDragable.node.pos:
                goalDragable.Draw()
            if not current.walkable:
               current.tileImage(rect)
    
    if evaluatedTile is not None:
        s = pygame.Surface((nodeSize, nodeSize), pygame.SRCALPHA)
        s.fill((255, 0, 0, 128))
        p = GridToScreen(evaluatedTile.pos)
        screen.blit(s, (p[0] - nodeSize / 2, p[1] - nodeSize / 2))

    if findingPath:
        for node in closedSet:
            s = pygame.Surface((nodeSize, nodeSize), pygame.SRCALPHA)
            s.fill((255, 0, 0, 128))
            p = GridToScreen(node.pos)
            screen.blit(s, (p[0] - nodeSize / 2, p[1] - nodeSize / 2))
        for node in openSet:
            s = pygame.Surface((nodeSize, nodeSize), pygame.SRCALPHA)
            s.fill((0, 255, 0, 128))
            p = GridToScreen(node.pos)
            screen.blit(s, (p[0] - nodeSize / 2, p[1] - nodeSize / 2))

def DrawUI():
    pygame.draw.rect(screen, panelColor, Rect((0, 0), (width, 150)))

    startButton.Draw()
    resetButton.Draw()
    generateMazeButton.Draw()
    typeOfPFTButton.Draw()

isClickingGrid = False
draggingValue = False
def EventHandling():    
    global mouse, isClickingGrid, draggingValue
    mouse = pygame.mouse.get_pos()

    for event in pygame.event.get():
        if event.type == QUIT:
            pygame.quit()
            sys.exit()
        if event.type == pygame.MOUSEBUTTONDOWN:
            if startButton.InBounds():
                startButton.onClick()
            elif resetButton.InBounds():
                resetButton.onClick()
            elif generateMazeButton.InBounds():
                generateMazeButton.onClick()
            elif typeOfPFTButton.InBounds():
                typeOfPFTButton.Toggle()
            elif startDragable.InBounds(mouse):
                startDragable.moving = True
            elif goalDragable.InBounds(mouse):
                goalDragable.moving = True
            else:
                isClickingGrid = True
                p = ScreenToGrid(position(mouse[0], mouse[1]))
                possibleWall = grid[p[0]][p[1]]
                draggingValue = not possibleWall.walkable                  
        if event.type == pygame.MOUSEBUTTONUP:
            isClickingGrid = False
            if startDragable.moving:
                startDragable.moving = False
            if goalDragable.moving:
                goalDragable.moving = False
    
    if isClickingGrid:
        p = ScreenToGrid(position(mouse[0], mouse[1]))
        sp = GridToScreen(position(p[0], p[1]))
        if not startDragable.InBounds(sp) and not goalDragable.InBounds(sp):
            possibleWall = grid[p[0]][p[1]]
            possibleWall.walkable = draggingValue 
    
    if startDragable.moving:
        startDragable.Move()
    if goalDragable.moving:
        goalDragable.Move()
# endregion

if __name__ == "__main__":

    edgeTile = Node((-15, -15))
    edgeTile.walkable = False

    clock = pygame.time.Clock()
    size = width, height = 1350, 700

    gridRect = Rect(0, 150, width, height - 150)
    nodeSize = 32
    gridSize = gridWidth, gridHeight = gridRect.width // nodeSize, gridRect.height // nodeSize
    grid = [[Node(position(x, y)) for y in range(gridHeight)] for x in range(gridWidth)]

    startDragable = Dragable(nodeSize / 3, normalStartColor, hoverStartColor, grid[0][0])
    goalDragable = Dragable(nodeSize / 3, normalGoalColor, hoverGoalColor, grid[gridWidth - 1][gridHeight - 1])

    goalRect = Rect(100, 100, nodeSize, nodeSize)

    textFont = pygame.font.SysFont('myriadprosemibolditopentype',20)
    
    startButton = Button(Rect((50, 50), (200, 50)), textFont.render('Start Pathfinding', True, textColor), InitPathFinding)
    resetButton = Button(Rect((300, 50), (100, 50)), textFont.render('Reset', True, textColor), ResetWallsAndPath)
    generateMazeButton = Button(Rect((450, 50), (200, 50)), textFont.render('Generate Maze', True, textColor), GenerateMaze)
    typeOfPFTButton = ToggableButton(Rect((700, 50), (100, 50)), textFont.render('A Star', True, textColor), textFont.render('Dijkstra', True, textColor))

    screen = pygame.display.set_mode(size)  
    
    ss = spritesheet.spritesheet('spritesheet.png')

    images = ss.load_strip((1, 1, 16, 16), 4, 3, colorkey=(255, 255, 255))
    variations = [[img for x in range(4)] for img in images]

    for i in range(0, len(images)):
        images[i] = pygame.transform.scale(images[i], (nodeSize, nodeSize))        
        images[i].convert()
        variations[i][0] = images[i]  

        if i is not 0:
            for j in range(1, 4): variations[i][j] = pygame.transform.rotate(images[i], (4 - j) * 90)    

    for rows in grid:
        for tile in rows:
            tile.setupVecinos()

    while True:
        EventHandling()

        DrawUI()
        DrawGrid()

        pygame.display.update()
        clock.tick(60)