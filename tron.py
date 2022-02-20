"""
Programme du tron
Lejdar, Lukáš, G1
"""
from asyncio import FastChildWatcher
from re import A
import pygame
import random as rand
import copy
import time

WIDTH=256
HEIGHT=256
RED=(255,0,0)
GREEN=(0,255,0)
BLUE=(0,0,255)
NECO=(255,0,255)
GREY=(200,200,200)
WHITE=(255,255,255)

PLAYERCOLORS = [GREEN, BLUE, RED, NECO]

COLOR_INACTIVE = (150,150,150)
COLOR_ACTIVE = (255,255,255)

BORDER_WIDTH = 10
OBSTACLE_SIZE = 16

WAITBEFOREGAME = 88

class SelectableText:
    def __init__(self, x, y, font, text, index, activeColor):
        
        self.activeColor = activeColor
        self.index = index
        self.text = text
        self.font = font

        self.setAsInactive()
        self.x = x - self.txt_surface.get_width()/2
        self.y = y - self.txt_surface.get_height()/2

    def switch(self):
        if self.active:
            self.setAsInactive()
        else:
            self.setAsActive()

    def setAsActive(self):
        self.active = True
        self.color = self.activeColor
        self.renderText()

    def setAsInactive(self):
        self.active = False
        self.color = COLOR_INACTIVE
        self.renderText()
    
    def renderText(self):
        self.txt_surface = self.font.render(self.text, True, self.color)

    def draw(self, surface):
        surface.blit(self.txt_surface, (self.x, self.y))

class CenteredInputBox:

    def __init__(self, w, h, font, color, text=''):
        
        self.text = text
        self.font = font
        self.preferedWidth = w
        self.preferedHeight = h  
        self.active = True
        self.color = color
        self.done = False
        self.txt_surface = font.render(text, True, self.color)

        height = max(h, self.txt_surface.get_height()+20)
        self.rect = pygame.Rect(WIDTH/2 - w/2, HEIGHT/2 - height/2, w, height)

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            # If the user clicked on the input_box rect.
            if self.rect.collidepoint(event.pos):
                # Toggle the active variable.
                self.active = not self.active
            else:
                self.active = False
            # Change the current color of the input box.
            self.color = COLOR_ACTIVE if self.active else COLOR_INACTIVE
        if event.type == pygame.KEYDOWN:
            if self.active:
                if event.key == pygame.K_RETURN:
                    self.text = ''
                elif event.key == pygame.K_BACKSPACE:
                    self.text = self.text[:-1]
                else:
                    self.text += event.unicode.upper()
                    if len(self.text) >= 5:
                        self.done = True

                # Re-render the text.
                self.txt_surface = self.font.render(self.text.upper(), True, self.color)

    def update(self):
        # Resize the box if the text is too long.
        width = max(self.preferedWidth, self.txt_surface.get_width()+20)
        self.rect.x = WIDTH/2 - width/2
        self.rect.w = width

    def draw(self, surface):
        # Blit the text.
        heightMargin = self.rect.y + (self.rect.h-self.txt_surface.get_height())/2
        surface.blit(self.txt_surface, (self.rect.x+10, heightMargin))
        pygame.draw.rect(surface, self.color, self.rect, 2)

class Player:
    def __init__(self, name, color):
        self.color = color
        self.name = name
        self.wonGames = []

class Vector:
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def addVec(self, vec):
        self.x += vec.x
        self.y += vec.y

class Tron():

    def __init__(self, vector, player):
        self.position = vector
        self.player = player
        self.isDead = False

        self.up = Vector(0,-1)
        self.down = Vector(0,1)
        self.left = Vector(-1,0)
        self.right = Vector(1,0)

        self.movementVec = self.up
    
    def compareVecs(self, vec1, vec2):
        return vec1.x == vec2.x and vec1.y == vec2.y

    def moveUp(self):
        if not self.compareVecs(self.movementVec, self.down):
            self.movementVec = self.up

    def moveDown(self):
        if not self.compareVecs(self.movementVec, self.up):
            self.movementVec = self.down

    def moveLeft(self):
        if not self.compareVecs(self.movementVec, self.right):
            self.movementVec = self.left

    def moveRight(self):
        if not self.compareVecs(self.movementVec, self.left):
            self.movementVec = self.right

    def updatePosition(self):
        
        if self.isDead: 
            return

        self.position.addVec(self.movementVec)

