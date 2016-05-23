'''

This is the module for buiding the Blueprint UI

'''
import maya.cmds as cmds
from functools import partial

import system.utils as utils
reload(utils)

class BlueprintUi:
	def __init__(self):
		
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
																	columnAlign="center"
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
																		rs=3
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

	def initialize_module_tab(self,tab_height,tab_width):
		
		scroll_height = tab_height - 150

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
														aie=True
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
														label="Re-hook"
													)

		self.ui_elements["snap_root_btn"] = cmds.button(
															enable=False,
															label="Snap Root > Hook"
														)

		self.ui_elements["constraint_root_btn"] = cmds.button(
																	enable=False,
																	label="Constraint Root > Hook"
																)

		self.ui_elements["group_selected_btn"] = cmds.button(label="Group Selected")

		self.ui_elements["ungroup_btn"] = cmds.button(
															enable=False,
															label="Ungroup"
														)

		self.ui_elements["mirror_module_btn"] = cmds.button(
																enable=False,
																label="Mirror Module"
															)

		cmds.text(label="")

		self.ui_elements["delete_module_btn"] = cmds.button(
																enable=False,
																label="Delete"
															)

		self.ui_elements["symmetry_move_checkbox"] = cmds.checkBox(
																		enable=True,
																		label="Symmetry Move"
																	)

		cmds.setParent(self.ui_elements["module_column"])
		cmds.separator()

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

		text_column = cmds.columnLayout(columnAlign="center")

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

		mod = __import__("blueprint."+module, {}, {}, [module])
		reload(mod)

		module_class = getattr(mod, mod.CLASS_NAME)
		module_instance = module_class(user_specified_name)
		module_instance.install()

		module_trans = mod.CLASS_NAME+"__"+user_specified_name+":module_transform"

		cmds.select(
						module_trans,
						replace=True
					)

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
			module_instance = module_class(user_specified_name=module[1])

			module_info = module_instance.lock_phase1()

			module_instances.append((module_instance, module_info))

		for module in module_instances:
			module[0].lock_phase2(module[1])