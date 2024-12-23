import os, sys, gc
import traceback as trace
import numpy as np
import pygame as pg

class Paddle(pg.sprite.Sprite):
    """Object controlled by player (either human or AI)
    Paddle can be moved up or down, so only on the y-axis. If included, 
    the ai agents get the position of the ball and the y-position of the 
    opponent paddle as input.
    
    Attributes
    
    image: rectangle sprite of the paddle
    rect.center:  coordinate (position) of the paddle's centre
    
    
    """    
    def __init__(self, screen_height, pos: pg.math.Vector2, *groups):
        """constructor for the Paddle class

        Args:
            pos (pg.math.Vector2): Initial position of the paddle
            groups: All sprite groups to assign Paddle sprite to
        """
        super().__init__(groups)
        self.image = pg.Surface([20, 100])
        self.image.fill((0,0,0))
        self.rect = self.image.get_rect()
        self.rect.center = pos
        self.y_ceil = screen_height
        self.y_movement = 0.0

    def move_y(self, dy=0.0):
        """apply movement on y-axis for paddle

        Args:
            dy (float): The y-gradient to move the paddle for. Defaults to 0.0. 
        """
        self.y_movement = dy

    def update(self):
        """update function of ball sprite, applied every frame of the pygame
        """
        self.rect.y += self.y_movement
        if self.rect.top > self.y_ceil: self.rect.top = self.y_ceil
        if self.rect.bottom < 0.0: self.rect.bottom = 0.0
        

class Ball(pg.sprite.Sprite):
    """Ball sprite class, inherits from pygame Sprite class.
    When each game round starts, ball is teleported to the middle of the field.
    Throughout every round, the ball can be reflected by the paddles changing its
    movement vector towards the other paddle. If the ball collides with the height
    limitations of the window, it will invert its y-movement. If colliding with the
    width limitations of the window, its collided attribute will indicate which side
    has been collided with. This determines the winner of the current round.
    
    """    
    def __init__(self, paddles : pg.sprite.Group, screen_size : pg.math.Vector2, init_pos : pg.math.Vector2, speed: float=1., *groups):
        """constructor for the Ball class

        Args:
            paddles(pg.sprite.Group): Sprite group which includes both (or more if you want to, I guess, idk, maybe) paddle sprites
            screen_size (pg.math.Vector2): Window screen width and height for window border collision
            init_pos (pg.math.Vector2): Initial position of the ball
            speed (float, optional): Movement speed of the ball. Defaults to 1..
            groups(list): Sprite groups to assign Paddle sprite to
        """
        super().__init__(groups)
        self.paddles = paddles
        self.borders = screen_size
        self.image = pg.Surface([20, 20])
        self.image.fill((0,0,0))
        self.rect = self.image.get_rect()
        self.rect.center = init_pos
        self.speed = speed
        self.movement_vec = pg.math.Vector2(1.,4.) # Movement vector where the ball initially moves towards
        self.x_collided = 0  #can take values 0, 1 or -1 meaning playing = 0, touched left goal = -1, touched right goal = 1

    def score(self):
        return self.x_collided
    
    def update(self):
        """update function of ball sprite, applied every frame of the pygame
        """
        width, height = self.borders
        paddles = self.paddles 
        dx, dy = self.movement_vec * self.speed
        # obsolete? (new_ball_pos = self.rect.center + self.movement_vec)
        # Check if current movement leads ball to collide with left or right window borders.
        # If so, one paddle has scored.
        if self.rect.left + dx < 0: self.x_collided = -1 # BALL touched left goal
        elif self.rect.right + dx >= width: self.x_collided = 1 #ball touched right goal
        # Check if current movement leads ball to collide with left or right window borders.
        # If so, invert y projectory and update the y-position according to what distance it
        # has travelled beyond the stepped over border.
        if self.rect.top + dy < 0: 
            print("Top", self.rect.top)
            # The distance after the collision must be the overflowing distance beyond the border.
            # I.e. the y-position of the ball after the collision on y=0 is the y-distance below 0 negated.
            # (total y-distance = rect.center[1] [-> distance until y=0] + (movement_vec[1] - rect.center[1]) [-> distance after y=0]) 
            dist_after_coll = -(self.rect.top + dy) 
            self.rect.top = dist_after_coll
            self.movement_vec[1] *= -1
        elif self.rect.bottom + dy >= height: 
            print("Butt", self.rect.bottom)
            # The distance after the collision must be the overflowing distance beyond the border.
            # I.e. the y-position of the ball after the collision on y=height is difference between the height and the new center y-position.
            # (total y-distance = (height - rect.center[1]) [-> distance until y=0] + (movement_vec[1] - height) [-> distance after y=0])
            dist_after_coll = 2*height - (self.rect.bottom + dy)
            self.rect.bottom = dist_after_coll
            self.movement_vec[1] *= -1

        self.rect.center += self.movement_vec
        #-----
        #|   |
        #| x |
        #|   |
        #-----


