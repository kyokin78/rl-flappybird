from itertools import cycle
import random
import sys
import os
import argparse
import pickle
import datetime

import pygame
from pygame.locals import *

sys.path.append(os.getcwd())

from enum import Enum
class Mode(Enum):
    NORMAL = 1
    PLAYER_AI = 2
    TRAIN = 3
    TRAIN_NOUI = 4
    TRAIN_REPLAY = 5

from bot import Bot

# Initialize the bot
bot = Bot()

SCREENWIDTH = 288
SCREENHEIGHT = 512
# amount by which base can maximum shift to left
PIPEGAPSIZE = 100  # gap between upper and lower part of pipe
BASEY = SCREENHEIGHT * 0.79
# image, sound and hitmask  dicts
IMAGES, SOUNDS, HITMASKS = {}, {}, {}
# Set init mode
MODE = Mode.NORMAL

# list of all possible players (tuple of 3 positions of flap)
PLAYERS_LIST = (
    # red bird
    (
        "data/assets/sprites/redbird-upflap.png",
        "data/assets/sprites/redbird-midflap.png",
        "data/assets/sprites/redbird-downflap.png",
    ),
    # blue bird
    (
        # amount by which base can maximum shift to left
        "data/assets/sprites/bluebird-upflap.png",
        "data/assets/sprites/bluebird-midflap.png",
        "data/assets/sprites/bluebird-downflap.png",
    ),
    # yellow bird
    (
        "data/assets/sprites/yellowbird-upflap.png",
        "data/assets/sprites/yellowbird-midflap.png",
        "data/assets/sprites/yellowbird-downflap.png",
    ),
)

# list of backgrounds
BACKGROUNDS_LIST = (
    "data/assets/sprites/background-day.png",
    "data/assets/sprites/background-night.png",
)

# list of pipes
PIPES_LIST = ("data/assets/sprites/pipe-green.png", "data/assets/sprites/pipe-red.png")

# image, Width, Height
WIDTH = 0
HEIGHT = 1
IMAGES_INFO = {}
IMAGES_INFO["player"] = ([34, 24], [34, 24], [34, 24])
IMAGES_INFO["pipe"] = [52, 320]
IMAGES_INFO["base"] = [336, 112]
IMAGES_INFO["background"] = [288, 512]

SCORES = []
EPISODE = 0
MAX_SCORE = 10_000_000
RESUME_ONCRASH = False

def getNextUpdateTime():
    return datetime.datetime.now() + datetime.timedelta(minutes = 5)

NEXT_UPDATE_TIME = getNextUpdateTime()

