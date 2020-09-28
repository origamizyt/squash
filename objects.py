import pygame, shelve
from config import config
from abc import ABCMeta, abstractmethod
from random import randint

EC_QUITGAME = 0
EC_STARTGAME = 1
EC_PAUSE = 2
EC_RESUME = 3
EC_NEXTLEVEL = 4
EC_PREPARED = 5
EC_RESTART = 6
EC_RESET = 7

VD_NONE = 0
VD_LEFT = -1
VD_RIGHT = 1

EID_TIMER = pygame.USEREVENT

class GameEntity(pygame.sprite.Sprite):
    def __init__(self, game):
        super().__init__()
        self.game = game
        self.screenRect = game.getScreenRect()
    def draw(self):
        self.game.getScreen().blit(self.image, self.rect)

class Pumpkin(GameEntity):
    def __init__(self, game, pos):
        super().__init__(game)
        self.image = pygame.image.load(config.objects.pumpkinImage)
        self.rect = self.image.get_rect()
        self.rect.midtop = randint(pos-config.control.positionOffset, pos+config.control.positionOffset), 0
    def update(self, speed):
        self.rect.top += speed
        if self.rect.bottom > self.screenRect.height:
            self.kill()

class Victim(GameEntity):
    def __init__(self, game):
        super().__init__(game)
        self.image = pygame.image.load(config.objects.victimImage)
        self.rect = self.image.get_rect()
        self.rect.midbottom = game.getScreenRect().midbottom
    def update(self, speed, direction):
        self.rect.move_ip(direction * speed, 0)
        if self.rect.centerx < 0:
            self.rect.centerx = 0
        elif self.rect.centerx > self.game.getScreenRect().width:
            self.rect.centerx = self.game.getScreenRect().width

class Stage(metaclass=ABCMeta):
    def __init__(self, game):
        self.game = game
    @abstractmethod
    def display(self):
        pass
    @abstractmethod
    def update(self):
        pass
    def handle(self, event):
        if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
            return EC_QUITGAME

class Startup(Stage):
    def display(self):
        screen = self.game.getScreen()
        screen.fill(config.theme.getRaw('backgroundColor'))
        title = self.game.getBigFont().render('Squash', True, config.theme.getRaw('textColor'))
        info = self.game.getSmallFont().render(f'Copyright 2020 (c) {config.game.developer}', True, config.theme.getRaw('textColor'))
        rect = screen.get_rect()
        title_rect = title.get_rect()
        info_rect = info.get_rect()
        title_rect.midbottom = rect.centerx, rect.centery - config.screen.textOffset
        info_rect.midbottom = rect.midbottom
        screen.blit(title, title_rect)
        screen.blit(info, info_rect)
    def update(self):
        pass
    def handle(self, event):
        handled = super().handle(event)
        if handled is not None:
            return handled
        if event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN:
            return EC_STARTGAME

class LevelPreparation(Stage):
    def __init__(self, game, levelnum):
        super().__init__(game)
        self.levelNumber = levelnum
        self.preparation = config.control.preparation
        self.needsUpdate = False
    def display(self):
        screen = self.game.getScreen()
        screen.fill(config.theme.getRaw('backgroundColor'))
        info = self.game.getSmallFont().render(f'Level {self.levelNumber}', True, config.theme.getRaw('textColor'))
        count = self.game.getBigFont().render(str(self.preparation), True, config.theme.getRaw('textColor'))
        rect = screen.get_rect()
        info_rect = info.get_rect()
        count_rect = count.get_rect()
        info_rect.midtop = rect.midtop
        count_rect.center = rect.center
        screen.blit(info, info_rect)
        screen.blit(count, count_rect)
        pygame.time.set_timer(EID_TIMER, 1000)
    def update(self):
        if not self.needsUpdate: return
        screen = self.game.getScreen()
        screen.fill(config.theme.getRaw('backgroundColor'))
        info = self.game.getSmallFont().render(f'Level {self.levelNumber}', True, config.theme.getRaw('textColor'))
        count = self.game.getBigFont().render(str(self.preparation), True, config.theme.getRaw('textColor'))
        rect = screen.get_rect()
        info_rect = info.get_rect()
        count_rect = count.get_rect()
        info_rect.midtop = rect.midtop
        count_rect.center = rect.center
        screen.blit(info, info_rect)
        screen.blit(count, count_rect)
        pygame.time.set_timer(EID_TIMER, 1000)
        self.needsUpdate = False
    def handle(self, event):
        handled = super().handle(event)
        if handled is not None:
            return handled
        if event.type == EID_TIMER:
            self.preparation -= 1
            if self.preparation == 0:
                pygame.time.set_timer(EID_TIMER, 0)
                return EC_PREPARED
            self.needsUpdate = True

