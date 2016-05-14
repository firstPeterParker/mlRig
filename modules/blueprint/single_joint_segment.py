'''

This module is for creating a single joint segment

'''
import maya.cmds as cmds
import os
import system.blueprint as blueprint_mod
reload(blueprint_mod)

CLASS_NAME = "SingleJointSegment"
TITLE = "Single Joint Segment"
DESCRIPTION = "Creates 2 joints with control for it's joint's orientation and rotation order. Ideal Use: Clavicle/Shoulder"
ICON = os.environ["mlrig_tool"]+"/icons/_singleJointSeg.xpm"

class SingleJointSegment(blueprint_mod.Blueprint):
	def __init__(self, user_specified_name):

		joint_info = [ ["root_joint", [0.0, 0.0, 0.0]], ["end_joint", [4.0, 0.0, 0.0]] ]

		blueprint_mod.Blueprint.__init__(self, CLASS_NAME, user_specified_name, joint_info)

	def install_custom(self, joints):

		self.create_ori_ctrl(joints[0], joints[1])