def main():
    global HITMASKS, SCREEN, FPSCLOCK, FPS, bot, MODE, SCORES, EPISODE, MAX_SCORE, RESUME_ONCRASH

    parser = argparse.ArgumentParser("flappy.py")
    parser.add_argument("--fps", type=int, default=60, help="number of frames per second, default in normal mode: 25, training or AI mode: 60")
    parser.add_argument("--episode", type=int, default=10000, help="episode number, default: 10000")
    parser.add_argument("--ai", action="store_true", help="use AI agent to play game")
    parser.add_argument("--train", action="store", choices=('normal', 'noui', 'replay'), help="train AI agent to play game, replay game from last 50 steps in 'replay' mode")
    parser.add_argument("--resume", action="store_true", help="Resume game from last 50 steps before crash")
    parser.add_argument("--max", type=int, default=10_000_000, help="maxium score per episode, restart game if agent reach this score, default: 10M")
    parser.add_argument("--dump_hitmasks", action="store_true", help="dump hitmasks to file and exit")
    args = parser.parse_args()

    FPS = args.fps
    EPISODE = args.episode
    MAX_SCORE = args.max
    RESUME_ONCRASH = args.resume
    if args.ai:
        MODE = Mode.PLAYER_AI
    elif args.train == "noui":
        MODE = Mode.TRAIN_NOUI
    elif args.train == "replay":
        MODE = Mode.TRAIN_REPLAY
        RESUME_ONCRASH = True
        FPS = 20
    elif args.train == "normal":
        MODE = Mode.TRAIN
    else:
        MODE = Mode.NORMAL
        FPS = 25

    if MODE == Mode.TRAIN_NOUI:
        # load dumped HITMASKS
        with open("data/hitmasks_data.pkl", "rb") as input:
            HITMASKS = pickle.load(input)
    else:
        pygame.init()
        FPSCLOCK = pygame.time.Clock()
        SCREEN = pygame.display.set_mode((SCREENWIDTH, SCREENHEIGHT))
        pygame.display.set_caption("Flappy Bird")

        # numbers sprites for score display
        IMAGES["numbers"] = (
            pygame.image.load("data/assets/sprites/0.png").convert_alpha(),
            pygame.image.load("data/assets/sprites/1.png").convert_alpha(),
            pygame.image.load("data/assets/sprites/2.png").convert_alpha(),
            pygame.image.load("data/assets/sprites/3.png").convert_alpha(),
            pygame.image.load("data/assets/sprites/4.png").convert_alpha(),
            pygame.image.load("data/assets/sprites/5.png").convert_alpha(),
            pygame.image.load("data/assets/sprites/6.png").convert_alpha(),
            pygame.image.load("data/assets/sprites/7.png").convert_alpha(),
            pygame.image.load("data/assets/sprites/8.png").convert_alpha(),
            pygame.image.load("data/assets/sprites/9.png").convert_alpha(),
        )

        # game over sprite
        IMAGES["gameover"] = pygame.image.load("data/assets/sprites/gameover.png").convert_alpha()
        # message sprite for welcome screen
        IMAGES["message"] = pygame.image.load("data/assets/sprites/message.png").convert_alpha()
        # base (ground) sprite
        IMAGES["base"] = pygame.image.load("data/assets/sprites/base.png").convert_alpha()

        # sounds
        if "win" in sys.platform:
            soundExt = ".wav"
        else:
            soundExt = ".ogg"

        SOUNDS["die"] = pygame.mixer.Sound("data/assets/audio/die" + soundExt)
        SOUNDS["hit"] = pygame.mixer.Sound("data/assets/audio/hit" + soundExt)
        SOUNDS["point"] = pygame.mixer.Sound("data/assets/audio/point" + soundExt)
        SOUNDS["swoosh"] = pygame.mixer.Sound("data/assets/audio/swoosh" + soundExt)
        SOUNDS["wing"] = pygame.mixer.Sound("data/assets/audio/wing" + soundExt)

    while True:
        if MODE != Mode.TRAIN_NOUI:
            # select random background sprites
            randBg = random.randint(0, len(BACKGROUNDS_LIST) - 1)
            IMAGES["background"] = pygame.image.load(BACKGROUNDS_LIST[randBg]).convert()

            # select random player sprites
            randPlayer = random.randint(0, len(PLAYERS_LIST) - 1)
            IMAGES["player"] = (
                pygame.image.load(PLAYERS_LIST[randPlayer][0]).convert_alpha(),
                pygame.image.load(PLAYERS_LIST[randPlayer][1]).convert_alpha(),
                pygame.image.load(PLAYERS_LIST[randPlayer][2]).convert_alpha(),
            )

            # select random pipe sprites
            pipeindex = random.randint(0, len(PIPES_LIST) - 1)
            IMAGES["pipe"] = (
                pygame.transform.rotate(pygame.image.load(PIPES_LIST[pipeindex]).convert_alpha(), 180),
                pygame.image.load(PIPES_LIST[pipeindex]).convert_alpha(),
            )

            # hismask for pipes
            HITMASKS["pipe"] = (getHitmask(IMAGES["pipe"][0]), getHitmask(IMAGES["pipe"][1]))

            # hitmask for player
            HITMASKS["player"] = (
                getHitmask(IMAGES["player"][0]),
                getHitmask(IMAGES["player"][1]),
                getHitmask(IMAGES["player"][2]),
            )

            if args.dump_hitmasks:
                with open("data/hitmasks_data.pkl", "wb") as output:
                    pickle.dump(HITMASKS, output, pickle.HIGHEST_PROTOCOL)
                sys.exit()

        movementInfo = showWelcomeAnimation()
        crashInfo = mainGame(movementInfo)
        showGameOverScreen(crashInfo)

