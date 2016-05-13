'''

Module A

'''
import os
import maya.cmds as cmds
import system.utils as utils
reload(utils)

CLASS_NAME = "ModuleA"
TITLE = "Module A"
DESCRIPTION = "This is a description for module A"
ICON = os.environ["mlrig_tool"]+"/icons/_hand.xpm"

class ModuleA():
	def __init__(self, user_specified_name):
		
		self.module_name = CLASS_NAME
		self.user_specified_name = user_specified_name

		self.module_namespace = self.module_name+"__"+self.user_specified_name

		self.container_name = self.module_namespace+":module_container"

		self.joint_info = [ ["root_joint", [0.0, 0.0, 0.0]], ["end_joint", [4.0, 0.0, 0.0]] ]

	def install(self):
		
		cmds.namespace(setNamespace = ":")
		cmds.namespace(add=self.module_namespace)

		self.joints_grp = cmds.group(empty=True, name=self.module_namespace+":joint_grp")
		self.module_grp = cmds.group(self.joints_grp, name=self.module_namespace+":module_grp")

		cmds.container(name=self.container_name, addNode=self.module_grp, ihb=True)

		cmds.select(clear=True)

		index = 0 
		joints = []

		for joint in self.joint_info:
			
			joint_name = joint[0]
			joint_pos = joint[1]
			parent_joint = ""

			if index > 0:
				parent_joint = self.module_namespace+":"+self.joint_info[index-1][0]
				cmds.select(parent_joint, replace=True)

			joint_name_full = cmds.joint(n=self.module_namespace+":"+joint_name, p=joint_pos)
			joints.append(joint_name_full)

			utils.add_node_to_container(self.container_name, joint_name_full)

			cmds.container(self.container_name, edit=True, publishAndBind=[joint_name_full+".rotate", joint_name+"_R"])
			cmds.container(self.container_name, edit=True, publishAndBind=[joint_name_full+".rotateOrder", joint_name+"_rotateOrder"])


			if index > 0:
				cmds.joint(parent_joint, edit=True, orientJoint="xyz", sao="yup")

			index += 1

		cmds.parent(joints[0], self.joints_grp, absolute=True)

		trans_ctrl = []

		for joint in joints:
			trans_ctrl.append(self.create_trans_ctrl_at_joint(joint))

		root_joint_point_con = cmds.pointConstraint(trans_ctrl[0], joints[0], maintainOffset=False, name=joints[0]+"_pointConstraint")

		utils.add_node_to_container(self.container_name, root_joint_point_con)

		# Set up stretchy joint segment

		for index in range(len(joints)-1):
			self.setup_stretchy_jnt_segment(joints[index], joints[index+1])

		utils.force_scene_update()

		cmds.lockNode(self.container_name, lock=True, lockUnpublished=True)

	def create_trans_ctrl_at_joint(self, joint):
		
		pos_ctrl_file = os.environ["mlrig_tool"]+"/controlobjects/blueprint/translation_control.ma"
		cmds.file(pos_ctrl_file, i=True)

		container = cmds.rename("translation_control_container", joint+"_translation_control_container")
		
		utils.add_node_to_container(self.container_name, container)

		for node in cmds.container(container, q=True, nodeList=True):
			cmds.rename(node, joint+"_"+node, ignoreShape=True)

		control = joint+"_translation_control"

		joint_pos = cmds.xform(joint, q=True, worldSpace=True, translation=True)
		cmds.xform(control, worldSpace=True, absolute=True, translation=joint_pos)

		nice_name = utils.strip_leading_namespace(joint)[1]
		attr_name = nice_name+"_T"

		cmds.container(container, edit=True, publishAndBind=[control+".translate", attr_name])
		cmds.container(self.container_name, edit=True, publishAndBind=[container+"."+attr_name, attr_name])

		return control

	def get_trans_ctrl(self, joint_name):

		return joint_name+"_translation_control"

	def setup_stretchy_jnt_segment(self, parent_joint, child_joint):
		parent_trans_control = self.get_trans_ctrl(parent_joint)
		child_trans_control = self.get_trans_ctrl(child_joint)

		pole_vector_loc = cmds.spaceLocator(n=parent_trans_control+"_poleVectorLocator")[0]
		pole_vector_loc_grp = cmds.group(pole_vector_loc, n=pole_vector_loc+"_parentConstraintGrp")

		cmds.parent(pole_vector_loc_grp, self.module_grp, absolute=True)
		parent_con = cmds.parentConstraint(parent_trans_control, pole_vector_loc_grp, maintainOffset=False)[0]

		cmds.setAttr(pole_vector_loc+".visibility", 0)
		cmds.setAttr(pole_vector_loc+".ty", -0.5)

		ik_nodes = utils.basic_stretchy_ik(parent_joint, child_joint, container=self.container_name, lock_min_len=False, pole_vector_obj=pole_vector_loc, scale_correct_atrr=None)
		ik_handle = ik_nodes["ik_handle"]
		root_loc = ik_nodes["root_loc"]
		end_loc = ik_nodes["end_loc"]

		child_point_con = cmds.pointConstraint(child_trans_control, end_loc, maintainOffset=False, n=end_loc+"_pointConstraint")[0]

		utils.add_node_to_container(self.container_name, [pole_vector_loc_grp, parent_con, child_point_con], ihb=True)

		for node in [ik_handle, root_loc, end_loc]:
			cmds.parent(node, self.joints_grp, absolute=True)
			cmds.setAttr(node+".visibility", 0)

