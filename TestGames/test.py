from ale_python_interface import ALEInterface
import numpy as np
import cv2
from random import randrange
import os
import sys

class Atari:
    def __init__(self):
        self.ale = ALEInterface()
        self.max_frames_per_episode = self.ale.getInt(b"max_num_frames_per_episode")
        self.ale.setInt(b"random_seed",123)
        self.ale.setInt(b"frame_skip",4)

        USE_SDL = True
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
        dirROM = os.path.join(os.getcwd(),'../roms/frostbite.bin')
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



# -----------------------------
# File: Deep Q-Learning Algorithm
# Author: Flood Sung
# Date: 2016.3.21
# -----------------------------

import tensorflow as tf
import numpy as np
import random
from collections import deque
import os
# parameter 4 fix problem of pause
# Hyper Parameters:
FRAME_PER_ACTION = 1
GAMMA = 0.95 # decay rate of past observations
OBSERVE = 50000 # timesteps to observe before training
EXPLORE = 1000000 # frames over which to anneal epsilon
FINAL_EPSILON = 0.1#0.001 # final value of epsilon
INITIAL_EPSILON = 1.0#0.01 # starting value of epsilon
REPLAY_MEMORY = 400000 # number of previous transitions to remember
BATCH_SIZE = 32 # size of minibatch
UPDATE_TIME = 10000