def showDebugInfo(x, y, vel, pipe):
    white = (255,255,255)
    font = pygame.font.Font(None, 20)
    text = []
    text.append(font.render(str("x, y: {}, {}".format(x, y)), 1, white))
    text.append(font.render(str("V: {}".format(vel)), 1, white))
    text.append(font.render(str("x0, y0: {}, {}".format(int(pipe[0]["x"]-x), int(pipe[0]["y"]-y))), 1, white))
    text.append(font.render(str("x1, y1: {}, {}".format(int(pipe[1]["x"]-x), int(pipe[1]["y"]-y))), 1, white))
    for no, data in enumerate(text):
        SCREEN.blit(data, (0, 20*no))

def showWelcomeAnimation():
    """Shows welcome screen animation of flappy bird"""
    # index of player to blit on screen
    playerIndex = 0
    playerIndexGen = cycle([0, 1, 2, 1])
    # iterator used to change playerIndex after every 5th iteration
    loopIter = 0

    playerx = int(SCREENWIDTH * 0.2)
    playery = int((SCREENHEIGHT - IMAGES_INFO["player"][0][HEIGHT]) / 2)

    if MODE != Mode.TRAIN_NOUI:
        messagex = int((SCREENWIDTH - IMAGES["message"].get_width()) / 2)
        messagey = int(SCREENHEIGHT * 0.12)

    basex = 0
    # amount by which base can maximum shift to left
    baseShift = IMAGES_INFO["base"][WIDTH] - IMAGES_INFO["background"][WIDTH]

    # player shm for up-down motion on welcome screen
    playerShmVals = {"val": 0, "dir": 1}

    while True:
        """ De-activated the press key functionality"""

        if MODE != Mode.NORMAL:
            if MODE != Mode.TRAIN_NOUI:
                SOUNDS["wing"].play()
            return {
                "playery": playery + playerShmVals["val"],
                "basex": basex,
                "playerIndexGen": playerIndexGen,
            }
        else:
            for event in pygame.event.get():
                if event.type == QUIT or (event.type == KEYDOWN and event.key == K_ESCAPE):
                    pygame.quit()
                    sys.exit()
                if event.type == KEYDOWN and (event.key == K_SPACE or event.key == K_UP):
                    # make first flap sound and return values for mainGame
                    SOUNDS['wing'].play()
                    return {
                        'playery': playery + playerShmVals['val'],
                        'basex': basex,
                        'playerIndexGen': playerIndexGen,
                    }

        # adjust playery, playerIndex, basex
        if (loopIter + 1) % 5 == 0:
            playerIndex = next(playerIndexGen)
        loopIter = (loopIter + 1) % 30
        basex = -((-basex + 4) % baseShift)
        playerShm(playerShmVals)

        # draw sprites
        SCREEN.blit(IMAGES["background"], (0, 0))
        SCREEN.blit(IMAGES["player"][playerIndex], (playerx, playery + playerShmVals["val"]))
        SCREEN.blit(IMAGES["message"], (messagex, messagey))
        SCREEN.blit(IMAGES["base"], (basex, BASEY))

        pygame.display.update()
        FPSCLOCK.tick(FPS)


def updateQtable(score):
    global NEXT_UPDATE_TIME

    if MODE in [Mode.TRAIN, Mode.TRAIN_NOUI, Mode.TRAIN_REPLAY]:
        print("Game " + str(bot.gameCNT) + ": " + str(score))

        justUpdate = False
        if MODE == Mode.TRAIN or score > 100_000 or datetime.datetime.now() > NEXT_UPDATE_TIME:
            bot.dump_qvalues(force=True)
            justUpdate = True
            NEXT_UPDATE_TIME = getNextUpdateTime()

        if score > max(SCORES, default=0) and score > 100_000:
            print("\n$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$")
            print("$$$$$$$$ NEW RECORD: %d $$$$$$$$" % score)
            print("$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$\n")

        SCORES.append(score)
        
        if bot.gameCNT >= EPISODE:
            if not justUpdate: bot.dump_qvalues(force=True)
            showPerformance()
            pygame.quit()
            sys.exit()


