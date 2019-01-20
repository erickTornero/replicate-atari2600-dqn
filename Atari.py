from ale_python_interface import ALEInterface
import numpy as np
import cv2
from random import randrange
from configurations import *
import os
import sys

class Atari:
	def __init__(self,gameProps):
		self.gameProp = gameProps
		self.ale = ALEInterface()
		self.max_frames_per_episode = self.ale.getInt(b"max_num_frames_per_episode")
		self.ale.setInt(b"random_seed",123)
		self.ale.setInt(b"frame_skip",4)

		USE_SDL = gameProps.isTesting
		if USE_SDL:
		  if sys.platform == 'darwin':
		    import pygame
		    pygame.init()
		    self.ale.setBool(b'sound', False) # Sound doesn't work on OSX
		  elif sys.platform.startswith('linux'):
		    self.ale.setBool(b'sound', True)
		  self.ale.setBool(b'display_screen', True)

		# Define direction of ROM
		#print( 'cwd: ', os.getcwd() )
		dirROM = os.path.join(os.getcwd(), gameProps.rompath + gameProps.namegame+'.bin')
		#dirROM = os.path.join( os.getcwd(), "/home/erick/Escritorio/eerr/wilbermaq/mishi/DQN-Atari-Tensorflow/roms/pong.bin" )
		#print( 'dirROM: ', dirROM )
		rom_file = str.encode(dirROM)
		self.ale.loadROM(rom_file)
		self.screen_width,self.screen_height = self.ale.getScreenDims()
		self.legal_actions = self.ale.getMinimalActionSet()
		self.action_map = dict()
		for i in range(len(self.legal_actions)):
			self.action_map[self.legal_actions[i]] = i
		#print len(self.legal_actions)
		#self.windowname = rom_name
		#cv2.startWindowThread()
		#cv2.namedWindow(rom_name)

	def get_image(self):
		numpy_surface = np.zeros(self.screen_height*self.screen_width*3, dtype=np.uint8)
		self.ale.getScreenRGB(numpy_surface)
		image = np.reshape(numpy_surface, (self.screen_height, self.screen_width, 3))
		return image

	def newGame(self):
		self.ale.reset_game()
		return self.get_image()

	def next(self, action):
		reward = self.ale.act(self.legal_actions[np.argmax(action)])
		nextstate = self.get_image()

		#cv2.imshow(self.windowname,nextstate)
		term = self.ale.game_over()
		if term:
			self.newGame()
		#print "reward %d" % reward
		return nextstate, reward, term
