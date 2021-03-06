#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import division
from __future__ import print_function
import sys
import os
from vizdoom import *
import tensorflow as tf
import itertools as it
from random import sample, randint, random
from time import time, sleep
import numpy as np
from tqdm import tqdm
import replay_memory
import network_double
import agent_dqn
import math
import moviepy.editor as mpy

# Q-learning settings
learning_rate = 0.0025
discount_factor= 0.99
resolution = (30, 45, 1)
n_epoch = 10
steps_per_epoch = 1000
testepisodes_per_epoch = 5
config_file_path = "./config/simpler_basic.cfg"
ckpt_path = "./model/"
freq_copy = 30
frame_repeat = 4
capacity = 10**4
batch_size = 64

sleep_time = 0.028

save_gif = True

# Creates and initializes ViZDoom environment.
def initialize_vizdoom(config_file_path):
    print("Initializing doom...")
    game = DoomGame()
    game.load_config(config_file_path)
    game.set_window_visible(True)
    game.set_mode(Mode.ASYNC_PLAYER)
    game.set_screen_format(ScreenFormat.GRAY8)
    #game.set_screen_format(ScreenFormat.CRCGCB)
    game.set_screen_resolution(ScreenResolution.RES_640X480)
    game.init()
    print("Doom initialized.")
    return game

def make_gif(images,fname,duration=2):

    def make_frame(t):
        try:
            x = images[int(len(images)/duration*t)]
        except:
            x = images[-1]

        return x.astype(np.uint8)

    clip = mpy.VideoClip(make_frame,duration=duration)
    clip.write_gif(fname, fps=len(images)/duration,verbose=False)


if __name__ == "__main__":
    args = sys.argv
    game = initialize_vizdoom(config_file_path)

    n_actions = game.get_available_buttons_size()
    actions = np.eye(n_actions,dtype=np.int32).tolist()
    replay_memory = replay_memory.ReplayMemory(resolution,capacity)

    session = tf.Session()
    network = network_double.network_simple(session,resolution,n_actions,learning_rate)

    session.run(tf.global_variables_initializer())

    agent = agent_dqn.agent_dqn(network,replay_memory,actions,resolution,discount_factor,learning_rate,frame_repeat,batch_size, freq_copy)

    agent.restore_model(args[1])

    frames = []

    for step in range(testepisodes_per_epoch):

        game.new_episode()
        while not game.is_episode_finished():
            s1 = game.get_state().screen_buffer
            frames.append(s1)
            best_action_index = agent.get_best_action(s1)

            game.make_action(actions[best_action_index])

            for _ in range(frame_repeat):
                if not game.is_episode_finished():
                    s1 = game.get_state().screen_buffer
                    frames.append(s1)
                game.advance_action()
            
            sleep(sleep_time)

        print("total:", game.get_total_reward())


    if save_gif == True:
        images = np.array(frames)
        print("saving gif...")
        filename, _ = os.path.splitext(os.path.basename(args[1]))
        make_gif(images,"./demonstration_" + filename + ".gif",duration=len(images)*0.05)

    game.close()