import copy
def mainGame(movementInfo):

    score = playerIndex = loopIter = 0
    playerIndexGen = movementInfo["playerIndexGen"]

    playerx, playery = int(SCREENWIDTH * 0.2), movementInfo["playery"]

    basex = movementInfo["basex"]
    baseShift = IMAGES_INFO["base"][WIDTH] - IMAGES_INFO["background"][WIDTH]

    # get 2 new pipes to add to upperPipes lowerPipes list
    newPipe1 = getRandomPipe()
    newPipe2 = getRandomPipe()

    # list of upper pipes
    upperPipes = [
        {"x": SCREENWIDTH + 200, "y": newPipe1[0]["y"]},
        {"x": SCREENWIDTH + 200 + (SCREENWIDTH / 2), "y": newPipe2[0]["y"]},
    ]

    # list of lowerpipe
    lowerPipes = [
        {"x": SCREENWIDTH + 200, "y": newPipe1[1]["y"]},
        {"x": SCREENWIDTH + 200 + (SCREENWIDTH / 2), "y": newPipe2[1]["y"]},
    ]

    pipeVelX = -4

    # player velocity, max velocity, downward accleration, accleration on flap
    playerVelY = -9  # player's velocity along Y, default same as playerFlapped
    playerMaxVelY = 10  # max vel along Y, max descend speed
    playerMinVelY = -8  # min vel along Y, max ascend speed
    playerAccY = 1  # players downward accleration
    playerFlapAcc = -9  # players speed on flapping
    playerFlapped = False  # True when player flaps

    printHighScore = False

    stateHistory = []   # record last 50 state for restart
    replayGame = False
    restartGame = False
    steps = 0
    refreshCount = 1
    while True:

        if MODE != Mode.TRAIN_NOUI:
            if MODE == Mode.TRAIN_REPLAY and not replayGame and not restartGame:
                refreshCount += 1

            if MODE != Mode.TRAIN_REPLAY or refreshCount % 5000 == 0 or replayGame or restartGame:
                if refreshCount % 5000 == 0:
                    refreshCount = 1

                for event in pygame.event.get():
                    if event.type == QUIT or (event.type == KEYDOWN and event.key == K_ESCAPE):
                        pygame.quit()
                        sys.exit()
                    if event.type == KEYDOWN and (event.key == K_SPACE or event.key == K_UP):
                        if playery > -2 * IMAGES["player"][0].get_height():
                            playerVelY = playerFlapAcc
                            playerFlapped = True
                            SOUNDS["wing"].play()

        if replayGame:
            steps += 1
            if steps >= len(stateHistory):
                return {
                "y": playery,
                "groundCrash": False,
                "basex": basex,
                "upperPipes": upperPipes,
                "lowerPipes": lowerPipes,
                "score": score,
                "playerVelY": playerVelY,
            }
            (playerx, playery, playerVelY, lowerPipes, upperPipes, score, playerIndex) = stateHistory[steps]

        else:
            
            if MODE in [Mode.TRAIN_NOUI, Mode.TRAIN, Mode.TRAIN_REPLAY] and RESUME_ONCRASH: 
                currentState = [playerx, playery, playerVelY, copy.deepcopy(lowerPipes), copy.deepcopy(upperPipes), score, playerIndex]
                if restartGame and steps < len(stateHistory):
                    stateHistory[steps] = currentState
                else:
                    stateHistory.append(currentState)
                    if len(stateHistory) > 50:
                        stateHistory.pop(0)
            
            if MODE != Mode.NORMAL and bot.act(playerx, playery, playerVelY, lowerPipes):
                if playery > -2 * IMAGES_INFO["player"][0][HEIGHT]:
                    playerVelY = playerFlapAcc
                    playerFlapped = True
                    if MODE != Mode.TRAIN_NOUI and MODE != Mode.TRAIN_REPLAY:
                        SOUNDS["wing"].play()

       # check for crash here
        crashTest = checkCrash(
            {"x": playerx, "y": playery, "index": playerIndex}, upperPipes, lowerPipes
        )
        if crashTest[0]:
            #print(playerx, playery, playerIndex, upperPipes, lowerPipes)
            if MODE == Mode.TRAIN_REPLAY:
                if not replayGame:
                    restartGame = False
                    replayGame = True
                    steps = -1
                    print("REPLAY GAME for last 50 steps...")
                    continue
                else:
                    replayGame = False

            # Update the q scores
            if MODE in [Mode.TRAIN_NOUI, Mode.TRAIN, Mode.TRAIN_REPLAY]:
                bot.update_scores()

                if len(stateHistory) > 20 and (not restartGame or (restartGame and steps > 10)):
                    updateQtable(score)
                    (playerx, playery, playerVelY, lowerPipes, upperPipes, score, playerIndex) = stateHistory[0]
                    if score > 100_000:
                        print("\n" + "#"*40)
                        print("RESTART FROM LAST 50th state: %s" % bot.get_state(playerx, playery, playerVelY, lowerPipes))
                        print("#"*40 + "\n")
                    score = 0
                    restartGame = True
                    replayGame = False
                    steps = 0      # show the first 100 steps in the new game
                    #print("CONTINUE GAME from death position...")
                    continue

                restartGame = False

            return {
                "y": playery,
                "groundCrash": crashTest[1],
                "basex": basex,
                "upperPipes": upperPipes,
                "lowerPipes": lowerPipes,
                "score": score,
                "playerVelY": playerVelY,
            }

        # check for score
        playerMidPos = playerx + IMAGES_INFO["player"][0][WIDTH] / 2
        for pipe in upperPipes:
            pipeMidPos = pipe["x"] + IMAGES_INFO["pipe"][WIDTH] / 2
            if pipeMidPos <= playerMidPos < pipeMidPos + 4:
                score += 1
                printHighScore = True
                if MODE not in [Mode.TRAIN_NOUI, Mode.TRAIN_REPLAY]:
                    SOUNDS["point"].play()
                if score >= MAX_SCORE:    # terminate game if reach maxium score and restart game
                    bot.terminate_game()
                    return {
                        "score": score,
                    }

        if MODE in [Mode.TRAIN_NOUI, Mode.TRAIN, Mode.TRAIN_REPLAY] and printHighScore and score != 0 and score % 10000==0:
            print("Game " + str(bot.gameCNT+1) + ": reach " + str(score) + "...")
            printHighScore = False

        # playerIndex basex change
        if (loopIter + 1) % 3 == 0:
            playerIndex = next(playerIndexGen)
        loopIter = (loopIter + 1) % 30
        basex = -((-basex + 100) % baseShift)

        # player's movement
        if playerVelY < playerMaxVelY and not playerFlapped:
            playerVelY += playerAccY
        if playerFlapped:
            playerFlapped = False
        playerHeight = IMAGES_INFO["player"][playerIndex][HEIGHT]
        playery += min(playerVelY, BASEY - playery - playerHeight)

        addPipes = True
        if restartGame:
            steps += 1
            if steps < len(stateHistory):
                (_, _, _, lowerPipes, upperPipes, _, _) = stateHistory[steps]
                addPipes = False
            elif steps > 100:
                restartGame = False

        if not replayGame and addPipes:
             # move pipes to left
            for uPipe, lPipe in zip(upperPipes, lowerPipes):
                uPipe["x"] += pipeVelX
                lPipe["x"] += pipeVelX

           # add new pipe when first pipe is about to touch left of screen
            if 0 < upperPipes[0]["x"] < 5:
                newPipe = getRandomPipe()
                upperPipes.append(newPipe[0])
                lowerPipes.append(newPipe[1])

            # remove first pipe if its out of the screen
            if upperPipes[0]["x"] < -IMAGES_INFO["pipe"][WIDTH]:
                upperPipes.pop(0)
                lowerPipes.pop(0)

        if MODE not in [Mode.TRAIN_NOUI, Mode.TRAIN_REPLAY] or (MODE == Mode.TRAIN_REPLAY and (restartGame or replayGame)):
            # draw sprites
            SCREEN.blit(IMAGES["background"], (0, 0))

            for uPipe, lPipe in zip(upperPipes, lowerPipes):
                SCREEN.blit(IMAGES["pipe"][0], (uPipe["x"], uPipe["y"]))
                SCREEN.blit(IMAGES["pipe"][1], (lPipe["x"], lPipe["y"]))

            SCREEN.blit(IMAGES["base"], (basex, BASEY))
            # print score so player overlaps the score
            showScore(score)
            SCREEN.blit(IMAGES["player"][playerIndex], (playerx, playery))
            if MODE == Mode.TRAIN_REPLAY:
                showDebugInfo(playerx, playery, playerVelY, lowerPipes)

            pygame.display.update()
            FPSCLOCK.tick(FPS)

