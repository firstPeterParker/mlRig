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

		self.ui_elements["window"] = cmds.window("blueprint_ui_window", width=window_width, height=window_height, title="Blueprint Module UI", sizeable=False)

		self.ui_elements["top_level_column"] = cmds.columnLayout(adjustableColumn=True, columnAlign="center")

		# Setup tabs
		tab_height = 500
		self.ui_elements["tabs"] = cmds.tabLayout(height=tab_height, innerMarginWidth=5, innerMarginHeight=5)

		tab_width = cmds.tabLayout(self.ui_elements["tabs"], q=True, width=True)
		self.scroll_width = tab_width - 40

		self.initialize_module_tab(tab_height, tab_width)

		cmds.tabLayout(self.ui_elements["tabs"], edit=True, tabLabelIndex=([1, "Modules"]))

		# Display window
		cmds.showWindow(self.ui_elements["window"])

	def initialize_module_tab(self, tab_height, tab_width):
		scroll_height = tab_height # temp value

		self.ui_elements["module_column"] = cmds.columnLayout(adj=True, rs=3)

		self.ui_elements["module_frame_layout"] = cmds.frameLayout(height=scroll_height, collapsable=False, borderVisible=False, labelVisible=False)

		self.ui_elements["module_list_scroll"] = cmds.scrollLayout(hst=0)

		self.ui_elements["module_list_column"] = cmds.columnLayout(columnWidth=self.scroll_width, adj=True, rs=2)

		# First separator

		cmds.separator()

		for module in utils.find_all_modules("modules/blueprint"):
			self.create_module_install_button(module)
			cmds.setParent(self.ui_elements["module_list_column"])
			cmds.separator()

		cmds.setParent(self.ui_elements["module_column"])
		cmds.separator()

	def create_module_install_button(self, module):
		mod = __import__("blueprint." + module, {}, {}, [module])
		reload(mod)

		title = mod.TITLE 
		description = mod.DESCRIPTION 
		icon = mod.ICON 

		# Create UI
		button_size = 64
		row = cmds.rowLayout(numberOfColumns=2, columnWidth=([1, button_size]), adjustableColumn=2, columnAttach=([1, "both", 0],[2, "both", 5]))

		self.ui_elements["module_button_" + module] = cmds.symbolButton(width=button_size, height=button_size, image=icon, command=partial(self.install_module, module))

		text_column = cmds.columnLayout(columnAlign="center")
		cmds.text(align="center", width=self.scroll_width - button_size + 300, label=title)

		cmds.scrollField(text=description, editable=False, width=self.scroll_width - button_size + 300, height=button_size, wordWrap=True)

	def install_module(self, module, *args):
		basename = "instance_"
		
		cmds.namespace(setNamespace = ":")
		namespaces = cmds.namespaceInfo(listOnlyNamespaces=True)

		for i in range(len(namespaces)):
			if namespaces[i].find("__") != -1:
				namespaces[i] = namespaces[i].partition("__")[2]

		new_suffix = utils.find_highest_trailing_number(namespaces, basename) + 1

		user_specified_name = basename + str(new_suffix)

		mod = __import__("blueprint." + module, {}, {}, [module])
		reload(mod)

		module_class = getattr(mod, mod.CLASS_NAME)
		module_instance = module_class(user_specified_name)
		module_instance.install()

		