def calculateScore(start, end):
    return end - start

def averageScore(scores):
    total = 0
    for score in scores:
        total += score

    return int(total/len(scores))

def tronCollision(tronPosition, surface):
    if tronPosition.position.x >= WIDTH or tronPosition.position.x <= 0 :
        return True
    if tronPosition.position.y >= HEIGHT or tronPosition.position.y <= 0:
        return True

    if surface.get_at([int(tronPosition.position.x), int(tronPosition.position.y)]) != (0,0,0,255): 
        # if the pixel where the tron is about to go to is already colored -> dies
        # must be called before new tron position is colored

        return True

    return False

def isSquareInRange(vecList, x, y, obstacleSize):
    TOPLEFTMARGIN = obstacleSize*2
    for vec in vecList:
        if vec.x - TOPLEFTMARGIN < x and x < vec.x + obstacleSize:
            if vec.y - TOPLEFTMARGIN < y and y < vec.y + obstacleSize:
                return True

    return False

def isCircleInRange(vecList, x, y, obstacleSize):
    MARGIN = obstacleSize*1.5

    for vec in vecList:
        if vec.x - MARGIN < x and x < vec.x + MARGIN:
            if vec.y - MARGIN < y and y < vec.y + MARGIN:
                return True

    return False
    
def drawBackround(surface, vecList):
    surface.fill((0,0,0))
    pygame.draw.rect(surface, GREY, [1, 1, WIDTH-1, HEIGHT-1],1)

    SQUARE_LEFT_BOUNDARY = BORDER_WIDTH
    SQUARE_RIGHT_BOUNDARY = WIDTH - OBSTACLE_SIZE - BORDER_WIDTH
    SQUARE_TOP_BOUNDARY = BORDER_WIDTH
    SQUARE_BOTTOM_BOUNDARY = HEIGHT - OBSTACLE_SIZE -  BORDER_WIDTH


    for i in range(10):
        x = 0
        y = 0

        while True:
            x = rand.randint(SQUARE_LEFT_BOUNDARY, SQUARE_RIGHT_BOUNDARY) 
            y = rand.randint(SQUARE_TOP_BOUNDARY, SQUARE_BOTTOM_BOUNDARY)

            if isSquareInRange(vecList, x, y, OBSTACLE_SIZE) == False:
                break

        pygame.draw.rect(surface, GREY, pygame.Rect(x, y, OBSTACLE_SIZE, OBSTACLE_SIZE), 10)
    
    
    CIRCLE_RADIUS = OBSTACLE_SIZE/2
    CIRCLE_LEFT_BOUNDARY = CIRCLE_RADIUS + BORDER_WIDTH
    CIRCLE_RIGHT_BOUNDARY = WIDTH - CIRCLE_LEFT_BOUNDARY
    CIRCLE_TOP_BOUNDARY = CIRCLE_RADIUS + BORDER_WIDTH
    CIRCLE_BOTTOM_BOUNDARY = HEIGHT - CIRCLE_TOP_BOUNDARY

    for i in range(10):
        
        while True:
            x = rand.randint(CIRCLE_LEFT_BOUNDARY, CIRCLE_RIGHT_BOUNDARY) 
            y = rand.randint(CIRCLE_TOP_BOUNDARY, CIRCLE_BOTTOM_BOUNDARY)

            if isCircleInRange(vecList, x, y, OBSTACLE_SIZE) == False:
                break

        pygame.draw.circle(surface, GREY, [x + CIRCLE_RADIUS, y + CIRCLE_RADIUS], CIRCLE_RADIUS)

def drawTron(surface, tron):
    if tron.isDead == False:
        surface.set_at((int(tron.position.x), int(tron.position.y)), tron.player.color)