import matplotlib.pyplot as plt
#from matplotlib.ticker import MaxNLocator
def showPerformance():
    average = []
    num = 0
    sum_s = 0

    for s in SCORES:
        num += 1
        sum_s += s
        average.append(sum_s/num)

    print("\nEpisode: {}, highest score: {}, average: {}".format(num, max(SCORES), average[-1]))
    plt.figure(1)
    #plt.gca().get_xaxis().set_major_formatter(MaxNLocator(integer=True))
    plt.scatter(range(1, num+1), SCORES, c="green", s=3)
    plt.plot(range(1, num+1), average, 'b')
    plt.xlim((1,num))
    plt.ylim((0,int(max(SCORES)*1.1)))

    plt.title("Score distribution")
    plt.xlabel("Episode")
    plt.ylabel("Score")
    plt.show()

def showGameOverScreen(crashInfo):

    updateQtable(crashInfo["score"])
    if MODE != Mode.NORMAL and MODE != Mode.PLAYER_AI:
        return

    """crashes the player down and shows gameover image"""
    score = crashInfo["score"]
    playerx = SCREENWIDTH * 0.2
    playery = crashInfo["y"]
    playerHeight = IMAGES["player"][0].get_height()
    playerVelY = crashInfo["playerVelY"]
    playerAccY = 2

    basex = crashInfo["basex"]

    upperPipes, lowerPipes = crashInfo["upperPipes"], crashInfo["lowerPipes"]

    # play hit and die sounds
    SOUNDS["hit"].play()
    if not crashInfo["groundCrash"]:
        SOUNDS["die"].play()

    gameoverx = int((SCREENWIDTH - IMAGES["gameover"].get_width()) / 2)
    gameovery = int(SCREENHEIGHT * 0.4)

    while True:
        """ De-activated press key functionality """
        for event in pygame.event.get():
            if event.type == QUIT or (event.type == KEYDOWN and event.key == K_ESCAPE):
                pygame.quit()
                sys.exit()
            if event.type == KEYDOWN and (event.key == K_SPACE or event.key == K_UP):
                if playery + playerHeight >= BASEY - 1:
                    return
        
        #return  ### Must remove to activate press-key functionality

        # player y shift
        if playery + playerHeight < BASEY - 1:
            playery += min(playerVelY, BASEY - playery - playerHeight)

        # player velocity change
        if playerVelY < 15:
            playerVelY += playerAccY

        # draw sprites
        SCREEN.blit(IMAGES["background"], (0, 0))

        for uPipe, lPipe in zip(upperPipes, lowerPipes):
            SCREEN.blit(IMAGES["pipe"][0], (uPipe["x"], uPipe["y"]))
            SCREEN.blit(IMAGES["pipe"][1], (lPipe["x"], lPipe["y"]))

        SCREEN.blit(IMAGES["base"], (basex, BASEY))
        showScore(score)
        SCREEN.blit(IMAGES["player"][1], (playerx, playery))
        SCREEN.blit(IMAGES["gameover"], (gameoverx, gameovery))

        FPSCLOCK.tick(FPS)
        pygame.display.update()


