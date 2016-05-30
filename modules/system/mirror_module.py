'''

This script will define the mirror module and mirror group functionality 

'''

import maya.cmds as cmds
import system.utils as utils
reload(utils)

class MirrorModule:

	def __init__(self):

		selection = cmds.ls(sl=True, transforms=True)

		if len(selection) == 0:

			return

		first_selected = selection[0]

		self.modules = []
		self.group = None

		if first_selected.find("Group__") == 0:

			self.group = first_selected
			self.modules = self.find_sub_modules(first_selected)

		else:

			module_namespace_info = utils.strip_leading_namespace(first_selected)

			if module_namespace_info != None:

				self.modules.append(module_namespace_info[0])

		#####################
		temp_module_list = []

		for module in self.modules:

			if self.is_module_a_mirror(module):

				cmds.confirmDialog(title="Mirror Module(s)", message="Cannot mirror a previously mirrored module, aborting mirror.", button="Accept", default="Accpet")

				return

			if not self.can_module_be_mirrored(module):

				print "Module \""+module+"\" is of a module type that cannot be mirrored... skipping module."

			else:

				temp_module_list.append(module)

		self.modules = temp_module_list

		if len(self.modules) > 0:

			self.mirror_module_ui()

	def find_sub_modules(self, group):

		return_modules = []

		children = cmds.listRelatives(group, children=True)
		children = cmds.ls(children, transforms=True)

		for child in children:

			if child.find("Group__") == 0:

				return_modules.extend(self.find_sub_modules(child))

			else:

				namespace_info = utils.strip_all_namespaces(child)

				if namespace_info != None and namespace_info[1] == "module_transform":

					modules = namespace_info[0]

					return_modules.append(modules)

		return return_modules

	def is_module_a_mirror(self, module):

		module_group = module+":module_grp"

		return cmds.attributeQuery("mirrorLinks", node=module_group, exists=True)

	def can_module_be_mirrored(self, module):

		module_name_info = utils.find_all_module_names("/modules/blueprint")
		valid_modules = module_name_info[0]
		valid_module_names = module_name_info[1]

		module_name = module.partition("__")[0]

		if not module_name in valid_module_names:

			return False

		index = valid_module_names.index(module_name)
		mod = __import__("blueprint."+valid_modules[index], {}, {}, valid_modules[index])
		reload(mod)

		module_class = getattr(mod, mod.CLASS_NAME)
		module_inst = module_class("null", None)

		return module_inst.can_module_be_mirrored()

	def mirror_module_ui(self):

		self.module_names = []

		for module in self.modules:
			
			self.module_names.append(module.partition("__")[2])

		self.same_mirror_settings_for_all = False

		if len(self.modules) > 1:

			result = cmds.confirmDialog(
											title="Mirror Multiple Modules",
											message=str(len(self.modules))+" modules selected for mirror. \nHow would you like to apply mirror settings?",
											button=["Same for All", "Individually", "Cancel"],
											defaultButton="Same for All",
											cancelButton="Cancel",
											dismissString="Cancel"
										)
			if result == "Cancel":

				return

			if result == "Same for All":

				self.same_mirror_settings_for_all = True

		self.ui_elements = {}

		if cmds.window("mirror_module_ui_window", exists=True):

			cmds.deleteUI("mirror_module_ui_window")

		window_width = 300
		window_height = 400

		self.ui_elements["window"] = cmds.window(
													"mirror_module_ui_window",
													width=window_width,
													height=window_height,
													title="Mirror Module(s)",
													sizeable=False
												)

		self.ui_elements["scroll_layout"] = cmds.scrollLayout(hst=0)
		self.ui_elements["top_column_layout"] = cmds.columnLayout(adj=True, rs=3)

		# Mirror options XY, YZ, XZ
		scroll_width = window_width - 30
		mirror_plane_text_width = 85
		mirror_plane_column_width = (scroll_width - mirror_plane_text_width / .4)

		self.ui_elements["mirror_plane_row_column"] = cmds.rowColumnLayout(
																				nc=4,
																				columnAttach=(1, "right", 0),
																				columnWidth=[
																								(1, mirror_plane_text_width),
																								(2, mirror_plane_column_width),
																								(3, mirror_plane_column_width),
																								(4, mirror_plane_column_width)
																							]
																			)

		cmds.text(label="Mirror Plane: ")

		self.ui_elements["mirror_plane_radio_collection"] = cmds.radioCollection()

		cmds.radioButton("XY", label="XY", select=False)
		cmds.radioButton("YZ", label="YZ", select=True)
		cmds.radioButton("XZ", label="XZ", select=False)

		cmds.setParent(self.ui_elements["top_column_layout"])
		cmds.separator()

		# list of modules in the selected group
		cmds.text(label="Mirrored Name(s):")

		column_width = scroll_width / 2

		self.ui_elements["module_name_row_column"] = cmds.rowColumnLayout(
																			nc=2,
																			columnAttach=(1, "left", 0),
																			columnWidth=[(1, column_width-60), (2, column_width)]
																		)

		for module in self.module_names:

			cmds.text(label=module+" >> ")

			self.ui_elements["module_name_"+module] = cmds.textField(enable=True, text=module+"_mirror")

		cmds.setParent(self.ui_elements["top_column_layout"])
		cmds.separator()

		if self.same_mirror_settings_for_all:

			self.generate_mirror_function_controls(None, scroll_width)

		else:

			for module in self.module_names:

				cmds.setParent(self.ui_elements["top_column_layout"])
				self.generate_mirror_function_controls(module, scroll_width)

		cmds.setParent(self.ui_elements["top_column_layout"])
		cmds.separator()

		self.ui_elements["button_row"] = cmds.rowLayout(
															nc=2,
															columnWidth=[
																			(1, column_width),
																			(2, column_width)
																		],
															columnAttach=[
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

		cmds.showWindow(self.ui_elements["window"])

	def generate_mirror_function_controls(self, module_name, scroll_width):

		rotation_radio_collection = "rotation_radioCollection_all"
		translation_radio_collection = "translation_radioCollection_all"
		text_label = "Mirror Settings:"

		behavior_name = "behavior__"
		orientation_name = "orientation__"
		mirrored_name = "mirrored__"
		worldspace_name = "worldSpace__"

		if module_name != None:

			rotation_radio_collection = "rotation_radioCollection_"+module_name
			translation_radio_collection = "translation_radioCollection_"+module_name

			text_label = module_name+" Mirror Settings:"

			behavior_name = "behavior__"+module_name
			orientation_name = "orientation__"+module_name
			mirrored_name = "mirrored__"+module_name
			worldspace_name = "worldSpace__"+module_name

		cmds.text(label=text_label)

		mirror_settings_text_width = 100
		mirror_settings_column_width = (scroll_width - mirror_settings_text_width / .55)

		cmds.rowColumnLayout(
								nc=3,
								columnAttach=(1, "right", 0),
								columnWidth=[
												(1, mirror_settings_text_width),
												(2, mirror_settings_column_width),
												(3, mirror_settings_column_width)
											]
							)

		cmds.text(label="Rotation Mirror: ")
		self.ui_elements[rotation_radio_collection] = cmds.radioCollection()

		cmds.radioButton(behavior_name, label="Behavior", select=True)
		cmds.radioButton(orientation_name, label="Orientation", select=False)


		cmds.text(label="Translation Mirror: ")
		self.ui_elements[translation_radio_collection] = cmds.radioCollection()

		cmds.radioButton(mirrored_name, label="Mirrored", select=True)
		cmds.radioButton(worldspace_name, label="World Space", select=False)

		cmds.setParent(self.ui_elements["top_column_layout"])
		cmds.text(label="")

	def cancel_window(self, *args):

		cmds.deleteUI(self.ui_elements["window"])

	def accept_window(self, *args):

		# a module info entry = (original_module, mirrored_module, mirror_plane, rotation_function, translation_function)

		self.module_info = []

		self.mirror_plane = cmds.radioCollection(
													self.ui_elements["mirror_plane_radio_collection"],
													query=True,
													select=True
												)

		for i in range(len(self.modules)):

			original_module = self.modules[i]
			original_module_name = self.module_names[i]

			original_module_prefix = original_module.partition("__")[0]
			mirrored_module_user_specified_name = cmds.textField(
																	self.ui_elements["module_name_"+original_module_name],
																	query=True,
																	text=True
																)

			mirrored_module_name = original_module_prefix+"__"+mirrored_module_user_specified_name

			if utils.does_blueprint_user_specified_name_exist(mirrored_module_user_specified_name):

				cmds.confirmDialog(
										title="Name Conflict",
										message="Name \""+mirrored_module_user_specified_name+"\" already exists, aborting mirror.",
										button=["Accept"],
										defaultButton="Accept"
									)
				return

			rotation_function = ""
			translation_function = ""

			if self.same_mirror_settings_for_all == True:

				rotation_function = cmds.radioCollection(
															self.ui_elements["rotation_radioCollection_all"],
															query=True,
															select=True
														)
				translation_function = cmds.radioCollection(
																self.ui_elements["translation_radioCollection_all"],
																query=True,
																select=True
															)

			else:

				rotation_function = cmds.radioCollection(
															self.ui_elements["rotation_radioCollection_"+original_module_name],
															query=True,
															select=True
														)
				translation_function = cmds.radioCollection(
																self.ui_elements["translation_radioCollection_"+original_module_name],
																query=True, 
																select=True
															)

			rotation_function = rotation_function.partition("__")[0]
			translation_function = translation_function.partition("__")[0]

			self.module_info.append([
										original_module,
										mirrored_module_name,
										self.mirror_plane,
										rotation_function,
										translation_function
									])

		cmds.deleteUI(self.ui_elements["window"])

		self.mirror_modules()

	def mirror_modules(self):

		mirror_modules_progress_ui = cmds.progressWindow(title="Mirroring Module(s)", status="This may take a few minutes...", isInteruptable=False)

		mirror_modules_progress = 0

		mirror_modules_progress_stage1_proportion = 15
		mirror_modules_progress_stage2_proportion = 70
		mirror_modules_progress_stage3_proportion = 10

		module_name_info = utils.find_all_module_names("/modules/blueprint")
		valid_modules = module_name_info[0]
		valid_module_names = module_name_info[1]

		for module in self.module_info:

			module_name = module[0].partition("__")[0]

			if module_name in valid_module_names:

				index = valid_module_names.index(module_name)
				module.append(valid_modules[index])

		mirror_modules_progress_progress_increment = mirror_modules_progress_stage1_proportion/len(self.module_info)

		for module in self.module_info:

			user_specified_name = module[0].partition("__")[2]
			mod = __import__("blueprint."+module[5], {}, {}, [module[5]])
			reload(mod)

			module_class = getattr(mod, mod.CLASS_NAME)
			module_inst = module_class(user_specified_name, None)

			hook_object = module_inst.find_hook_obj()

			new_hook_object = None

			hook_module = utils.strip_leading_namespace(hook_object)[0]

			hook_found = False

			for m in self.module_info:

				if hook_module == m[0]:

					hook_found = True

					if m == module:

						continue

					hook_object_name = utils.strip_leading_namespace(hook_object)[1]

					new_hook_object = m[1]+":"+hook_object_name

			if not hook_found:

				new_hook_object = hook_object

			module.append(new_hook_object)

			hook_constrained = module_inst.is_root_constrained()

			module.append(hook_constrained)

			mirror_modules_progress += mirror_modules_progress_progress_increment
			cmds.progressWindow(mirror_modules_progress_ui, edit=True, progress=mirror_modules_progress)

		mirror_modules_progress_progress_increment = mirror_modules_progress_stage2_proportion/len(self.module_info)
		
		for module in self.module_info:

			new_user_specified_name = module[1].partition("__")[2]

			mod = __import__("blueprint."+module[5], {}, {}, [module[5]])
			reload(mod)

			module_class = getattr(mod, mod.CLASS_NAME)
			module_inst = module_class(new_user_specified_name, None)

			module_inst.mirror(module[0], module[2], module[3], module[4])

			mirror_modules_progress += mirror_modules_progress_progress_increment
			cmds.progressWindow(mirror_modules_progress_ui, edit=True, progress=mirror_modules_progress)

		cmds.progressWindow(mirror_modules_progress_ui, edit=True, endProgress=True)

		utils.force_scene_update()




	