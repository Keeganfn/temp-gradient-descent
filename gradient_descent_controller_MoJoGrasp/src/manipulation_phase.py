#!/usr/bin/python3
from mojograsp.simcore import episode
import pybullet as p
from mojograsp.simcore.phase import Phase

from modified_mojograsp_classes import UpdatedObjectBase, UpdatedTwoFingerGripper

from mojograsp.simcore.state import State
from mojograsp.simcore.reward import Reward
from mojograsp.simcore.action import Action
import hand_controller
from math import isclose
import helper_functions as HF
import numpy as np
import json
import pickle as pkl

logger = HF.colored_logging(name="manipulation_phase")


class AstriskManipulation(Phase):

    def __init__(
            self, hand: UpdatedTwoFingerGripper, obj: UpdatedObjectBase, x_goals, y_goals, state: State, action: Action,
            reward: Reward):
        self.name = "manipulation"
        self.hand = hand
        self.obj = obj

        self.state = state
        self.action = action
        self.reward = reward
        self.terminal_step = 400
        self.timestep = 0
        self.episode = 0
        self.x_goals = x_goals
        self.y_goals = y_goals
        self.goal_position = None
        self.angles_list = []
        self.angles_name = ["N", "NW", "W", "SW", "S", "SE", "E", "NE"]

    def setup(self):
        self.controller = hand_controller.HandController(self.hand, self.obj)
        self.timestep = 0
        self.controller.num_contact_loss = 0
        logger.info(
            f'episode #: {self.episode}\nCube Goal Position:\nx: {self.x_goals[self.episode]}\ny: {self.y_goals[self.episode]}')
        self.goal_position = [float(self.x_goals[self.episode]),
                              float(self.y_goals[self.episode]), 0]
        self.controller.set_goal_position(self.goal_position)

    def pre_step(self):

        int_val = self.controller.get_next_action()
        if int_val == False:
            pass
        else:
            self.target = int_val

        self.action.set_action(self.target)
        self.state.set_state()

    def execute_action(self):
        p.setJointMotorControlArray(self.hand.id, jointIndices=self.hand.get_joint_numbers(),
                                    controlMode=p.POSITION_CONTROL, targetPositions=self.target)
        self.timestep += 1

    def post_step(self):
        self.angles_list.append(self.hand.get_joint_angles())
        if self.reward == None:
            pass
        else:
            self.reward.set_reward(self.goal_position, self.obj)

    def record(self):
        temp = np.array(self.angles_list)
        save_dict = {
            "joint_1": temp[:, 0],
            "joint_2": temp[:, 1],
            "joint_3": temp[:, 2],
            "joint_4": temp[:, 3]}
        label = "data/angles_" + self.angles_name[self.episode] + ".pkl"
        with open(label, "wb+") as file:
            pkl.dump(save_dict, file)
        self.angles_list = []
        with open(label, 'rb') as f2:
            diff_r = pkl.load(f2)
            print(diff_r)

    def exit_condition(self) -> bool:
        if self.timestep > self.terminal_step:
            logger.warning("Time step limit reached\n\n")
            self.record()
            return True
        elif self.controller.exit_condition():
            logger.warning("Controller exit condition\n\n")
            self.record()
            return True
        return False

    def next_phase(self) -> str:
        self.episode += 1
        return None