def updateTron(tron, surface):
        tron.updatePosition()
        if tronCollision(tron, surface):
            tron.isDead = True

class AppState:
    def __init__(self, surface, players, elapsedTIme):
        self.surface = surface
        self.elapsedTime = elapsedTIme
        self.players = players
        
    def screenLoopFunc(self, appstate, events, elapsedTime):
        appstate.elapsedTime = elapsedTime
        self.nextScreenLoopFunc(appstate, events)

    def nextScreenLoopFunc(self, appstate, events):
        return
    
    def setScreenAsScoreScreen(self, scoreScreen):
        self.nextScreenLoopFunc = scoreScreen.loopFunc 

    def setScreenAsSelctPlayers(self, selectPlayersScreen):
        self.nextScreenLoopFunc = selectPlayersScreen.loopFunc

    def setScreenAsAskForPlayerName(self, askForPlayerNameScreen):
        self.nextScreenLoopFunc = askForPlayerNameScreen.loopFunc
    
    def setScreenAsGame(self, gameState):
        def gameStateLoopFunc(appState, events):
            gameState.loopFunc(appState, gameState, events)

        self.nextScreenLoopFunc = gameStateLoopFunc
    
class ScoreScreen:
        
    def handle_event(self, event, appState):
        if event.type == pygame.KEYDOWN:  
            if event.key == pygame.K_RETURN: 
                appState.setScreenAsSelctPlayers(SelectPlayersScreen(appState))

    def update(self):
        return

    def initialDraw(self, surface):
        surface.fill((30, 30, 30))
        surface.blit(self.score_surface, (WIDTH/2-self.score_surface.get_width()/2, 80))

        if len(self.gamesList) == 0:
            surface.blit(self.noGames_surface, (WIDTH/2-self.noGames_surface.get_width()/2, 130))
        else:
            i = 0
            for (player, score) in self.gamesList:
                i += 1
                gameScore_surface = self.smallFont.render('{}. {}   {}'.format(i, player.name, score), True, player.color)
                surface.blit(gameScore_surface, (WIDTH/2-gameScore_surface.get_width()/2, 90 + i*20))
        
        newGame_surface = self.font.render('> ENTER', True, GREY)
        surface.blit(newGame_surface, (WIDTH/2-newGame_surface.get_width()/2, HEIGHT-50))
    
    def loopFunc(self, appState, events):
        for event in events: 
            self.handle_event(event, appState)

        self.update()

    def __init__(self, appState):
        self.font = pygame.font.Font('freesansbold.ttf', 15)
        self.smallFont = pygame.font.Font('freesansbold.ttf', 12)
        self.score_surface = self.font.render('SCORE', True, WHITE)
        self.noGames_surface = self.smallFont.render('NO GAMES YET', True, GREY)
        self.newPlayer_surface = self.font.render('', True, GREY)
        self.playerList = appState.players
        self.gamesList = []
        self.askForNewPlayer = False

        for player in appState.players:
            for score in player.wonGames:
                if len(self.gamesList) >= 4:
                    break
                self.gamesList.append((player, score))
        
        self.initialDraw(appState.surface)

