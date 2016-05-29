'''

This is the module for buiding the Blueprint UI

'''
import maya.cmds as cmds
from functools import partial

import system.utils as utils
reload(utils)
import system.group_selected as group_selected
reload(group_selected)
import system.mirror_module as mirror_module
reload(mirror_module)

class BlueprintUi:

	def __init__(self):

		self.module_instance = None
		
		# Store UI elements in a dictionary

		self.ui_elements = {}

		if cmds.window("blueprint_ui_window", exists=True):
			cmds.deleteUI("blueprint_ui_window")

		window_width = 400
		window_height = 598

		self.ui_elements["window"] = cmds.window(	
													"blueprint_ui_window",
													width=window_width,
													height=window_height,
													title="Blueprint Module UI",
													sizeable=False
												)

		self.ui_elements["top_level_column"] = cmds.columnLayout(	
																	adjustableColumn=True,
																	columnAlign="center",
																	adj=True
																)

		# Setup tabs

		tab_height = 500

		self.ui_elements["tabs"] = cmds.tabLayout(
														height=tab_height,
														innerMarginWidth=5, 
														innerMarginHeight=5
													)

		tab_width = cmds.tabLayout(
										self.ui_elements["tabs"],
										q=True,
										width=True
									)

		self.scroll_width = tab_width+30

		self.initialize_module_tab(
									tab_height,
									tab_width
								)

		cmds.tabLayout(
						self.ui_elements["tabs"],
						edit=True,
						tabLabelIndex=([1, "Modules"])
					)

		cmds.setParent(self.ui_elements["top_level_column"])
		self.ui_elements["lock_publish_column"] = cmds.columnLayout(
																		adj=True,
																		columnAlign="center",
																		rs=3,
																	)

		cmds.separator()

		self.ui_elements["lock_btn"] = cmds.button(
														label="Lock",
														command=self.lock
													)

		cmds.separator()

		self.ui_elements["publish_btn"] = cmds.button(label="Publish")

		cmds.separator()

		# Display window

		cmds.showWindow(self.ui_elements["window"])

		# UI Script job

		self.create_script_job()

	def create_script_job(self):

		self.job_num = cmds.scriptJob(event=["SelectionChanged", self.modify_selected], runOnce=True, parent=self.ui_elements["window"])

	def delete_script_job(self):

		cmds.scriptJob(kill=self.job_num)

	def initialize_module_tab(self,tab_height,tab_width):
		
		module_specific_scroll_height = 100

		scroll_height = tab_height - module_specific_scroll_height - 140

		self.ui_elements["module_column"] = cmds.columnLayout(adj=True, rs=3)

		self.ui_elements["module_frame_layout"] = cmds.frameLayout(	
																		height=scroll_height,
																		collapsable=False,
																		borderVisible=False,
																		labelVisible=False
																	)

		self.ui_elements["module_list_scroll"] = cmds.scrollLayout(hst=0)

		self.ui_elements["module_list_column"] = cmds.columnLayout(
																		columnWidth=self.scroll_width,
																		adj=True,
																		rs=2
																	)

		# First separator

		cmds.separator()

		for module in utils.find_all_modules("modules/blueprint"):
			
			self.create_module_install_button(module)
			cmds.setParent(self.ui_elements["module_list_column"])
			cmds.separator()

		cmds.setParent(self.ui_elements["module_column"])
		cmds.separator()

		self.ui_elements["module_name_row"] = cmds.rowLayout(	
																nc=2,
																columnAttach=(1, "right", 0),
																columnWidth=[(1, 80)],
																adjustableColumn=2
															)
		cmds.text(label="Module Name:")
		self.ui_elements["module"] = cmds.textField(	
														enable=False,
														aie=True,
														enterCommand=self.rename_module
													)

		cmds.setParent(self.ui_elements["module_column"])

		column_width = tab_width + 50

		self.ui_elements["module_btn_row_column"] = cmds.rowColumnLayout(	
																			numberOfColumns=3, ro=[(1, "both", 2), (2, "both", 2), (3, "both", 2)], 
																			columnAttach=[(1, "both", 3), (2, "both", 3), (3, "both", 3)], 
																			columnWidth=[(1, column_width), (2, column_width), (3, column_width)]
																		)

		self.ui_elements["rehook_btn"] = cmds.button(	
														enable=False,
														label="Re-hook",
														command=self.rehook_module_setup
													)

		self.ui_elements["snap_root_btn"] = cmds.button(
															enable=False,
															label="Snap Root > Hook",
															c=self.snap_root_to_hook
														)

		self.ui_elements["constraint_root_btn"] = cmds.button(
																	enable=False,
																	label="Constraint Root > Hook",
																	c=self.constrain_root_to_hook
																)

		self.ui_elements["group_selected_btn"] = cmds.button(label="Group Selected", c=self.group_selected)

		self.ui_elements["ungroup_btn"] = cmds.button(
															enable=False,
															label="Ungroup",
															c=self.ungroup_selected
														)

		self.ui_elements["mirror_module_btn"] = cmds.button(
																enable=False,
																label="Mirror Module",
																c=self.mirror_selection
															)

		cmds.text(label="")

		self.ui_elements["delete_module_btn"] = cmds.button(
																enable=False,
																label="Delete",
																c=self.delete_module
															)

		self.ui_elements["symmetry_move_checkbox"] = cmds.checkBox(
																		enable=True,
																		label="Symmetry Move"
																	)

		cmds.setParent(self.ui_elements["module_column"])
		cmds.separator()

		self.ui_elements["module_specific_roll_column_layout"] = cmds.rowColumnLayout(
																							nr=1,
																							rowAttach=[1, "both", 0],
																							rowHeight=[2, module_specific_scroll_height]
																						)

		self.ui_elements["module_specific_scroll"] = cmds.scrollLayout(hst=0, width=300)

		self.ui_elements["module_specific_column"] = cmds.columnLayout(
																			columnWidth=self.scroll_width,
																			adj=True,
																			columnAttach=["both", 5],
																			rs=2
																		)
		

		cmds.setParent(self.ui_elements["module_column"])
		# cmds.separator()

	def create_module_install_button(self,module):
		
		mod = __import__("blueprint."+module, {}, {}, [module])
		reload(mod)

		title = mod.TITLE 
		description = mod.DESCRIPTION 
		icon = mod.ICON 

		# Create UI

		button_size = 64
		row = cmds.rowLayout(	
								numberOfColumns=2,
								columnWidth=([1, button_size]),
								adjustableColumn=2,
								columnAttach=([1, "both", 0],[2, "both", 5])
							)

		self.ui_elements["module_button_"+module] = cmds.symbolButton(	
																			width=button_size,
																			height=button_size,
																			image=icon,
																			command=partial(self.install_module, module)
																		)

		text_column = cmds.columnLayout(
											columnAlign="center",
											adj=True
										)

		cmds.text(
						align="center",
						width=self.scroll_width-button_size+300,
						label=title
					)

		cmds.scrollField(	
							text=description,
							editable=False,
							width=self.scroll_width-button_size+300,
							height=button_size,
							wordWrap=True
						)

	def install_module(self,module,*args):
		
		basename = "instance_"
		
		cmds.namespace(setNamespace =":")
		namespaces = cmds.namespaceInfo(listOnlyNamespaces=True)

		for i in range(len(namespaces)):
			if namespaces[i].find("__") != -1:
				namespaces[i] = namespaces[i].partition("__")[2]

		new_suffix = utils.find_highest_trailing_number(namespaces, basename)+1

		user_specified_name = basename+str(new_suffix)

		hook_obj = self.find_hook_obj_from_selection()

		mod = __import__("blueprint."+module, {}, {}, [module])
		reload(mod)

		module_class = getattr(mod, mod.CLASS_NAME)
		module_instance = module_class(user_specified_name, hook_obj)
		module_instance.install()

		module_trans = mod.CLASS_NAME+"__"+user_specified_name+":module_transform"

		cmds.select(module_trans,replace=True)

		cmds.setToolTo("moveSuperContext")

	def lock(self,*args):

		result = cmds.confirmDialog(
										messageAlign="center",
										title="Lock Blueprints",
										message="The action of locking a character will convert the current blueprint modules to joints."+
												"\nThis action cannot be undone."+
												"\nModification to the blueprint system cannot be made after this point."+
												"\nDo you want to continue?",
										button=["Accept", "Cancel"],
										defaultButton="Accept",
										cancelButton="Cancel",
										dismissString="Cancel"
										)

		if result != "Accept":
			return

		module_info = [] # store (module, user_specified_name) pairs

		cmds.namespace(setNamespace=":")
		namespaces = cmds.namespaceInfo(listOnlyNamespaces=True)

		module_name_info = utils.find_all_module_names("/modules/blueprint")
		valid_modules = module_name_info[0]
		valid_module_names = module_name_info[1]

		for n in namespaces:
			split_string = n.partition("__")

			if split_string[1] != "":
				module = split_string[0]
				user_specified_name = split_string[2]

				if module in valid_module_names:
					index = valid_module_names.index(module)
					module_info.append([valid_modules[index], user_specified_name])

		if len(module_info) == 0:
			cmds.confirmDialog(
									messageAlign="center",
									title="Lock Blueprints",
									message="There are no blueprint instances in the current scene."+
											"\nAborting Lock",
									button=["Accept"],
									defaultButton="Accept"
									)
			return

		module_instances = []

		for module in module_info:
			mod = __import__("blueprint."+module[0], {}, {}, [module[0]])
			reload(mod)

			module_class = getattr(mod, mod.CLASS_NAME)
			module_instance = module_class(module[1], None)
			module_info = module_instance.lock_phase1()

			module_instances.append((module_instance, module_info))

		# calling on phase 1 functionality
		for module in module_instances:
			module[0].lock_phase2(module[1])

		group_container = "Group_container"

		# finding the existing groups and deleting thems
		if cmds.objExists(group_container):
			cmds.lockNode(group_container, lock=False, lockUnpublished=False)
			cmds.delete(group_container)

		# calling on phase 2 functionality
		for module in module_instances:
			hook_obj = module[1][4]
			module[0].lock_phase3(hook_obj)

	def modify_selected(self, *args):

		selected_nodes = cmds.ls(selection=True)

		if len(selected_nodes) <= 1:
			self.module_instance = None
			selected_module_namespace = None
			current_module_file = None

			cmds.button(self.ui_elements["ungroup_btn"], edit=True, enable=False)
			cmds.button(self.ui_elements["mirror_module_btn"], edit=True, enable=False)

			if len(selected_nodes) == 1:
				last_selected = selected_nodes[0]

				if last_selected.find("Group__") == 0:

					cmds.button(self.ui_elements["ungroup_btn"], edit=True, enable=True)
					cmds.button(self.ui_elements["mirror_module_btn"], edit=True, enable=True, label="Mirror Group")

				namespace_and_node = utils.strip_leading_namespace(last_selected)

				if namespace_and_node != None:

					namespace = namespace_and_node[0]

					module_name_info = utils.find_all_module_names("/modules/blueprint")
					valid_modules = module_name_info[0]
					valid_module_names = module_name_info[1]

					index = 0

					for module_name in valid_module_names:

						module_name_inc_suffix = module_name+"__"

						if namespace.find(module_name_inc_suffix) == 0:

							current_module_file = valid_modules[index]
							selected_module_namespace = namespace

							break

						index += 1

			control_enabled = False
			user_specified_name = ""
			constrain_command = self.constrain_root_to_hook
			constrain_label = "Constrain Root > Hook"

			if selected_module_namespace != None:

				control_enabled = True
				user_specified_name = selected_module_namespace.partition("__")[2]

				mod = __import__("blueprint."+current_module_file, {}, {}, [current_module_file])
				reload(mod)

				module_class = getattr(mod, mod.CLASS_NAME)
				self.module_instance = module_class(user_specified_name, None)

				cmds.button(self.ui_elements["mirror_module_btn"], edit=True, enable=True, label="Mirror Module")

				if self.module_instance.is_root_constrained():

					constrain_command = self.unconstrain_root_from_hook
					constrain_label = "Unconstrain Root"

			cmds.button(self.ui_elements["rehook_btn"], edit=True, enable=control_enabled)

			cmds.button(self.ui_elements["snap_root_btn"], edit=True, enable=control_enabled)

			cmds.button(
							self.ui_elements["constraint_root_btn"],
							edit=True,
							enable=control_enabled,
							label=constrain_label,
							c=constrain_command
						)

			cmds.button(self.ui_elements["delete_module_btn"], edit=True, enable=control_enabled)

			cmds.textField(self.ui_elements["module"], edit=True, enable=control_enabled, text=user_specified_name)

			self.create_module_specific_controls()

		self.create_script_job()

	def create_module_specific_controls(self):

		existing_controls = cmds.columnLayout(
													self.ui_elements["module_specific_column"],
													q=True,
													adj=True,
													childArray=True
												)

		if existing_controls != None:
			cmds.deleteUI(existing_controls)

		cmds.setParent(self.ui_elements["module_specific_column"])

		if self.module_instance != None:
			self.module_instance.ui(self, self.ui_elements["module_specific_column"])

	def delete_module(self, *args):

		self.module_instance.delete()
		cmds.select(clear=True)

	def rename_module(self, *args):

		new_name = cmds.textField(self.ui_elements["module"], q=True, text=True)

		self.module_instance.rename_module_instance(new_name)

		previous_selection = cmds.ls(sl=True)

		if len(previous_selection) > 0:
			cmds.select(previous_selection, replace=True)
		else:
			cmds.select(clear=True)
			
	def find_hook_obj_from_selection(self, *args):

		selected_objs = cmds.ls(sl=True, transforms=True)

		number_objs = len(selected_objs)

		hook_obj = None

		if number_objs != 0:
			hook_obj = selected_objs[number_objs -1]

		return hook_obj

	def rehook_module_setup(self, *args):

		selected_nodes = cmds.ls(sl=True, transforms=True)

		if len(selected_nodes) == 2:

			new_hook = self.find_hook_obj_from_selection()
			self.module_instance.rehook(new_hook)

		else:
			self.delete_script_job()

			current_selection = cmds.ls(sl=True)

			cmds.headsUpMessage("Please select the joint you wish to re-hook to. Clear selection to un-hook")

			cmds.scriptJob(event=["SelectionChanged", partial(self.rehook_module_callback, current_selection)], runOnce=True)

	def rehook_module_callback(self, current_selection):

		new_hook = self.find_hook_obj_from_selection()

		self.module_instance.rehook(new_hook)

		if len(current_selection) > 0:

			cmds.select(current_selection, replace=True)

		else:

			cmds.select(clear=True)

		self.create_script_job()

	def snap_root_to_hook(self, *args):

		self.module_instance.snap_root_to_hook()

	def constrain_root_to_hook(self, *args):

		self.module_instance.constrain_root_to_hook()

		cmds.button(
						self.ui_elements["constraint_root_btn"],
						edit=True,
						label="Unconstrain Root",
						c=self.unconstrain_root_from_hook
					)

	def unconstrain_root_from_hook(self, *args):

		self.module_instance.unconstrain_root_from_hook()

		cmds.button(
						self.ui_elements["constraint_root_btn"],
						edit=True,
						label="Constrain Root > Hook",
						c=self.constrain_root_to_hook
					)

	def group_selected(self, *args):

		group_selected.GroupSelected().show_ui()

	def ungroup_selected(self, *args):

		group_selected.UngroupSelected()

	def mirror_selection(self, *args):

		mirror_module.MirrorModule()