class Level(Stage):
    def isCleared(self):
        return self.levelCleared
    def __init__(self, game, levelnum):
        super().__init__(game)
        self.levelNumber = levelnum
        self.group = pygame.sprite.RenderUpdates()
        self.victim = None
        self.shouldCreate = True
        self.needsUpdate = True
        self.pumpkinsLeft = config.control.pumpkinAmount
        self.levelCleared = False
        self.levelFailed = False
        self.victimDirection = VD_NONE
        self.pumpkinSpeed = config.control.initialSpeed + (levelnum - 1) * config.control.acceleration
        self.victimSpeed = config.control.victimSpeed + (levelnum - 1) * config.control.victimAcceleration
    def display(self):
        screen = self.game.getScreen()
        screen.fill(config.theme.getRaw('backgroundColor'))
        self.victim = Victim(self.game)
        self.victim.draw()
        pygame.time.set_timer(EID_TIMER, config.control.interval)
    def update(self):
        if not self.needsUpdate: return
        screen = self.game.getScreen()
        screen.fill(config.theme.getRaw('backgroundColor'))
        if self.shouldCreate:
            self.group.add(Pumpkin(self.game, self.victim.rect.centerx))
            self.pumpkinsLeft -= 1
            if self.pumpkinsLeft <= 0:
                pygame.time.set_timer(EID_TIMER, 0)
            self.shouldCreate = False
        self.group.update(self.pumpkinSpeed)
        self.group.draw(screen)
        self.victim.update(self.victimSpeed, self.victimDirection)
        self.victim.draw()
        if len(self.group) <= 0 and self.pumpkinsLeft <= 0:
            self.levelCleared = True
            screen = self.game.getScreen()
            screen.fill(config.theme.getRaw('backgroundColor'))
            title = self.game.getBigFont().render(f'Level {self.levelNumber} Cleared', True, config.theme.getRaw('textColor'))
            text = self.game.getFont().render(f'Click to Begin Next Level', True, config.theme.getRaw('textColor'))
            rect = screen.get_rect()
            title_rect = title.get_rect()
            text_rect = text.get_rect()
            title_rect.midbottom = rect.centerx, rect.centery - config.screen.textOffset
            text_rect.midtop = rect.centerx, rect.centery + config.screen.textOffset
            screen.blit(title, title_rect)
            screen.blit(text, text_rect)
            self.needsUpdate = False
        if pygame.sprite.spritecollideany(self.victim, self.group):
            self.levelFailed = True
            pygame.time.set_timer(EID_TIMER, 0)
            screen = self.game.getScreen()
            screen.fill(config.theme.getRaw('backgroundColor'))
            title = self.game.getBigFont().render(f'Level {self.levelNumber} Failed', True, config.theme.getRaw('textColor'))
            text = self.game.getFont().render(f'Click to Restart Level', True, config.theme.getRaw('textColor'))
            rect = screen.get_rect()
            title_rect = title.get_rect()
            text_rect = text.get_rect()
            title_rect.midbottom = rect.centerx, rect.centery - config.screen.textOffset
            text_rect.midtop = rect.centerx, rect.centery + config.screen.textOffset
            screen.blit(title, title_rect)
            screen.blit(text, text_rect)
            self.needsUpdate = False
    def handle(self, event):
        handled = super().handle(event)
        if handled is not None:
            return handled
        if event.type == EID_TIMER:
            self.shouldCreate = True
            return
        self.victimDirection = VD_NONE
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.levelCleared:
                return EC_NEXTLEVEL
            elif self.levelFailed:
                return EC_RESTART
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE and self.needsUpdate:
                return EC_PAUSE
            elif event.key == pygame.K_LEFT:
                self.victimDirection = VD_LEFT
            elif event.key == pygame.K_RIGHT:
                self.victimDirection = VD_RIGHT

