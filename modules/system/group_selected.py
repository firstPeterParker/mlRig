'''

This script will define the group selected functionality

'''
from functools import partial
import os

import system.utils as utils
reload(utils)

import maya.cmds as cmds


class GroupSelected:

	def __init__(self):

		self.objects_to_group = []

	def show_ui(self):

		# method to determine if we have a seletion and if we do then we are able to generate a UI
		self.find_selection_to_group()

		if len(self.objects_to_group) == 0:

			return

		self.ui_elements = {}

		if cmds.window("group_selected_ui_window", exists=True):

			cmds.deleteUI("group_selected_ui_window")

		# main window height and width parameters
		window_width = 300
		window_height = 150

		# main window attributes
		self.ui_elements["window"] = cmds.window(
													"group_selected_ui_window",
													width=window_width,
													height=window_height,
													title="Group Selected",
													sizeable=False
												)

		# top level column layout 
		self.ui_elements["top_level_column"] = cmds.columnLayout(
																	adj=True,
																	columnAlign="center",
																	rs=3
																)

		# row layout for a label and a user specified text field
		self.ui_elements["group_name_row_column"] = cmds.rowColumnLayout(
																			nc=2,
																			columnAttach=(1, "right", 0),
																			columnWidth=[
																							(1, 80),
																							(2, window_width-90)
																						]
																		)

		# text field label
		cmds.text(label="Group Name :")

		# user specified text field
		self.ui_elements["group_name"] = cmds.textField(text="group")

		# parenting to the main column layout 
		cmds.setParent(self.ui_elements["top_level_column"])

		self.ui_elements["create_at_row_column"] = cmds.rowColumnLayout(
																			numberOfColumns=3,
																			columnAttach=(1, "right", 0),
																			columnWidth=[
																							(1, 80),
																							(2, window_width-170),
																							(3, 80)
																						]
																		)

		cmds.text(label="Position at :")
		cmds.text(label="")
		cmds.text(label="")

		cmds.text(label="")
		self.ui_elements["create_at_last_selected"] = cmds.button(label="Last Selected", c=self.create_at_last_selected)
		cmds.text(label="")

		cmds.text(label="")
		self.ui_elements["create_at_average_position"] = cmds.button(label="Average Position", c=self.create_at_average_position)
		cmds.text(label="")

		cmds.setParent(self.ui_elements["top_level_column"])

		cmds.separator()

		columnWidth = (window_width/2) - 5

		self.ui_elements["button_row"] = cmds.rowLayout(
															nc=2,
															columnWidth=[
																			(1, columnWidth),
																			(2, columnWidth)
																		],
															cat=[
																	(1, "both", 10),
																	(2, "both", 10)
																],
															columnAlign=[
																			(1, "center"),
																			(2, "center")
																		]
														)

		cmds.button(label="Accept", c=self.accept_window)
		cmds.button(label="Cancel", c=self.cancel_window)

		# show main window
		cmds.showWindow(self.ui_elements["window"])

		#####################################
		self.create_temp_grp_representation()

		self.create_at_last_selected()

		cmds.select(self.temp_group_transform)
		cmds.setToolTo("moveSuperContext")

	def find_selection_to_group(self):

		selected_objects = cmds.ls(selection=True, transforms=True)

		self.objects_to_group = []

		for obj in selected_objects:

			valid = False

			if obj.find("module_transform") != -1:

				split_string = obj.rsplit("module_transform")

				if split_string[1] == "":

					valid = True

			if valid == False and obj.find("Group__") == 0:

				valid = True 

			if valid == True:

				self.objects_to_group.append(obj)

	def create_temp_grp_representation(self):

		control_group_file = os.environ["mlrig_tool"]+"/controlobjects/blueprint/controlGroup_control.ma"
		cmds.file(control_group_file, i=True)

		self.temp_group_transform = cmds.rename("controlGroup_control", "Group__tempGroupTransform__")

		cmds.connectAttr(self.temp_group_transform+".scaleY", self.temp_group_transform+".scaleX")
		cmds.connectAttr(self.temp_group_transform+".scaleY", self.temp_group_transform+".scaleZ")

		for attr in ["scaleX", "scaleZ", "visibility"]:

			cmds.setAttr(self.temp_group_transform+"."+attr, keyable=False, lock=True)

		cmds.aliasAttr("globalScale", self.temp_group_transform+".scaleY")

	def create_at_last_selected(self, *args):

		control_pos = cmds.xform(
									self.objects_to_group[len(self.objects_to_group)-1],
									query=True,
									worldSpace=True, 
									translation=True
								)

		cmds.xform(
						self.temp_group_transform,
						worldSpace=True,
						absolute=True,
						translation=control_pos
					)

	def create_at_average_position(self, *args):

		control_pos = [0.0, 0.0, 0.0]

		for obj in self.objects_to_group:

			obj_pos = cmds.xform(obj, query=True, worldSpace=True, translation=True)
			control_pos[0] += obj_pos[0]
			control_pos[1] += obj_pos[1]
			control_pos[2] += obj_pos[2]

		number_of_objects = len(self.objects_to_group)
		control_pos[0] /= number_of_objects
		control_pos[1] /= number_of_objects
		control_pos[2] /= number_of_objects

		cmds.xform(self.temp_group_transform, worldSpace=True, absolute=True, translation=control_pos)

	def cancel_window(self, *args):

		cmds.deleteUI(self.ui_elements["window"])
		cmds.delete(self.temp_group_transform)

	def accept_window(self, *args):

		group_name = cmds.textField(self.ui_elements["group_name"], query=True, text=True)

		if self.create_group(group_name) != None:

			cmds.deleteUI(self.ui_elements["window"])

	def create_group(self, group_name):

		full_group_name = "Group__"+group_name

		if cmds.objExists(full_group_name):

			cmds.confirmDialog(
									title="Name Conflict",
									message="Group \""+group_name+"\" already exists",
									button="Accept",
									defaultButton="Accept"
								)

			return None

		group_transform = cmds.rename(self.temp_group_transform, full_group_name)

		group_container = "Group_container"

		if not cmds.objExists(group_container):

			cmds.container(name=group_container)

		containers = [group_container]

		for obj in self.objects_to_group:

			if obj.find("Group__") == 0:

				continue

			obj_namespace = utils.strip_leading_namespace(obj)[0]
			containers.append(obj_namespace+":module_container")

		for c in containers:

			cmds.lockNode(c, lock=False, lockUnpublished=False)

		if len(self.objects_to_group) != 0:

			temp_group = cmds.group(self.objects_to_group, absolute=True)

			group_parent = cmds.listRelatives(temp_group, parent=True)

			if group_parent != None:

				cmds.parent(group_transform, group_parent[0], absolute=True)

			cmds.parent(self.objects_to_group, group_transform, absolute=True)

			cmds.delete(temp_group)

		self.add_group_to_container(group_transform)

		for c in containers:
			cmds.lockNode(c, lock=True, lockUnpublished=True)

		cmds.setToolTo("moveSuperContext")
		cmds.select(group_transform, replace=True)

		return group_transform

	def add_group_to_container(self, group):

		group_container = "Group_container"

		utils.add_node_to_container(group_container, group, includeShapes=True)

		group_name = group.partition("Group__")[2]

		cmds.container(group_container, edit=True, publishAndBind=[group+".translate", group_name+"_t"])
		cmds.container(group_container, edit=True, publishAndBind=[group+".rotate", group_name+"_r"])
		cmds.container(group_container, edit=True, publishAndBind=[group+".globalScale", group_name+"_globalScale"])





