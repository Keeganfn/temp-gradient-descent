#!/usr/bin/python3

from numpy import pi, cos, sin
# from multiprocessing.dummy import current_process

import pybullet as p

import numpy as np
import time

from modified_mojograsp_classes import UpdatedTwoFingerGripper
from modified_mojograsp_classes import UpdatedObjectBase
import helper_functions as HF
logger = HF.colored_logging(name="gradient_descent")


class GradientDescent():

    def __init__(self, hand: UpdatedTwoFingerGripper, finger: str, contact_in_distal: list, goal_contact_pose):
        """Initialize GradientDescent solver. The goal with this solver is take the current contact point between the distal finger and the object, finger config, and

        Args:
            hand (UpdatedTwoFingerGripper): Hand object used in the simulator
            finger (str): the name of the finger that the joint angles are being solved for.
            contact_in_distal (list): [x,y,z] location of contact between current finger and object in the distal link frame
            goal_contact_pose (_type_): _description_
        """
        self.MAX_ERROR = 0.0001  # meters
        self.MAR_STEPSIZE = .005
        self.EXIT_CONDITION_LOOP = 20  # The number of full loops the gradient descent will do until it determines it can't move
        self.STEP_SIZE = pi/75  # radients
        self.REDUCE_STEP_SIZE = 0.25
        self.hand = hand
        self.finger = finger
        self.contact_in_distal = contact_in_distal
        self.goal_contact_pose = goal_contact_pose
        logger.debug(f'\ncontact_in_distal: {self.contact_in_distal}  \ngoal_contact_pose: {self.goal_contact_pose}')

        self.starting_joint_angles = hand.kinematics.joint_angles
        self.new_joint_angles = self.starting_joint_angles.copy()
        self.palm_to_world = np.identity(4)
        self.palm_to_world[0:3, 3] = hand.setup_param["position"]
        self.palm_to_world[0:3, 0:3] = np.around(np.reshape(
            p.getMatrixFromQuaternion(hand.setup_param["orientation"]), (3, 3)), 5)
        logger.debug(f'palm to world transform: \n{self.palm_to_world}')

    def gradient_calculator(self):
        # update_joint_angles = self.new_joint_angles.copy()
        # c = previous_delta = self.delta_calculator(update_joint_angles)
        # g = c[0] - self.goal_contact_pose[0]
        # g2 = c[1] - self.goal_contact_pose[1]
        # self.goal_contact_pose[0] -= g
        # self.goal_contact_pose[1] -= g2
        # print(self.finger)
        # print(self.starting_joint_angles)
        # update_joint_angles = self.hand.get_joint_angles()
        # print(update_joint_angles)
        # if self.finger == "finger0":
        #     joints = list(p.calculateInverseKinematics(self.hand.id, 1, self.goal_contact_pose))
        #     for i in range(0, 2):
        #         if joints[i] > update_joint_angles[i]:
        #             diff = min(joints[i] - update_joint_angles[i], self.MAR_STEPSIZE)
        #             update_joint_angles[i] = update_joint_angles[i] + diff
        #         else:
        #             diff = min(update_joint_angles[i] - joints[i], self.MAR_STEPSIZE)
        #             update_joint_angles[i] = update_joint_angles[i] - diff
        #     self.starting_joint_angles[0] = update_joint_angles[0]
        #     self.starting_joint_angles[1] = update_joint_angles[1]
        # else:
        #     joints = list(p.calculateInverseKinematics(self.hand.id, 3, self.goal_contact_pose))
        #     for i in range(2, 4):
        #         if joints[i] > update_joint_angles[i]:
        #             diff = min(joints[i] - update_joint_angles[i], self.MAR_STEPSIZE)
        #             self.update_joint_angles[i] = update_joint_angles[i] + diff
        #         else:
        #             diff = min(update_joint_angles[i] - joints[i], self.MAR_STEPSIZE)
        #             update_joint_angles[i] = update_joint_angles[i] - diff
        #     self.starting_joint_angles[2] = update_joint_angles[2]
        #     self.starting_joint_angles[3] = update_joint_angles[3]
        #     # j2 = []
        #     # j2.append(joints[2])
        #     # j2.append(joints[3])
        #     # j2.append(joints[0])
        #     # j2.append(joints[1])
        #     # joints = j2

        # print(update_joint_angles)
        # print(joints)
        # return update_joint_angles

        # print("IK: ", joints)

        gradient_test_val = 0.0002
        update_joint_angles = self.new_joint_angles
        previous_delta = self.delta_calculator(update_joint_angles)
        counter_outer = 0
        while True:

            if counter_outer >= self.EXIT_CONDITION_LOOP:
                return False

            # logger.debug(f'previous_delta:\n{previous_delta}')
            if previous_delta < self.MAX_ERROR:
                #logger.debug('going to next finger')
                break

            for joint_index in self.hand.fingers[self.finger]['index_values']:
                step_size = self.STEP_SIZE
                # very small step to see the direction to move in.
                update_joint_angles[joint_index] += gradient_test_val
                direction_cal = self.delta_calculator(update_joint_angles)
                # logger.debug(f'joint: {joint_index}\ndirection_cal: {direction_cal}')
                if direction_cal < previous_delta:
                    step_size *= 1
                    # logger.debug(f'increase the angle')
                else:
                    step_size *= -1
                update_joint_angles[joint_index] += gradient_test_val
                # logger.debug(f'decrease the angle')
                #step_joint_angles = update_joint_angles.copy()
                counter = 0
                while True:
                    if counter >= 5:  # if one of the links can't improve the delta skip it
                        break
                    #step_joint_angles[joint_index] = update_joint_angles[joint_index] + step_size
                    update_joint_angles[joint_index] += step_size
                    updated_delta = self.delta_calculator(update_joint_angles)
                    # logger.debug(f'updated_delta: {updated_delta}')
                    if updated_delta < previous_delta:
                        # logger.debug(f'\nprevious_delta:{previous_delta}\nupdated_delta: {updated_delta}')
                        previous_delta = updated_delta
                        break
                    else:
                        #step_joint_angles = update_joint_angles.copy()
                        update_joint_angles[joint_index] -= step_size
                        step_size *= self.REDUCE_STEP_SIZE
                    counter += 1

                #update_joint_angles = step_joint_angles.copy()
            counter_outer += 1
        #self.new_joint_angles = update_joint_angles

        #logger.debug(f'\nnew_angles: {self.new_joint_angles}')
        #print("GRADIENT: ", self.new_joint_angles)
        return update_joint_angles

    def delta_calculator(self, joint_angles: list) -> float:
        transform = self.hand.kinematics.calculate_forward_kinematics(joint_angles)
        contact_in_world = np.around(np.matmul(
            self.palm_to_world, np.matmul(
                transform[self.finger],
                self.contact_in_distal)),
            10)
        delta_vector = contact_in_world[0:2] - self.goal_contact_pose[:2]
        # logger.debug(f"\ncontact in world: \n{contact_in_world}\ngoal_contact: {self.goal_contact_pose}\nDelta vector:\n{delta_vector}, {np.linalg.norm(delta_vector)}")
        return np.linalg.norm(delta_vector)
        # return contact_in_world