class Engine:
    def __init__(self, ball : Ball, paddles : pg.sprite.Group, print_debug=False):
        self.__print_debug = print_debug
        if print_debug: print("\rBuilding engine...")
        self.__state_id = 0
        self.__playing = False
        self.__screen_size = (1280, 720)
        self.__fps = 60
        self.__master_volume = 100
        self.__sound_volume = 100
        self.__music_volume = 100
        #self.read_options_file()

        pg.init()
        self.__screen = pg.display.set_mode(self.__screen_size)
        self.__mouse_pos = pg.mouse.get_pos()
        self.__clock = pg.time.Clock()
        self.__dt = self.__clock.tick(self.__fps) / 1000
        self.__ball = ball
        self.__paddles = paddles
        self.__sprites = paddles.copy()
        self.__sprites.add(ball)
        pg.key.set_repeat(int(self.__dt * 1000))
        pg.display.set_caption("engine")
        self.__playing = True
        if print_debug: print("\rBuilding successful!")

    def __quit(self):
        if self.__print_debug: print("Closing engine")
        pg.quit()
        sys.exit()

    def get_screen_size(self):
        return self.__screen_size

    def add_sprite(self, new_sprite : pg.sprite.Sprite):
        self.__sprites.add(new_sprite)
        
    def draw(self):
        self.__screen.fill((10,100,10))
        self.__sprites.draw(self.__screen)
        pg.display.flip()

        """
        Updates the game state after each frame transpires  
        """    
    def update(self):
        #to be called every frame of the game
        if self.__state_id == 0: # Playing state
            self.__paddles.update()
            self.__ball.update()
            if self.__ball.score != 0: self.__state_id = 1
        elif self.__state_id == 1: # Evaluation phase for ai agent
            # Let ai update itself, something, blabla
            self.__state_id = 0

    def events(self):
        for event in pg.event.get():
            if event.type == pg.QUIT:
                self.__playing = False
            if event.type == pg.KEYDOWN:
                if event.key == pg.K_ESCAPE:
                    self.__playing = False
                if event.key == pg.K_0:
                    print(0)
        
    def run(self):
        if self.__print_debug: print("Engine running...")
        while self.__playing:
            try:
                self.__dt = self.__clock.tick(self.__fps) / 1000
                self.events()
                self.update()
                self.draw()
            except Exception:
                trace.print_exc()
                self.__playing = False
        self.__quit()

def main():
    paddles = pg.sprite.Group()
    paddleL = Paddle(720, pg.math.Vector2(0, 360), paddles)
    paddleR = Paddle(720, pg.math.Vector2(1280, 360), paddles)
    ball = Ball(paddles, pg.math.Vector2(1280, 720), pg.math.Vector2(640, 360))
    pong = Engine(ball, paddles, True)
    while True:
        pong.run()
               
if __name__ == "__main__":  
    main() 