Simulator Tango device
======================

This is the reference documentation of the Simulator Tango device.

you can also find some useful information about the camera models/prerequisite/installation/configuration/compilation in the :ref:`Simulator camera plugin <camera-simulator>` section.

Properties
----------

=============== =============== =============== =========================================================================
Property name	Mandatory	Default value	Description
=============== =============== =============== =========================================================================
peaks		No		N/A		A gauss peak list [x0,y0,w0,A0,x1,y1,w1,A1...]	
peak_angles	No		N/A		The base rotation angle for each peak
fill_type	No		Gauss		The image fill type:  Gauss or Diffraction	
rotation_axis	No		rotationy	Peak move policy: STATIC, ROTATIONX, ROTATIONY	
frame_dim	No		1024, 1024, 4	Size of the frame. Width, height, depth. The depth is one of 1, 2, 4
pixel_size	No		1e-6, 1e-6	Pixel size metadata in meter. Default is 1um pixel size
=============== =============== =============== =========================================================================

Attributes
----------
======================= ======= ======================= ======================================================================
Attribute name		RW	Type			Description
======================= ======= ======================= ======================================================================
peaks			rw	Spectrum,DevDouble      The gauss peak list [x0,y0,w0,A0,x1,y1,w1,A1...]	
peak_angles		rw	Spectrum,DevDouble	The base rotation angle for each peak
grow_factor		rw	DevDouble		The Grow factor for gauss peaks	
fill_type		rw	DevString		The image fill type:  Gauss or Diffraction
rotation_axis		rw	DevString	 	The rotation axis policy: Static, RotationX or RotationY	
diffraction_pos		rw	Spectrum,DevDouble	The source diplacement position: x and y	
diffraction_speed	rw	Spectrum,DevDouble	The source diplacement speed: sx and sy	
rotation_angle  	rw	DevDouble	 	The peak rotation angle in deg
rotation_speed  	rw	DevDouble	 	The peak rotation speed in deg/frame 
======================= ======= ======================= ======================================================================

Commands
--------

=======================	=============== =======================	===========================================
Command name		Arg. in		Arg. out		Description
=======================	=============== =======================	===========================================
Init			DevVoid 	DevVoid			Do not use
State			DevVoid		DevLong			Return the device state
Status			DevVoid		DevString		Return the device state as a string
getAttrStringValueList	DevString:	DevVarStringArray:	Return the authorized string value list for
			Attribute name	String value list	a given attribute name
=======================	=============== =======================	===========================================

Custom LimaCCDs camera simulator
--------------------------------

A custom camera simulator can be created following this recipe.

- Create a custom tango camera simulator
- Register this new module as a Lima camera entry point
- Set/update the tango database

Tango camera simulator
''''''''''''''''''''''

.. code-block:: python

   # module myproject.MySimulator.py

   from Lima import Core
   from Lima import Simulator
   import Lima.Server.camera.Simulator as TangoSimuMod

   class MyCamera(Simulator.Camera):
       """Derive the camera in order to custom the way to render the frame"""
       def fillData(self, data):
           # Increment the first pixel every frames
           data.buffer[0, 0] = data.buffer[0, 0] + 1

   class MySimulator(TangoSimuMod.Simulator):
       """Derive the tango device in order to handle extra attributes/properties/commands implementation"""

   class MySimulatorClass(TangoSimuMod.SimulatorClass):
       """Derive the tango device class in order to describe extra attributes/properties/commands"""

   # Plugin

   def get_control(**kwargs):
       return TangoSimuMod.get_control(
           _Camera=MyCamera,
           _Simulator=MySimulator,
           **kwargs)

   def get_tango_specific_class_n_device():
       return MySimulatorClass, MySimulator

Lima camera entry point
'''''''''''''''''''''''

Lima provides entry points for plugins and cameras.

This can be used to register our new camera.

This allows `LimaCCDs` launcher to found your camera from your project.

.. code-block:: python

   # setup.py

   setup(
      name=__name__,
      version=__version__,
      ...
      entry_points={
          "Lima_tango_camera": ["MySimulator = myproject.MySimulator"],
      },
   )

Database description
''''''''''''''''''''

This is a representation of the Tango database content.

.. code-block:: yaml

   personal_name: my_simulator
   server: LimaCCDs
   device:
   - class: MySimulator
     tango_name: id00/mysimulator/my_simulator
     properties:
       mode: GENERATOR_PREFETCH
       nb_prefetched_frames: 1      # Alloc a single frame in memory
       fill_type: EMPTY             # Let python filling the full frame
   - class: LimaCCDs
     properties:
       LimaCameraType: MySimulator  # Ask to use your custom camera

Start the tango device
''''''''''''''''''''''

.. code-block:: sh

   LimaCCDs my_simulator
