'''

utilities

'''
import os
import re

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

	file_directory = os.environ["mlrig_tool"] + "/" + relative_directory + "/"

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


