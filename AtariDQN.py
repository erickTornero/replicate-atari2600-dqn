import cv2
import sys
sys.path.append("game/")
from Atari import Atari
from BrainDQN_Nature import *
import numpy as np


TEST = False
crop_above = True
# preprocess raw image to 80*80 gray image
def preprocess(observation):

	observation = cv2.cvtColor(cv2.resize(observation, (84, 110)), cv2.COLOR_BGR2GRAY)
	if crop_above:
		#observation = observation[26:110,:]
		observation = observation[18:102,:]  # Just Pong configs
	else:
		observation = observation[0:84,:]
	#ret, observation = cv2.threshold(observation,100,255,cv2.THRESH_BINARY)

	#cv2.waitKey(0)
	return np.reshape(observation,(84,84,1))

def playAtari():
	# Step 1: init BrainDQN
	# Step 2: init Flappy Bird Game
	atari = Atari('breakout.bin')
	actions = len(atari.legal_actions)
	brain = BrainDQN(actions)


	# Step 3: play game
	# Step 3.1: obtain init state
	action0 = np.array([1,0,0,0])  # do nothing
	observation0, reward0, terminal = atari.next(action0)
	observation0 = cv2.cvtColor(cv2.resize(observation0, (84, 110)), cv2.COLOR_BGR2GRAY)
	observation0 = observation0[26:110,:]
	#ret, observation0 = cv2.threshold(observation0,1,255,cv2.THRESH_BINARY)
	brain.setInitState(observation0)
	print(atari.ale.getLegalActionSet())
	limitsameactions = 1000
	action_prev = 0
	counter_actionssame = 0
	# Step 3.2: run the game
	if not TEST:
		while 1!= 0:
			if TEST :
				action = brain.getActionTest()
			else:
				action = brain.getAction()
			nextObservation,reward,terminal = atari.next(action)
			nextObservation = preprocess(nextObservation)
			brain.setPerception(nextObservation,action,reward,terminal)
	else:
		while True:
			total_reward = 0
			while not atari.ale.game_over():
				action = brain.getActionTest()
				nextObservation,reward,terminal = atari.next(action)
				nextObservation = preprocess(nextObservation)
				brain.setPerceptionTest(nextObservation,action,reward,terminal)
				total_reward += reward
				#print(counter_actionssame)
				action_curidx = getActionIdx(action)
				if action_prev == action_curidx:
					counter_actionssame = counter_actionssame + 1
					if counter_actionssame == 100:
						atari.ale.reset_game()
				else:
					counter_actionssame = 0
				action_prev = action_curidx
				counter_actionssame = counter_actionssame + 1
				#if(counter_actionssame % 100 == 0):
				#if(not terminal):
				#	print('terminal')
				#	atari.ale.reset_game()
				#print(atari.ale.game_over())
			print('Episode Ended with score: %d' %(total_reward))
			atari.ale.reset_game()

def getActionIdx(arr):
	i = 0
	for i in range(len(arr)):
		if(arr[i] > 0):
			return i
	return i

def main():
	playAtari()
	"""
	atari = Atari('breakout.bin')
	actions = len(atari.legal_actions)
	brain = BrainDQN(actions)


	# Step 3: play game
	# Step 3.1: obtain init state
	action0 = np.array([1,0,0,0])  # do nothing
	observation0, reward0, terminal = atari.next(action0)
	cv2.imwrite("imrgb.png", observation0);
	observation0 = cv2.cvtColor(cv2.resize(observation0, (84, 110)), cv2.COLOR_BGR2GRAY)
	observation0 = observation0[26:110,:]
	cv2.imwrite("imgray.png", observation0);
	#ret, observation0 = cv2.threshold(observation0,1,255,cv2.THRESH_BINARY)
	cv2.imwrite("imthres.png", observation0);
	brain.setInitState(observation0)
	for i in range(100):
		action = brain.getAction()
		nextObservation,reward,terminal = atari.next(action)
		nextObservation = preprocess(nextObservation)
		cv2.imwrite("imgray" + str(i+1) + ".png", nextObservation);
		brain.setPerception(nextObservation,action,reward,terminal)

	"""
if __name__ == '__main__':
	main()
