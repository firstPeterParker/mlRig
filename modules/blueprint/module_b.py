'''

dumby module

'''
import os

CLASS_NAME = "ModuleB"

TITLE = "Module B"
DESCRIPTION = "Test description for module B"
ICON = os.environ["mlrig_tool"] + "/icons/_hinge.xpm"

class ModuleB():
	def __init__(self):
		print "we're in the constructor"

	def install(self):
		print "Install" + CLASS_NAME