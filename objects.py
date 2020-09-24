import pygame
from config import config
from abc import ABCMeta, abstractmethod

EC_QUITGAME = 0
EC_STARTGAME = 1
EC_PAUSE = 2
EC_RESUME = 3

class ScreenStatus(metaclass=ABCMeta):
    def __init__(self, game):
        self.game = game
    @abstractmethod
    def display(self):
        pass
    @abstractmethod
    def update(self):
        pass
    def handle(self, event):
        if event.type == pygame.QUIT:
            return EC_QUITGAME
        return None

class Startup(ScreenStatus):
    def display(self):
        screen = self.game.getScreen()
        screen.fill(config.theme.getRaw('backgroundColor'))
        title = self.game.getBigFont().render('Squash', True, config.theme.getRaw('textColor'))
        info = self.game.getSmallFont().render(f'Copyright 2020 (c) {config.game.developer}', True, config.theme.getRaw('textColor'))
        rect = screen.get_rect()
        title_rect = title.get_rect()
        info_rect = info.get_rect()
        title_rect.midbottom = rect.centerx, rect.centery - config.layout.textOffset
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

class Level(ScreenStatus):
    def display(self):
        screen = self.game.getScreen()
        screen.fill(config.theme.getRaw('backgroundColor'))
    def update(self):
        screen = self.game.getScreen()
        screen.fill(config.theme.getRaw('backgroundColor'))
    def handle(self, event):
        handled = super().handle(event)
        if handled is not None:
            return handled
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            return EC_PAUSE

class Paused(ScreenStatus):
    def display(self):
        screen = self.game.getScreen()
        screen.fill(config.theme.getRaw('backgroundColor'))
        title = self.game.getBigFont().render('Paused', True, config.theme.getRaw('textColor'))
        text = self.game.getFont().render('Press Any Key to Resume...', True, config.theme.getRaw('textColor'))
        rect = screen.get_rect()
        title_rect = title.get_rect()
        text_rect = text.get_rect()
        title_rect.midbottom = rect.centerx, rect.centery - config.layout.textOffset
        text_rect.midtop = rect.centerx, rect.centery + config.layout.textOffset
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

class Game:
    def __init__(self):
        self.started = False
    def start(self):
        self.screenStatus = Startup(self)
        self.tempScreenStatus = None
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
    def mainLoop(self):
        clock = pygame.time.Clock()
        self.screenStatus.display()
        while self.started:
            clock.tick(30)
            for event in pygame.event.get():
                ecode = self.screenStatus.handle(event)
                if ecode == EC_QUITGAME:
                    self.started = False
                    break
                if ecode == EC_STARTGAME:
                    self.screenStatus = Level(self)
                    self.screenStatus.display()
                elif ecode == EC_PAUSE:
                    self.tempScreenStatus = self.screenStatus
                    self.screenStatus = Paused(self)
                    self.screenStatus.display()
                elif ecode == EC_RESUME:
                    self.screenStatus = self.tempScreenStatus
            self.screenStatus.update()
            pygame.display.flip()