def playerShm(playerShm):
    """oscillates the value of playerShm['val'] between 8 and -8"""
    if abs(playerShm["val"]) == 8:
        playerShm["dir"] *= -1

    if playerShm["dir"] == 1:
        playerShm["val"] += 1
    else:
        playerShm["val"] -= 1

def getRandomPipe():
    """returns a randomly generated pipe"""
    # y of gap between upper and lower pipe
    gapY = random.randrange(0, int(BASEY * 0.6 - PIPEGAPSIZE))
    gapY += int(BASEY * 0.2)
    pipeHeight = IMAGES_INFO["pipe"][HEIGHT]
    pipeX = SCREENWIDTH + 10

    return [
        {"x": pipeX, "y": gapY - pipeHeight},  # upper pipe
        {"x": pipeX, "y": gapY + PIPEGAPSIZE},  # lower pipe
    ]


def showScore(score):
    """displays score in center of screen"""
    scoreDigits = [int(x) for x in list(str(score))]
    totalWidth = 0  # total width of all numbers to be printed

    for digit in scoreDigits:
        totalWidth += IMAGES["numbers"][digit].get_width()

    Xoffset = (SCREENWIDTH - totalWidth) / 2

    for digit in scoreDigits:
        SCREEN.blit(IMAGES["numbers"][digit], (Xoffset, SCREENHEIGHT * 0.1))
        Xoffset += IMAGES["numbers"][digit].get_width()