class SelectPlayersScreen:
    def __init__(self, appState):
        self.font = pygame.font.Font('freesansbold.ttf', 15)
        self.smallFont = pygame.font.Font('freesansbold.ttf', 10)
        self.add_players_surface = self.font.render('n: Add Player', True, GREY)
        self.playersTextList = []

        i = 0
        for player in appState.players:
            self.playersTextList.append(SelectableText(WIDTH/2, 90 + i*30, self.font, str(i+1) +' '+ player.name, i, player.color))
            i += 1

    def handle_event(self, event, appState):
        if event.type == pygame.KEYDOWN:  
            if len(self.playersTextList) >= 1 and event.key == pygame.K_1:
                self.playersTextList[0].switch()
            elif len(self.playersTextList) >= 2 and  event.key == pygame.K_2:
                self.playersTextList[1].switch()
            elif len(self.playersTextList) >= 3 and  event.key == pygame.K_3:
                self.playersTextList[2].switch()
            elif len(self.playersTextList) >= 4 and  event.key == pygame.K_4:
                self.playersTextList[3].switch()
            elif event.key == pygame.K_n and len(appState.players) <= 3: 
                appState.setScreenAsAskForPlayerName(AskForPlayerNameScreen(appState))
                return     

    def update(self):
        return
        
    def draw(self, appState):
        appState.surface.fill((30, 30, 30))
        if len(appState.players) <= 3:
            appState.surface.blit(self.add_players_surface, (WIDTH-self.add_players_surface.get_width()-10, 20))

        for selectableText in self.playersTextList:
            selectableText.draw(appState.surface)
    
    def loopFunc(self, appState, events):
        for event in events: 
            self.handle_event(event, appState)
            
        self.update()
        self.draw(appState)

        player1 = None
        for selectableText in self.playersTextList:
            if selectableText.active:
                player = appState.players[selectableText.index]
                if player1 == None:
                    player1 = player
                else:
                    ('navigate')
                    appState.setScreenAsGame(GameState(appState, player1, player))

class AskForPlayerNameScreen:

    def __init__(self, appState):
        if len(appState.players) == 4:
            appState.setScreenAsSelctPlayers(SelectPlayersScreen(appState))
            return

        self.newColor = PLAYERCOLORS[len(appState.players)]
        self.font = pygame.font.Font('freesansbold.ttf', 40)
        self.input_box = CenteredInputBox(30, 40, self.font, self.newColor)

    def handle_event(self, event):
        self.input_box.handle_event(event)

    def update(self, appState):
        self.input_box.update()
        if self.input_box.done:
            appState.players.append(Player(self.input_box.text, self.newColor))
            appState.setScreenAsSelctPlayers(SelectPlayersScreen(appState)) 
        
    def draw(self, surface):
        surface.fill((30, 30, 30))
        self.input_box.draw(surface)

    def loopFunc(self, appState, events):
        for event in events: 
            self.handle_event(event)
            
        self.update(appState)
        self.draw(appState.surface)

class GameState:
    def __init__(self, appState, player1, player2):
        self.player1 = player1
        self.player2 = player2
        self.player1wins = []
        self.player2wins = []

        self.setScreenAsGame(GameScreen(appState, player1, player2))
    
    def loopFunc(self, appState, gameState, events):
        self.nextScreenLoopFunc(appState, gameState, events)
    
    def nextScreenLoopFunc(self, appstate, gameState, events):
        return

    def setScreenAsGame(self, gameScreen):
        self.nextScreenLoopFunc = gameScreen.loopFunc
    
    def setScreenAsWinnerScreen(self, winnerScreen):
        self.nextScreenLoopFunc = winnerScreen.loopFunc

    def continueFromWinnerScreen(self, appState):
        if len(self.player1wins) == 3:
            self.player1.wonGames.append(averageScore(self.player1wins))
            appState.setScreenAsScoreScreen(ScoreScreen(appState))
        elif len(self.player2wins) == 3:
            self.player2.wonGames.append(averageScore(self.player2wins))
            appState.setScreenAsScoreScreen(ScoreScreen(appState))
        else:
            self.setScreenAsGame(GameScreen(appState, self.player1, self.player2))

    def player1won(self, appState, score):
            self.player1wins.append(score)
            self.setScreenAsWinnerScreen(WinnerScreen(appState, self, self.player1, score))
    
    def player2won(self, appState, score):
            self.player2wins.append(score)
            self.setScreenAsWinnerScreen(WinnerScreen(appState, self, self.player2, score))

