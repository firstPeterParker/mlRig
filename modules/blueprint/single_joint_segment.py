'''

This module is for creating a single joint segment

'''
import maya.cmds as cmds
import os
import system.blueprint as blueprint_mod
reload(blueprint_mod)

CLASS_NAME = "SingleJointSegment"
TITLE = "Single Joint Segment"
DESCRIPTION = "Creates 2 joints with controls for orientation and rotation order. Ideal Use: Clavicle/Shoulder"
ICON = os.environ["mlrig_tool"]+"/icons/_singleJointSeg.xpm"

class SingleJointSegment(blueprint_mod.Blueprint):
	def __init__(self, user_specified_name):

		joint_info = [
							["root_joint", [0.0, 0.0, 0.0]],
							["end_joint", [4.0, 0.0, 0.0]]
						]

		blueprint_mod.Blueprint.__init__(self, CLASS_NAME, user_specified_name, joint_info)

	def install_custom(self, joints):

		self.create_ori_ctrl(joints[0], joints[1])

	def lock_phase1(self):

		joint_pos = []
		joint_ori_values = []
		joint_rotation_orders = []

		joints = self.get_joints()

		for joint in joints:
			joint_pos.append(cmds.xform(	joint,
											q=True,
											worldSpace=True,
											translation=True
										)
							)

		clean_parent = self.module_namespace+":joints_grp"
		ori_info = self.ori_ctrl_joint_get_ori(joints[0], clean_parent)
		cmds.delete(ori_info[1])
		
		joint_ori_values.append(ori_info[0])
		joint_ories = (joint_ori_values, None)

		joint_rotation_orders.append(cmds.getAttr(joints[0]+".rotateOrder"))

		joint_pref_angle = None
		hook_obj = None
		root_trans = False

		module_info = (
							joint_pos,
							joint_ories,
							joint_rotation_orders,
							joint_pref_angle,
							hook_obj,
							root_trans
						)

		return module_info

	def ui_custom(self):

		joints = self.get_joints()
		self.create_rotation_order_ui_control(joints[0])