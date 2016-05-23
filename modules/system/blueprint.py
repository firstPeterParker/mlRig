'''

This is a Blueprint base class module 

'''
import os
import maya.cmds as cmds
import system.utils as utils
reload(utils)

class Blueprint():
	def __init__(self,module_name,user_specified_name,joint_info):
		
		self.module_name = module_name
		self.user_specified_name = user_specified_name

		self.module_namespace = self.module_name+"__"+self.user_specified_name

		self.container_name = self.module_namespace+":module_container"

		self.joint_info = joint_info

	# Methods intended for overriding by derived classes
	
	def install_custom(self,joints):

		print "install_custom() method is not implemented by derived class"

	def lock_phase1(self):

		return None

	def lock_phase2(self, module_info):

		joint_pos = module_info[0]
		num_joints = len(joint_pos)

		joint_ori = module_info[1]
		ori_with_axis = False
		pure_ori = False

		if joint_ori[0] == None:
			ori_with_axis = True
			joint_ori = joint_ori[1]
		else:
			pure_ori = True
			joint_ori = joint_ori[0]

		num_ori = len(joint_ori)

		joint_rotation_orders = module_info[2]
		num_rotation_orders = len(joint_rotation_orders)

		joint_pref_angle = module_info[3]
		num_pref_angle = 0
		if joint_pref_angle != None:
			num_pref_angle = len(joint_pref_angle)

		# hook_obj = module_info[4]

		root_trans = module_info[5]

		# delete our blueprint controls

		cmds.lockNode(self.container_name, lock=False, lockUnpublished=False)
		cmds.delete(self.container_name)
		cmds.namespace(setNamespace=":")



	# Baseclass Methods 
	
	def install(self):
		
		cmds.namespace(setNamespace = ":")
		cmds.namespace(add=self.module_namespace)

		self.joints_grp = cmds.group(empty=True, name=self.module_namespace+":joints_grp")
		self.hierarchy_grp = cmds.group(empty=True, name=self.module_namespace+":hierarchy_grp")
		self.ori_ctrl_grp = cmds.group(empty=True, name=self.module_namespace+":orientationControls_grp")
		self.module_grp = cmds.group([self.joints_grp, self.hierarchy_grp, self.ori_ctrl_grp], name=self.module_namespace+":module_grp")

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

			cmds.setAttr(joint_name_full+".visibility", 0)

			utils.add_node_to_container(self.container_name, joint_name_full)

			cmds.container(self.container_name, edit=True, publishAndBind=[joint_name_full+".rotate", joint_name+"_R"])
			cmds.container(self.container_name, edit=True, publishAndBind=[joint_name_full+".rotateOrder", joint_name+"_rotateOrder"])


			if index > 0:
				cmds.joint(parent_joint, edit=True, orientJoint="xyz", sao="yup")

			index += 1

		cmds.parent(joints[0], self.joints_grp, absolute=True)

		self.init_module_trans(self.joint_info[0][1])

		trans_ctrl = []

		for joint in joints:
			trans_ctrl.append(self.create_trans_ctrl_at_joint(joint))

		root_joint_point_con = cmds.pointConstraint(trans_ctrl[0], joints[0], maintainOffset=False, name=joints[0]+"_pointConstraint")

		utils.add_node_to_container(self.container_name, root_joint_point_con)

		# Set up stretchy joint segment

		for index in range(len(joints)-1):
			self.setup_stretchy_jnt_segment(joints[index], joints[index+1])

		self.install_custom(joints)

		utils.force_scene_update()

		cmds.lockNode(self.container_name, lock=True, lockUnpublished=True)

	def create_trans_ctrl_at_joint(self,joint):
		
		pos_ctrl_file = os.environ["mlrig_tool"]+"/controlobjects/blueprint/translation_control.ma"
		cmds.file(pos_ctrl_file, i=True)

		container = cmds.rename("translation_control_container", joint+"_translation_control_container")
		
		utils.add_node_to_container(self.container_name, container)

		for node in cmds.container(container, q=True, nodeList=True):
			cmds.rename(node, joint+"_"+node, ignoreShape=True)

		control = joint+"_translation_control"

		cmds.parent(control, self.module_trans, absolute=True)

		joint_pos = cmds.xform(joint, q=True, worldSpace=True, translation=True)
		cmds.xform(control, worldSpace=True, absolute=True, translation=joint_pos)

		nice_name = utils.strip_leading_namespace(joint)[1]
		attr_name = nice_name+"_T"

		cmds.container(container, edit=True, publishAndBind=[control+".translate", attr_name])
		cmds.container(self.container_name, edit=True, publishAndBind=[container+"."+attr_name, attr_name])

		return control

	def get_trans_ctrl(self,joint_name):

		return joint_name+"_translation_control"

	def setup_stretchy_jnt_segment(self,parent_joint,child_joint):
		
		parent_trans_control = self.get_trans_ctrl(parent_joint)
		child_trans_control = self.get_trans_ctrl(child_joint)

		pole_vector_loc = cmds.spaceLocator(n=parent_trans_control+"_poleVectorLocator")[0]
		pole_vector_loc_grp = cmds.group(pole_vector_loc, n=pole_vector_loc+"_parentConstraint_grp")

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

		self.create_hierarchy(parent_joint, child_joint)

	def create_hierarchy(self,parent_joint,child_joint):

		nodes = self.create_stretchy_obj("/controlobjects/blueprint/hierarchy_representation.ma", "hierarchy_representation_container", "hierarchy_representation", parent_joint, child_joint)
		con_grp = nodes[2]

		cmds.parent(con_grp, self.hierarchy_grp, relative=True)

	def create_stretchy_obj(self,obj_relative_filepath,obj_container_name,obj_name,parent_joint,child_joint):

		obj_file = os.environ["mlrig_tool"]+obj_relative_filepath
		cmds.file(obj_file, i=True)

		obj_container = cmds.rename(obj_container_name, parent_joint+"_"+obj_container_name)

		for node in cmds.container(obj_container, q=True, nodeList=True):
			cmds.rename(node, parent_joint+"_"+node, ignoreShape=True)

		obj = parent_joint+"_"+obj_name

		con_grp = cmds.group(empty=True, name=obj+"_parentConstraint_grp")
		cmds.parent(obj, con_grp, absolute=True)

		parent_con = cmds.parentConstraint(parent_joint, con_grp, maintainOffset=False)[0]

		cmds.connectAttr(child_joint+".translateX", con_grp+".scaleX")

		scale_con = cmds.scaleConstraint(self.module_trans, con_grp, skip=["x"], maintainOffset=0)[0]

		utils.add_node_to_container(obj_container, [con_grp, parent_con, scale_con], ihb=True)
		utils.add_node_to_container(self.container_name, obj_container)

		return(obj_container, obj, con_grp)

	def init_module_trans(self,root_pos):

		ctrl_grp_file = os.environ["mlrig_tool"]+"/controlobjects/blueprint/controlGroup_control.ma"
		cmds.file(ctrl_grp_file, i=True)

		self.module_trans = cmds.rename("controlGroup_control", self.module_namespace+":module_transform")

		cmds.xform(self.module_trans, worldSpace=True, absolute=True, translation=root_pos)

		utils.add_node_to_container(self.container_name, self.module_trans, ihb=True)

		# Setup global scaling 

		cmds.connectAttr(self.module_trans+".scaleY", self.module_trans+".scaleX")
		cmds.connectAttr(self.module_trans+".scaleY", self.module_trans+".scaleZ")

		cmds.aliasAttr("globalScale", self.module_trans+".scaleY")

		cmds.container(self.container_name, edit=True, publishAndBind=[self.module_trans+".translate", "moduleTransform_T"])
		cmds.container(self.container_name, edit=True, publishAndBind=[self.module_trans+".rotate", "moduleTransform_R"])
		cmds.container(self.container_name, edit=True, publishAndBind=[self.module_trans+".globalScale", "moduleTransform_globalScale"])

	def delete_hierarchy(self,parent_joint):

		hierarchy_container = parent_joint+"_hierarchy_representation_container"
		cmds.delete(hierarchy_container)

	def create_ori_ctrl(self,parent_joint,child_joint):

		self.delete_hierarchy(parent_joint)

		nodes = self.create_stretchy_obj("/controlobjects/blueprint/orientation_control.ma", "orientation_control_container", "orientation_control", parent_joint, child_joint)
		ori_container = nodes[0]
		ori_ctrl = nodes[1]
		con_grp = nodes[2]

		cmds.parent(con_grp, self.ori_ctrl_grp, relative=True)

		parent_joint_without_namespace = utils.strip_all_namespaces(parent_joint)[1]
		attr_name = parent_joint_without_namespace+"_orientation"

		cmds.container(ori_container, edit=True, publishAndBind=[ori_ctrl+".rotateX", attr_name])
		cmds.container(self.container_name, edit=True, publishAndBind=[ori_container+"."+attr_name, attr_name])

		return ori_ctrl

	def get_joints(self):
		joint_basename = self.module_namespace+":"
		joints = []

		for joint_inf in self.joint_info:
			joints.append(joint_basename+joint_inf[0])

		return joints

	def get_ori_ctrl(self,joint_name):

		return joint_name+"_orientation_control"

	def ori_ctrl_joint_get_ori(self,joint,clean_parent):
		new_clean_parent = cmds.duplicate(joint, parentOnly=True)[0]

		if not clean_parent in cmds.listRelatives(new_clean_parent, parent=True):
			cmds.parent(new_clean_parent, clean_parent, absolute=True)

		cmds.makeIdentity(
							new_clean_parent,
							apply=True,
							rotate=True, 
							scale=False, 
							translate=False
						)

		ori_ctrl = self.get_ori_ctrl(joint)
		cmds.setAttr(new_clean_parent+".rotateX", cmds.getAttr(ori_ctrl+".rotateX"))

		cmds.makeIdentity(
							new_clean_parent,
							apply=True,
							rotate=True, 
							scale=False, 
							translate=False
						)

		orient_x = cmds.getAttr(new_clean_parent+".jointOrientX")
		orient_y = cmds.getAttr(new_clean_parent+".jointOrientY")
		orient_z = cmds.getAttr(new_clean_parent+".jointOrientZ")

		ori_values = (orient_x, orient_y, orient_z)

		return (ori_values, new_clean_parent)