class WinnerScreen:
    def handle_event(self, event, appState, gameState):
        if event.type == pygame.KEYDOWN:  
            if event.key == pygame.K_RETURN: 
                #pressedenter
                gameState.continueFromWinnerScreen(appState)

    def update(self):
        return

    def initialDraw(self, surface):
        surface.fill((30, 30, 30))

        surface.blit(self.players_surface, (WIDTH/2-self.players_surface.get_width()/2, 40))
        surface.blit(self.wonGames_surface, (WIDTH/2-self.wonGames_surface.get_width()/2, 60))
        surface.blit(self.winner_surface, (WIDTH/2-self.winner_surface.get_width()/2, 120))
        surface.blit(self.score_surface, (WIDTH/2-self.score_surface.get_width()/2, 150))
        
        
        newGame_surface = self.font.render('> ENTER', True, GREY)
        surface.blit(newGame_surface, (WIDTH/2-newGame_surface.get_width()/2, HEIGHT-50))
    
    def loopFunc(self, appState, gameState, events):
        for event in events: 
            self.handle_event(event, appState, gameState)

        self.update()

    def __init__(self, appState, gameState, winner, score):
        self.score = score
        self.bigfont = pygame.font.Font('freesansbold.ttf', 19)
        self.font = pygame.font.Font('freesansbold.ttf', 15)
        self.smallFont = pygame.font.Font('freesansbold.ttf', 14)
        self.winner_surface = self.bigfont.render(winner.name +' won', True, winner.color)
        self.score_surface = self.font.render('Score: ' +str(score), True, WHITE)
        self.players_surface = self.smallFont.render('{} / {}'.format(gameState.player1.name, gameState.player2.name), True, WHITE)
        self.wonGames_surface = self.smallFont.render('{} / {}'.format(len(gameState.player1wins), len(gameState.player2wins)), True, WHITE)
        
        self.initialDraw(appState.surface)

class GameScreen:
    def __init__(self, appState, player1, player2):
        self.start = appState.elapsedTime
        self.player1Tron = Tron(Vector(WIDTH*0.25, HEIGHT/2), player1)
        self.player2Tron = Tron(Vector(WIDTH*0.75, HEIGHT/2), player2)
        self.winner = None

        drawBackround(appState.surface, [self.player1Tron.position, self.player2Tron.position])
        drawTron(appState.surface, self.player1Tron)
        drawTron(appState.surface, self.player2Tron)
        
    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_UP:
                self.player1Tron.moveUp()
            elif event.key == pygame.K_DOWN:
                self.player1Tron.moveDown()
            elif event.key == pygame.K_RIGHT:
                self.player1Tron.moveRight()
            elif event.key == pygame.K_LEFT:
                self.player1Tron.moveLeft()
            elif event.key == pygame.K_w:    
                self.player2Tron.moveUp()
            elif event.key == pygame.K_s:  
                self.player2Tron.moveDown()
            elif event.key == pygame.K_d:  
                self.player2Tron.moveRight()
            elif event.key == pygame.K_a: 
                self.player2Tron.moveLeft()    
    
    def update(self, surface):
        updateTron(self.player1Tron, surface)
        updateTron(self.player2Tron, surface)

    def draw(self, surface):
        drawTron(surface, self.player1Tron)
        drawTron(surface, self.player2Tron)

    def loopFunc(self, appState, gameState, events):
        for event in events: 
            self.handle_event(event)

        if appState.elapsedTime < (self.start + WAITBEFOREGAME):
            return 

        self.update(appState.surface)
        self.draw(appState.surface)

        if self.player1Tron.isDead:
            gameState.player2won(appState, calculateScore(self.start, appState.elapsedTime))

        if self.player2Tron.isDead:
            gameState.player1won(appState, calculateScore(self.start, appState.elapsedTime))

def main():
    surface = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Tron")
    frequence = pygame.time.Clock()

    elapsedTime = 0

    appState = AppState(surface, [Player('PLYR1', PLAYERCOLORS[0]), Player('PLYR2', PLAYERCOLORS[1])], elapsedTime)
    appState.setScreenAsScoreScreen(ScoreScreen(appState))

    loop=True
    while loop==True:
        
        events = pygame.event.get()
        for event in events:
            if event.type == pygame.QUIT:
                loop = False

        loopFunc = appState.screenLoopFunc
        loopFunc(appState, events, elapsedTime)

        pygame.display.update() 
        frequence.tick(60)
        elapsedTime += 1
    
    return

if __name__ == '__main__':
    pygame.init()
    main()
    pygame.quit()