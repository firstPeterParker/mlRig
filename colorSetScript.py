'''
Author: Matthew Lowe

Description: This script is meant to generate a second color set for the selected 
			 geomorty given it has a current default color set. The second color
			 set will generate and store varying gray scale vertex color values
			 for each vertex. The goal is to add a noise gradient to "colorSet2".

User Interface: The user has the ability to create a colorSet1 or colorSet2 depending
				on if the selected object already has a color set. Also being able to 
				change the minimum and maximum values of the vertex color, with the
				abilty to randomize the gray scale noise for colorSet2.

How to Run:

import sys
sys.path.append(r"Directory URL Here")
import colorSetScript as css
reload(css)

color_set = css.ColorSet()
color_set.main_ui()


'''

#Imported modules
import maya.cmds as cmds
import random as rand
from functools import partial


#Class
class ColorSet():

	#Initual method
	def __init__(self):

		'''

		__init__ has been left empty so that other artists can call
		on this class and use it's attributes if needed.

		'''
		print "Color Set Tool Activated"
	
	#Create main UI method
	def main_ui(self):

		'''

		main_ui consists of the UI elements for the Color Set Tool.
		Each UI element will be stored in a dictionary for easy use.


		'''

		#empty dictionary for UI elements
		self.ui_elements = {}

		#delete window if it already exists
		if cmds.window("colorSetWindow", exists=True):
			cmds.deleteUI("colorSetWindow")

		#default values for the window
		self.window_width = 100
		self.window_height = 100
		self.column_Width = 75

		#main window
		self.ui_elements["main_window"] = cmds.window(
															"colorSetWindow",
															title="Color Set Tool",
															width=self.window_width,
															height=self.window_height,
															sizeable=False,
															closeCommand=self.delete_script_job
														)

		#main column
		self.ui_elements["top_column"] = cmds.columnLayout(
																adjustableColumn=True,
																columnAlign="center",
																adj=True
															)

		#text field for selected item
		self.ui_elements["item_textfield"] = cmds.textFieldGrp(
																	label="Selected Item",
																	columnWidth=[1, self.column_Width],
																	text="Please select an object",
																	columnAlign=(1, "left"),
																	editable=False
																)

		#separator
		cmds.separator()

		#create color set button
		self.ui_elements["colorset_btn"] = cmds.button(
															label="Create Color Set",
															width=self.window_width,
															align="center",
															command=partial(self.create_color_set)
														)

		#separator
		cmds.separator()

		#minimum value slider
		self.ui_elements["min_slider"] = cmds.intSliderGrp(
																"minimum",
																columnAlign=(1, "left"),
																columnWidth=[1, self.column_Width],
																label="Min Value",
																field=True,
																minValue=0,
																maxValue=100,
																value=20
															)

		#maximum value slider
		self.ui_elements["max_slider"] = cmds.intSliderGrp(
																"maximum",
																columnAlign=(1, "left"),
																columnWidth=[1, self.column_Width],
																label="Max Value",
																field=True,
																minValue=0,
																maxValue=100,
																value=80
															)

		#separator
		cmds.separator()

		#randomize button for colorset2
		self.ui_elements["random_button"] = cmds.button(
															label="Randomize",
															width=self.window_width,
															align="center",
															enable=True,
															command=partial(self.main)
														)

		#show the main window
		cmds.showWindow(self.ui_elements["main_window"])

		#pointer to script job method
		self.create_script_job()

	#color set creation method
	def create_color_set(self, *args):

		'''

		This method will create the initial Color Sets that are needed.
		It will also check to see if color sets currently exist in the
		scene and if not it will create a default color set then create
		color set 2.

		'''

		print "Creating Color Set"

		selected_obj = cmds.ls(selection=True)

		#Error message if the use has not selected anything
		if not selected_obj:

			cmds.confirmDialog(
									title="Error Message",
									message="No objects selected. Must select one object!",
									button="Accept"
								)
			return False

		color_sets = cmds.polyColorSet(query=True, allColorSets=True)

		# Create colorSet1 if it does not exist
		if not color_sets:

			print "Creating ColorSet1"
			cmds.polyColorSet(create=True, rpt="RBGA", colorSet="colorSet1")

		# Create colorSet2 
		print "Creating ColorSet2"
		cmds.polyColorSet(create=True, rpt="RBGA", colorSet="colorSet2")
		cmds.polyColorSet(currentColorSet=True, colorSet= 'colorSet2' )

		self.main()

	# randomize colorSet2 method
	def main(self, *args):

		'''

		This method will be the main function of the tool letting the
		user generate random values for the color set 2.

		'''

		selected_obj = cmds.ls(selection=True)

		#Warning message for no selection
		if not selected_obj:

			cmds.confirmDialog(
									title="Error Message",
									message="No objects selected. Must select one object!",
									button="Accept"
								)
			return False

		color_sets = cmds.polyColorSet(query=True, allColorSets=True)

		#Warning message for no current color sets
		if not color_sets:

			cmds.confirmDialog(
									title="Error Message",
									message="Must create color set two!",
									button="Accept"
								)
			return False

		#If statement generates random values based on the users input for Minimum and Maximum sliders
		if "colorSet2" in color_sets:

			for index in xrange(cmds.polyEvaluate(selected_obj[0], vertex=True)):

				#slider values
				min_value = cmds.intSliderGrp("minimum", query=True, value=True)
				max_value = cmds.intSliderGrp("maximum", query=True, value=True)

				generate_value = rand.randint(min_value, max_value)
				color_value = generate_value/100.00

				color_set = cmds.polyColorPerVertex(
														"{object}.vtx[{number}]".format(object=selected_obj[0], number=index),
														rgb=( color_value, color_value, color_value)
													)
		#Error Message if colorSet2 does not exist
		else:

			cmds.confirmDialog(
									title="Error Message",
									message="Must create color set two!",
									button="Accept"
								)
			return False

	#Script job to update the UI based on selection change
	def create_script_job(self):

		'''
		The script job is being stored into a variable so that
		it can be killed later when the user decided to close
		the UI. The script job is being killed so that the scene
		stays clean.

		'''

		print "Creating Script Job"
		self.job_num = cmds.scriptJob(
										event=["SelectionChanged", self.modify_selected],
										parent=self.ui_elements["main_window"]
									)

	#Kills script job function
	def delete_script_job(self):

		print "Killing Script Job"
		cmds.scriptJob(kill=self.job_num)

	#Function to modify the selection amd send 
	def modify_selected(self, *args):

		'''

		modify_seleceted is a method so that the UI can be
		automaticly updated on which object, if any, is being
		selected in the scene.

		'''

		current_selection = cmds.ls(selection=True)

		#If statement to indicate what the current selection is or is not 
		if not current_selection:

			#No object selected
			cmds.textFieldGrp(
									self.ui_elements["item_textfield"],
									edit=True,
									text='No object is selected',
								)

		else:

			#Object that is selected
			cmds.textFieldGrp(
									self.ui_elements["item_textfield"],
									edit=True,
									text=current_selection[0],
								)
