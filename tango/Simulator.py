############################################################################
# This file is part of LImA, a Library for Image Acquisition
#
# Copyright (C) : 2009-2011
# European Synchrotron Radiation Facility
# BP 220, Grenoble 38043
# FRANCE
#
# This is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This software is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, see <http://www.gnu.org/licenses/>.
############################################################################
#----------------------------------------------------------------------------
# The Simulator camera plugin TANGO interface
#----------------------------------------------------------------------------

import itertools
import PyTango

from Lima.Server import AttrHelper

from Lima import Core
from Lima import Simulator as SimuMod

def grouper(n, iterable, padvalue=None):
    return itertools.izip(*[itertools.chain(iterable, itertools.repeat(padvalue, n-1))]*n)


class Simulator(PyTango.Device_4Impl):

    Core.DEB_CLASS(Core.DebModApplication, 'LimaSimulator')

#------------------------------------------------------------------
#    Device constructor
#------------------------------------------------------------------
    def __init__(self,*args) :
        PyTango.Device_4Impl.__init__(self,*args)

        self.__RotationAxis = {
            'ROTATIONX': SimuMod.FrameBuilder.RotationX,
            'ROTATIONY': SimuMod.FrameBuilder.RotationY,
	}

        self.__FillType = {
            'GAUSS':       SimuMod.FrameBuilder.Gauss,
            'DIFFRACTION': SimuMod.FrameBuilder.Diffraction,
	}

        self.init_device()

#------------------------------------------------------------------
#    Device destructor
#------------------------------------------------------------------
    def delete_device(self):
        pass

#------------------------------------------------------------------
#    Device initialization
#------------------------------------------------------------------
    @Core.DEB_MEMBER_FUNCT
    def init_device(self):
        self.set_state(PyTango.DevState.ON)
        #self.get_device_properties(self.get_device_class())

    @Core.DEB_MEMBER_FUNCT
    def getAttrStringValueList(self, attr_name):
        return AttrHelper.get_attr_string_value_list(self, attr_name)

    def __getattr__(self,name) :
        return AttrHelper.get_attr_4u(self, name, _SimuFrameBuilder)

    @staticmethod
    def getGaussPeaksFromFloatArray(peak_list_flat):
        peak_list = grouper(4, map(float, peak_list_flat))
        gauss_peaks = [SimuMod.GaussPeak(*p) for p in peak_list]
        return gauss_peaks

    def read_peaks(self,attr):
        gauss_peaks = _SimuFrameBuilder.getPeaks()
        peak_list = [(p.x0, p.y0, p.fwhm, p.max) for p in gauss_peaks]
        peak_list_flat = list(itertools.chain(*peak_list))
        attr.set_value(map(float, peak_list_flat))

    def write_peaks(self,attr) :
        peak_list_flat = attr.get_write_value()
        gauss_peaks = self.getGaussPeaksFromFloatArray(peak_list_flat)
        _SimuFrameBuilder.setPeaks(gauss_peaks)

    def read_peak_angles(self,attr) :
        peak_angle_list = _SimuFrameBuilder.getPeakAngles()
        attr.set_value(peak_angle_list)

    def write_peak_angles(self,attr) :
        peak_angle_list = attr.get_write_value()
        _SimuFrameBuilder.setPeakAngles(map(float, peak_angle_list))

    def read_diffraction_pos(self,attr) :
        x, y = _SimuFrameBuilder.getDiffractionPos()
        attr.set_value((x, y))

    def write_diffraction_pos(self,attr) :
        x, y = attr.get_write_value()
        _SimuFrameBuilder.setDiffractionPos(x, y)

    def read_diffraction_speed(self,attr) :
        sx, sy = _SimuFrameBuilder.getDiffractionSpeed()
        attr.set_value((sx, sy))

    def write_diffraction_speed(self,attr) :
        sx, sy = attr.get_write_value()
        _SimuFrameBuilder.setDiffractionSpeed(sx, sy)


class SimulatorClass(PyTango.DeviceClass):

    class_property_list = {}

    device_property_list = {
        'peaks':
        [PyTango.DevVarDoubleArray,
         "Gauss peak list [x0,y0,w0,A0,x1,y1,w1,A1...]",[]],
        'peak_angles':
        [PyTango.DevVarDoubleArray,
         "Base rotation angle for each peak",[]],
        'fill_type':
        [PyTango.DevString,
         "Image fill type: GAUSS, DIFFRACTION",[]],
        'rotation_axis':
        [PyTango.DevString,
         "Peak move policy: STATIC, ROTATIONX, ROTATIONY",[]],
        }

    cmd_list = {
        'getAttrStringValueList':
        [[PyTango.DevString, "Attribute name"],
         [PyTango.DevVarStringArray, "Authorized String value list"]],
    }

    attr_list = {
        'peaks':
        [[PyTango.DevDouble,
          PyTango.SPECTRUM,
          PyTango.READ_WRITE, 4000]],
        'peak_angles':
        [[PyTango.DevDouble,
          PyTango.SPECTRUM,
          PyTango.READ_WRITE, 1000]],
        'grow_factor':
        [[PyTango.DevDouble,
          PyTango.SCALAR,
          PyTango.READ_WRITE]],
        'fill_type':
        [[PyTango.DevString,
          PyTango.SCALAR,
          PyTango.READ_WRITE]],
        'rotation_axis':
        [[PyTango.DevString,
          PyTango.SCALAR,
          PyTango.READ_WRITE]],
        'diffraction_pos':
        [[PyTango.DevDouble,
          PyTango.SPECTRUM,
          PyTango.READ_WRITE, 2]],
        'diffraction_speed':
        [[PyTango.DevDouble,
          PyTango.SPECTRUM,
          PyTango.READ_WRITE, 2]],
        'rotation_angle':
        [[PyTango.DevDouble,
          PyTango.SCALAR,
          PyTango.READ_WRITE]],
        'rotation_speed':
        [[PyTango.DevDouble,
          PyTango.SCALAR,
          PyTango.READ_WRITE]],
        }

    def __init__(self,name) :
        PyTango.DeviceClass.__init__(self,name)
        self.set_type(name)

#----------------------------------------------------------------------------
# Plugins
#----------------------------------------------------------------------------
_SimuCamera = None
_SimuFrameBuilder = None
_SimuInterface = None

def get_control(peaks=[], peak_angles=[], **keys) :
    global _SimuCamera, _SimuFrameBuilder, _SimuInterface
    if _SimuInterface is None:
        _SimuCamera = SimuMod.Camera()
        _SimuFrameBuilder = _SimuCamera.getFrameBuilder()
        _SimuInterface = SimuMod.Interface(_SimuCamera)

        if peaks:
            if (type(peaks) != str and getattr(peaks, '__getitem__', None) and
                type(peaks[0]) == str):
                peaks = ','.join(peaks)
            if type(peaks) == str:
                peaks = map(float, peaks.split(','))
            gauss_peaks = Simulator.getGaussPeaksFromFloatArray(peaks)
            _SimuFrameBuilder.setPeaks(gauss_peaks)
        if peak_angles:
            if type(peak_angles) == str:
                peak_angles = peak_angles.split(',')
            if type(peak_angles[0]) == str:
                peak_angles = map(float, peak_angles)
            _SimuFrameBuilder.setPeakAngles(peak_angles)

    return Core.CtControl(_SimuInterface)

def get_tango_specific_class_n_device():
    return SimulatorClass,Simulator