class BrainDQN:

    def __init__(self,actions):
        # init replay memory
        self.replayMemory = deque()
        # self.gameProp = gameprops
        # init some parameters
        self.timeStep = 0
        self.epsilon = INITIAL_EPSILON
        self.actions = actions
        # init Q network
        self.stateInput,self.QValue,self.W_conv1,self.b_conv1,self.W_conv2,self.b_conv2,self.W_conv3,self.b_conv3,self.W_fc1,self.b_fc1,self.W_fc2,self.b_fc2 = self.createQNetwork()

        # init Target Q Network
        self.stateInputT,self.QValueT,self.W_conv1T,self.b_conv1T,self.W_conv2T,self.b_conv2T,self.W_conv3T,self.b_conv3T,self.W_fc1T,self.b_fc1T,self.W_fc2T,self.b_fc2T = self.createQNetwork()

        self.copyTargetQNetworkOperation = [self.W_conv1T.assign(self.W_conv1),self.b_conv1T.assign(self.b_conv1),self.W_conv2T.assign(self.W_conv2),self.b_conv2T.assign(self.b_conv2),self.W_conv3T.assign(self.W_conv3),self.b_conv3T.assign(self.b_conv3),self.W_fc1T.assign(self.W_fc1),self.b_fc1T.assign(self.b_fc1),self.W_fc2T.assign(self.W_fc2),self.b_fc2T.assign(self.b_fc2)]

        self.createTrainingMethod()

        # saving and loading networks
        self.saver = tf.train.Saver()
        self.session = tf.InteractiveSession()
        self.session.run(tf.global_variables_initializer())

        if False:
            checkpoint = tf.train.get_checkpoint_state('./saved_networks_' + self.gameProp.namegame)
        else:
            checkpoint = tf.train.get_checkpoint_state('./saved_networks')

        if checkpoint and checkpoint.model_checkpoint_path:
            self.saver.restore(self.session, checkpoint.model_checkpoint_path)
            print("Successfully loaded:", checkpoint.model_checkpoint_path)
        else:
            print("Could not find old network weights")


    def createQNetwork(self):
        # network weights
        W_conv1 = self.weight_variable([8,8,4,32])
        b_conv1 = self.bias_variable([32])

        W_conv2 = self.weight_variable([4,4,32,64])
        b_conv2 = self.bias_variable([64])

        W_conv3 = self.weight_variable([3,3,64,64])
        b_conv3 = self.bias_variable([64])

        W_fc1 = self.weight_variable([3136,512])
        b_fc1 = self.bias_variable([512])

        W_fc2 = self.weight_variable([512,self.actions])
        b_fc2 = self.bias_variable([self.actions])

        # input layer

        stateInput = tf.placeholder("float",[None,84,84,4])

        # hidden layers
        h_conv1 = tf.nn.relu(self.conv2d(stateInput,W_conv1,4) + b_conv1)
        #h_pool1 = self.max_pool_2x2(h_conv1)

        h_conv2 = tf.nn.relu(self.conv2d(h_conv1,W_conv2,2) + b_conv2)

        h_conv3 = tf.nn.relu(self.conv2d(h_conv2,W_conv3,1) + b_conv3)
        h_conv3_shape = h_conv3.get_shape().as_list()
        print("dimension:",h_conv3_shape[1]*h_conv3_shape[2]*h_conv3_shape[3])
        h_conv3_flat = tf.reshape(h_conv3,[-1,3136])
        h_fc1 = tf.nn.relu(tf.matmul(h_conv3_flat,W_fc1) + b_fc1)

        # Q Value layer
        QValue = tf.matmul(h_fc1,W_fc2) + b_fc2

        return stateInput,QValue,W_conv1,b_conv1,W_conv2,b_conv2,W_conv3,b_conv3,W_fc1,b_fc1,W_fc2,b_fc2

    def copyTargetQNetwork(self):
        self.session.run(self.copyTargetQNetworkOperation)

    def createTrainingMethod(self):
        self.actionInput = tf.placeholder("float",[None,self.actions])
        self.yInput = tf.placeholder("float", [None])
        Q_Action = tf.reduce_sum(tf.multiply(self.QValue, self.actionInput), reduction_indices = 1)
        self.cost = tf.reduce_mean(tf.square(self.yInput - Q_Action))
        self.trainStep = tf.train.RMSPropOptimizer(0.00025,0.99,0.0,1e-6).minimize(self.cost)


    def trainQNetwork(self):


        # Step 1: obtain random minibatch from replay memory
        minibatch = random.sample(self.replayMemory,BATCH_SIZE)
        state_batch = [data[0] for data in minibatch]
        action_batch = [data[1] for data in minibatch]
        reward_batch = [data[2] for data in minibatch]
        nextState_batch = [data[3] for data in minibatch]

        # Step 2: calculate y
        y_batch = []
        QValue_batch = self.QValueT.eval(feed_dict={self.stateInputT:nextState_batch})
        for i in range(0,BATCH_SIZE):
            terminal = minibatch[i][4]
            if terminal:
                y_batch.append(reward_batch[i])
            else:
                y_batch.append(reward_batch[i] + GAMMA * np.max(QValue_batch[i]))

        self.trainStep.run(feed_dict={
            self.yInput : y_batch,
            self.actionInput : action_batch,
            self.stateInput : state_batch
            })

        # save network every 100000 iteration
        if self.timeStep % 10000 == 0:
            self.saver.save(self.session, 'saved_networks/' + 'network' + '-dqn', global_step = self.timeStep)

        if self.timeStep % UPDATE_TIME == 0:
            self.copyTargetQNetwork()


    def setPerception(self,nextObservation,action,reward,terminal):
        newState = np.append(nextObservation,self.currentState[:,:,1:],axis = 2)
        self.replayMemory.append((self.currentState,action,reward,newState,terminal))
        print( 'len(replayMemory): ', len( self.replayMemory ) )
        # print( 'timeStep: ', self.timeStep )
        if len(self.replayMemory) > REPLAY_MEMORY:
            self.replayMemory.popleft()
        if self.timeStep > OBSERVE:
            # Train the network
            self.trainQNetwork()

        # print info
        state = ""
        if self.timeStep <= OBSERVE:
            state = "observe"
        elif self.timeStep > OBSERVE and self.timeStep <= OBSERVE + EXPLORE:
            state = "explore"
        else:
            state = "train"

        print("TIMESTEP", self.timeStep, "/ STATE", state, \
        "/ EPSILON", self.epsilon, "/ REWARD", reward)

        self.currentState = newState
        self.timeStep += 1
    def setPerceptionTest(self, nextObservation, action, reward, terminal):
        newState = np.append(nextObservation,self.currentState[:,:,1:],axis = 2)
        #self.replayMemory.append((self.currentState,action,reward,newState,terminal))
        self.currentState = newState
        self.timeStep += 1

    def getAction(self):
        QValue = self.QValue.eval(feed_dict= {self.stateInput:[self.currentState]})[0]
        action = np.zeros(self.actions)
        action_index = 0
        if self.timeStep % FRAME_PER_ACTION == 0:
            if random.random() <= self.epsilon:
                action_index = random.randrange(self.actions)
                action[action_index] = 1
            else:
                action_index = np.argmax(QValue)
                action[action_index] = 1
        else:
            action[0] = 1 # do nothing

        # change episilon
        if self.epsilon > FINAL_EPSILON and self.timeStep > OBSERVE:
            self.epsilon -= (INITIAL_EPSILON - FINAL_EPSILON)/EXPLORE

        return action

    def getActionTest(self):
        QValue = self.QValue.eval(feed_dict= {self.stateInput:[self.currentState]})[0]
        action = np.zeros(self.actions)
        action_index = 0
        if self.timeStep % FRAME_PER_ACTION == 0:
                action_index = np.argmax(QValue)
                action[action_index] = 1
        else :
            action[0] = 1 # do nothing

        return action

    def setInitState(self,observation):
        self.currentState = np.stack((observation, observation, observation, observation), axis = 2)

    def weight_variable(self,shape):
        initial = tf.truncated_normal(shape, stddev = 0.01)
        return tf.Variable(initial)
	
    def bias_variable(self,shape):
        initial = tf.constant(0.01, shape = shape)
        return tf.Variable(initial)

    def conv2d(self,x, W, stride):
        return tf.nn.conv2d(x, W, strides = [1, stride, stride, 1], padding = "VALID")

    def max_pool_2x2(self,x):
        return tf.nn.max_pool(x, ksize = [1, 2, 2, 1], strides = [1, 2, 2, 1], padding = "SAME")