def checkCrash(player, upperPipes, lowerPipes):
    """returns True if player collders with base or pipes."""
    pi = player["index"]
    player["w"] = IMAGES_INFO["player"][0][WIDTH]
    player["h"] = IMAGES_INFO["player"][0][HEIGHT]

    # if player crashes into ground
    if (player["y"] + player["h"] >= BASEY - 1) or (player["y"] + player["h"] <= 0):
        return [True, True]
    else:

        playerRect = pygame.Rect(player["x"], player["y"], player["w"], player["h"])
        pipeW = IMAGES_INFO["pipe"][WIDTH]
        pipeH = IMAGES_INFO["pipe"][HEIGHT]

        for uPipe, lPipe in zip(upperPipes, lowerPipes):
            # upper and lower pipe rects
            uPipeRect = pygame.Rect(uPipe["x"], uPipe["y"], pipeW, pipeH)
            lPipeRect = pygame.Rect(lPipe["x"], lPipe["y"], pipeW, pipeH)

            # player and upper/lower pipe hitmasks
            pHitMask = HITMASKS["player"][pi]
            uHitmask = HITMASKS["pipe"][0]
            lHitmask = HITMASKS["pipe"][1]

            # if bird collided with upipe or lpipe
            uCollide = pixelCollision(playerRect, uPipeRect, pHitMask, uHitmask)
            lCollide = pixelCollision(playerRect, lPipeRect, pHitMask, lHitmask)

            if uCollide or lCollide:
                return [True, False]

    return [False, False]


def pixelCollision(rect1, rect2, hitmask1, hitmask2):
    """Checks if two objects collide and not just their rects"""
    rect = rect1.clip(rect2)

    if rect.width == 0 or rect.height == 0:
        return False

    x1, y1 = rect.x - rect1.x, rect.y - rect1.y
    x2, y2 = rect.x - rect2.x, rect.y - rect2.y

    for x in range(rect.width):
        for y in range(rect.height):
            if hitmask1[x1 + x][y1 + y] and hitmask2[x2 + x][y2 + y]:
                return True
    return False


def getHitmask(image):
    """returns a hitmask using an image's alpha."""
    mask = []
    for x in range(image.get_width()):
        mask.append([])
        for y in range(image.get_height()):
            mask[x].append(bool(image.get_at((x, y))[3]))
    return mask


if __name__ == "__main__":
    main()
