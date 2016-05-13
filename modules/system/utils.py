'''

utilities

'''
import os
import re
import types
from math import fabs
import maya.cmds as cmds

def find_all_modules(relative_directory):
	
	# Search the relative directory for all available modules 
	# Return a list of all module name (excluding the ".py" extension)
	all_py_files = find_all_files(relative_directory, ".py")

	return_modules = []

	for file in all_py_files:
		if file != "__init__":
			return_modules.append(file)

	return return_modules

def find_all_files(relative_directory, file_extension):
	
	# Search the relative directory for all files with the given extenion 
	# Return a list of all file names, excluding the file extension

	file_directory = os.environ["mlrig_tool"]+"/"+relative_directory+"/"

	all_files = os.listdir(file_directory)

	# refine all files, listing only those of the specified file extension
	return_files = []

	for f in all_files:
		split_string = str(f).rpartition(file_extension)

		if not split_string[1] == "" and split_string[2] == "":
			return_files.append(split_string[0])


	return return_files

def find_highest_trailing_number(names, basename):
	
	highest_value = 0 

	for n in names:
		if n.find(basename) == 0:
			suffix = n.partition(basename)[2]

			if re.match("^[0-9]*$", suffix):
				numerical_element = int(suffix)

				if numerical_element > highest_value:
					highest_value = numerical_element

	return highest_value

def strip_leading_namespace(node_name):
	
	if str(node_name).find(":") == -1:
		return None

	split_string = str(node_name).partition(":")

	return [split_string[0], split_string[2]]

def strip_all_namespaces(node_name):

	if str(node_name).find(":") == -1:
		return None

	split_string = str(node_name).rpartition(":")

	return [split_string[0], split_string[2]]

def basic_stretchy_ik(root_joint, end_joint, container=None, lock_min_len=True, pole_vector_obj=None, scale_correct_atrr=None):
	
	contained_nodes = []

	total_orig_len = 0.0
	done = False
	parent = root_joint
	child_joints = []

	while not done:
		children = cmds.listRelatives(parent, children=True)
		children = cmds.ls(children, type="joint")

		if len(children) == 0:
			done = True
		else:
			child = children[0]
			child_joints.append(child)

			total_orig_len += fabs(cmds.getAttr(child+".translateX"))

			parent = child

			if child == end_joint:
				done = True

	# Create rotate plane IK on joint chain

	ik_nodes = cmds.ikHandle(sj=root_joint, ee=end_joint, sol="ikRPsolver", n=root_joint+"_ikHandle")
	ik_nodes[1] = cmds.rename(ik_nodes[1], root_joint+"_ikEffector")
	ik_effector = ik_nodes[1]
	ik_handle = ik_nodes[0]
	
	cmds.setAttr(ik_handle+".visibility", 0)
	contained_nodes.extend(ik_nodes)

	# Create pole vector locator 

	if pole_vector_obj == None:
		
		pole_vector_obj = cmds.spaceLocator(name=ik_handle+"_poleVectorLocator")[0]
		contained_nodes.append(pole_vector_obj)
		cmds.xform(pole_vector_obj, worldSpace=True, absolute=True, translation=cmds.xform(root_joint, q=True, worldSpace=True, translation=True))
		cmds.xform(pole_vector_obj, worldSpace=True, relative=True, translation=[0.0, 1.0, 0.0])

		cmds.setAttr(pole_vector_obj+".visibility", 0)

	pole_vector_con = cmds.poleVectorConstraint(pole_vector_obj, ik_handle)[0]
	contained_nodes.append(pole_vector_con)

	# Create root and end locators
	
	root_loc = cmds.spaceLocator(n=root_joint+"_rootPosLocator")[0]
	root_loc_point_con = cmds.pointConstraint(root_joint, root_loc, maintainOffset=False, n=root_loc+"_pointConstraint")[0]

	end_loc = cmds.spaceLocator(n=end_joint+"_endPosLocator")[0]
	cmds.xform(end_loc, worldSpace=True, absolute=True, translation=cmds.xform(ik_handle, q=True, worldSpace=True, translation=True))

	ik_handle_point_con = cmds.pointConstraint(end_loc, ik_handle, maintainOffset=False, n=ik_handle+"_pointConstraint")[0]

	contained_nodes.extend([root_loc, end_loc, root_loc_point_con, ik_handle_point_con])

	cmds.setAttr(root_loc+".visibility", 0)
	cmds.setAttr(end_loc+".visibility", 0)

	# Grabbing distance between locator

	root_loc_without_namespace = strip_all_namespaces(root_loc)[1]
	end_loc_without_namespace = strip_all_namespaces(end_loc)[1]
	module_namespace = strip_all_namespaces(root_joint)[0]

	dist_node = cmds.shadingNode("distanceBetween", asUtility=True, n=module_namespace+":distBetween_"+root_loc_without_namespace+"_"+end_loc_without_namespace)

	contained_nodes.append(dist_node)

	cmds.connectAttr(root_loc+"Shape.worldPosition[0]", dist_node+".point1")
	cmds.connectAttr(end_loc+"Shape.worldPosition[0]", dist_node+".point2")

	scale_attr = dist_node+".distance"

	# Divide distance by total original length = scale factor
	scale_factor = cmds.shadingNode("multiplyDivide", asUtility=True, n=ik_handle+"_scaleFactor")
	contained_nodes.append(scale_factor)

	cmds.setAttr(scale_factor+".operation", 2)
	cmds.connectAttr(scale_attr, scale_factor+".input1X")
	cmds.setAttr(scale_factor+".input2X", total_orig_len)

	translation_driver = scale_factor+".outputX"

	# Connect joints to stretchy calculations

	for joint in child_joints:

		mult_node = cmds.shadingNode("multiplyDivide", asUtility=True, n=joint+"_scaleMultiply")
		contained_nodes.append(mult_node)

		cmds.setAttr(mult_node+".input1X", cmds.getAttr(joint+".translateX"))
		cmds.connectAttr(translation_driver, mult_node+".input2X")
		cmds.connectAttr(mult_node+".outputX", joint+".translateX")

	if container != None:
		add_node_to_container(container, contained_nodes, ihb=True)

	return_dict = {}

	return_dict["ik_handle"] = ik_handle
	return_dict["ik_effector"] = ik_effector
	return_dict["root_loc"] = root_loc
	return_dict["end_loc"] = end_loc
	return_dict["pole_vector_obj"] = pole_vector_obj
	return_dict["ik_handle_point_con"] = ik_handle_point_con
	return_dict["root_loc_point_con"] = root_loc_point_con

	return return_dict

def force_scene_update():
	
	cmds.setToolTo("moveSuperContext")
	nodes = cmds.ls()

	for node in nodes:
		cmds.select(node, replace=True)

	cmds.select(clear=True)
	cmds.setToolTo("selectSuperContext")

def add_node_to_container(container, nodes_in, ihb=False, includeShapes=False, force=False):

	nodes = []

	if type(nodes_in) is types.ListType:
		nodes = list(nodes_in)
	else:
		nodes = [nodes_in]

	conversion_nodes = []

	for node in nodes:
		
		node_conversion_nodes = cmds.listConnections(node, source=True, destination=True)
		node_conversion_nodes = cmds.ls(node_conversion_nodes, type="unitConversion")

		conversion_nodes.extend(node_conversion_nodes)

	nodes.extend(conversion_nodes)
	cmds.container(container, edit=True, addNode=nodes, ihb=ihb, includeShapes=includeShapes, force=force)