atari = Atari()
actions = len(atari.legal_actions)
brain = BrainDQN(actions)

def preprocess(observation, perprocessFrom, preprocessTo):

	observation = cv2.cvtColor(cv2.resize(observation, (84, 110)), cv2.COLOR_BGR2GRAY)
	#kernel = np.ones((3,3),np.uint8)
	#observation = cv2.dilate(observation,kernel,iterations = 1)
	
	observation = observation[perprocessFrom:preprocessTo,:]
	#if crop_above:
		#observation = observation[26:110,:]
	#	observation = observation[18:102,:]  # Just Pong configs
	#else:
	#	observation = observation[0:84,:]
	#ret, observation = cv2.threshold(observation,100,255,cv2.THRESH_BINARY)

	#cv2.waitKey(0)
	return np.reshape(observation,(84,84,1))

# Step 3: play game
# Step 3.1: obtain init state
action0 = np.array([1,0,0,0])  # do nothing
observation0, reward0, terminal = atari.next(action0)
cv2.imwrite("imrgb.png", observation0);
observation0 = cv2.cvtColor(cv2.resize(observation0, (84, 110)), cv2.COLOR_BGR2GRAY)
observation0 = observation0[16:100,:]
cv2.imwrite("imgray.png", observation0);
#ret, observation0 = cv2.threshold(observation0,1,255,cv2.THRESH_BINARY)
cv2.imwrite("imthres.png", observation0);
brain.setInitState(observation0)
for i in range(100):
    action = brain.getAction()
    nextObservation,reward,terminal = atari.next(action)
    #cv2.imwrite("imrgb" + str(i+1) + ".png", nextObservation);
    nextObservation = preprocess(nextObservation, 16, 100)
    cv2.imwrite("imgray" + str(i+1) + ".png", nextObservation);
    brain.setPerception(nextObservation,action,reward,terminal)
