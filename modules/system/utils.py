'''

utilities

'''
import os
import re
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

def basic_stretchy_ik(root_joint, end_joint, container=None, lock_minimum_length=True, pole_vector_object=None, scale_correct_atrribute=None):
	
	contained_nodes = []

	# Create rotate plane IK on joint chain

	ik_nodes = cmds.ikHandle(sj=root_joint, ee=end_joint, sol="ikRPsolver", n=root_joint+"_ikHandle")
	ik_nodes[1] = cmds.rename(ik_nodes[1], root_joint+"_ikEffector")
	ik_effector = ik_nodes[1]
	ik_handle = ik_nodes[0]
	ik_handle = cmds.setAttr(ik_handle+".visibility", 0)
	contained_nodes.extend(ik_nodes)

	# Create pole vector locator 

	if pole_vector_object == None:
		pole_vector_object = cmds.spaceLocator(n=ik_handle+"_poleVectorLocator")[0]

