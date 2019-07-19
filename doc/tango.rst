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