class Paused(Stage):
    def display(self):
        screen = self.game.getScreen()
        screen.fill(config.theme.getRaw('backgroundColor'))
        title = self.game.getBigFont().render('Paused', True, config.theme.getRaw('textColor'))
        text = self.game.getFont().render('Press Any Key to Resume...', True, config.theme.getRaw('textColor'))
        rect = screen.get_rect()
        title_rect = title.get_rect()
        text_rect = text.get_rect()
        title_rect.midbottom = rect.centerx, rect.centery - config.screen.textOffset
        text_rect.midtop = rect.centerx, rect.centery + config.screen.textOffset
        screen.blit(title, title_rect)
        screen.blit(text, text_rect)
    def update(self): 
        pass
    def handle(self, event):
        handled = super().handle(event)
        if handled is not None:
            return handled
        if event.type == pygame.KEYDOWN:
            return EC_RESUME

class GameEnd(Stage):
    def display(self):
        screen = self.game.getScreen()
        screen.fill(config.theme.getRaw('backgroundColor'))
        title = self.game.getBigFont().render('Congratulations!', True, config.theme.getRaw('textColor'))
        text = pygame.image.load(config.objects.pumpkinImage)
        rect = screen.get_rect()
        title_rect = title.get_rect()
        text_rect = text.get_rect()
        title_rect.midbottom = rect.centerx, rect.centery - config.screen.textOffset
        text_rect.midtop = rect.centerx, rect.centery + config.screen.textOffset
        screen.blit(title, title_rect)
        screen.blit(text, text_rect)
    def update(self):
        pass
    def handle(self, event):
        handled = super().handle(event)
        if handled is not None:
            return handled
        if event.type == pygame.MOUSEBUTTONDOWN:
            return EC_RESET

class Game:
    def __init__(self):
        self.started = False
        db = shelve.open(config.objects.database)
        self.level = int(db.get('level', 1))
        db.close()
    def start(self):
        self.stage = Startup(self)
        self.tempStage = None
        self.screen = pygame.display.set_mode(config.screen.getRaw('size'), pygame.constants.FULLSCREEN if config.screen.fullscreen else 0)
        pygame.display.set_caption(f'{config.game.name} version {config.game.version}')
        self.bigFont = pygame.font.Font(config.theme.fontLocation, config.theme.bigFontSize)
        self.smallFont = pygame.font.Font(config.theme.fontLocation, config.theme.smallFontSize)
        self.font = pygame.font.Font(config.theme.fontLocation, config.theme.fontSize)
        self.started = True
        self.mainLoop()
    def getBigFont(self):
        return self.bigFont
    def getSmallFont(self):
        return self.smallFont
    def getFont(self):
        return self.font
    def getScreen(self):
        return self.screen
    def getScreenRect(self):
        return self.screen.get_rect()
    def getStage(self):
        return self.stage
    def setStage(self, newStage):
        self.stage = newStage
        self.stage.display()
    def saveAndSetStage(self, newStage):
        self.tempStage, self.stage = self.stage, newStage
        self.stage.display()
    def restoreStage(self):
        self.tempStage, self.stage = None, self.tempStage
    def mainLoop(self):
        clock = pygame.time.Clock()
        self.stage.display()
        while self.started:
            clock.tick(20)
            for event in pygame.event.get():
                ecode = self.stage.handle(event)
                if ecode == EC_QUITGAME:
                    self.started = False
                    break
                if ecode == EC_STARTGAME:
                    self.setStage(LevelPreparation(self, self.level))
                elif ecode == EC_PREPARED:
                    self.setStage(Level(self, self.level))
                elif ecode == EC_PAUSE:
                    self.saveAndSetStage(Paused(self))
                elif ecode == EC_RESUME:
                    self.restoreStage()
                elif ecode == EC_NEXTLEVEL:
                    if self.level >= config.control.levelCount:
                        self.level = 1
                        self.setStage(GameEnd(self))
                    else:
                        self.level += 1
                        self.setStage(LevelPreparation(self, self.level))
                elif ecode == EC_RESTART:
                    self.setStage(LevelPreparation(self, self.level))
                elif ecode == EC_RESTART:
                    self.setStage(Startup(self))
            self.stage.update()
            pygame.display.flip()
        self.stop()
    def stop(self):
        if isinstance(self.stage, Level) and self.stage.isCleared(): self.level += 1
        db = shelve.open(config.objects.database)
        db['level'] = self.level
        db.close()
