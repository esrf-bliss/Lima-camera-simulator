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

# python3 compat
try:
    from itertools import izip as zip
except ImportError:
    pass

from Lima.Server import AttrHelper

from Lima import Core
from Lima import Simulator as SimuMod

def grouper(n, iterable, padvalue=None):
    return zip(*[itertools.chain(iterable, itertools.repeat(padvalue, n-1))]*n)


class Simulator(PyTango.Device_4Impl):

#------------------------------------------------------------------
#    Static properties
#------------------------------------------------------------------
    _Mode = {
        'GENERATOR': SimuMod.Camera.MODE_GENERATOR,
        'GENERATOR_PREFETCH': SimuMod.Camera.MODE_GENERATOR_PREFETCH,
        'LOADER': SimuMod.Camera.MODE_LOADER,
        'LOADER_PREFETCH': SimuMod.Camera.MODE_LOADER_PREFETCH,
	}

    _invMode = {v: k for k, v in _Mode.items()}

    _RotationAxis = {
        'ROTATIONX': SimuMod.FrameBuilder.RotationX,
        'ROTATIONY': SimuMod.FrameBuilder.RotationY,
	}

    _FillType = {
        'GAUSS':       SimuMod.FrameBuilder.Gauss,
        'DIFFRACTION': SimuMod.FrameBuilder.Diffraction,
	}

    Core.DEB_CLASS(Core.DebModApplication, 'LimaSimulator')

#------------------------------------------------------------------
#    Device constructor
#------------------------------------------------------------------
    def __init__(self,*args) :
        PyTango.Device_4Impl.__init__(self,*args)

        # Leagcy code used by AttrHelper
        # switch to the new pyTango please
        self.__Mode = {
            'GENERATOR': SimuMod.Camera.MODE_GENERATOR,
            'GENERATOR_PREFETCH': SimuMod.Camera.MODE_GENERATOR_PREFETCH,
            'LOADER': SimuMod.Camera.MODE_LOADER,
            'LOADER_PREFETCH': SimuMod.Camera.MODE_LOADER_PREFETCH,
    	}

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

        # Load the properties
        self.get_device_properties(self.get_device_class())

        # Apply properties if any
        if self.frame_dim:
            frame_dim = self.getFrameDimFromLongArray(self.frame_dim)
            _SimuCamera.setFrameDim(frame_dim)

        if self.mode and (Simulator._Mode.get(self.mode) != None):
            _SimuCamera.setMode(Simulator._Mode[self.mode])

        if 'PREFETCH' in self.mode and self.nb_prefetched_frames:
            _SimuCamera.getFrameGetter().setNbPrefetchedFrames(self.nb_prefetched_frames)

    @Core.DEB_MEMBER_FUNCT
    def getFrameDimFromLongArray(self, dim_arr):
        width, height, depth = dim_arr
        if depth == 1:
            image_type = Core.Bpp8
        elif depth == 2:
            image_type = Core.Bpp16
        elif depth == 4:
            image_type = Core.Bpp32
        else:
            raise ValueError('Unknown pixel depth: %d' % depth)
        return Core.FrameDim(width, height, image_type)

    @Core.DEB_MEMBER_FUNCT
    def getLongArrayFromFrameDim(self, frame_dim):
        size = frame_dim.getSize()
        return [size.getWidth(), size.getHeight(), frame_dim.getDepth()]

    @Core.DEB_MEMBER_FUNCT
    def getAttrStringValueList(self, attr_name):
        return AttrHelper.get_attr_string_value_list(self, attr_name)

    def trigExternal(self):
        _SimuCamera.extTrigAcq()

    def __getattr__(self, name):
        try:
            return AttrHelper.get_attr_4u(self, name, _SimuCamera.getFrameGetter(), False)
        except:
            return AttrHelper.get_attr_4u(self, name, _SimuCamera)

    @staticmethod
    def getGaussPeaksFromFloatArray(peak_list_flat):
        peak_list = grouper(4, map(float, peak_list_flat))
        gauss_peaks = [SimuMod.GaussPeak(*p) for p in peak_list]
        return gauss_peaks

    def read_peaks(self,attr):
        gauss_peaks = _SimuCamera.getFrameGetter().getPeaks()
        peak_list = [(p.x0, p.y0, p.fwhm, p.max) for p in gauss_peaks]
        peak_list_flat = list(itertools.chain(*peak_list))
        attr.set_value(peak_list_flat)

    def write_peaks(self,attr) :
        peak_list_flat = attr.get_write_value()
        gauss_peaks = self.getGaussPeaksFromFloatArray(peak_list_flat)
        _SimuCamera.getFrameGetter().setPeaks(gauss_peaks)

    def read_peak_angles(self,attr) :
        peak_angle_list = _SimuCamera.getFrameGetter().getPeakAngles()
        attr.set_value(peak_angle_list)

    def write_peak_angles(self,attr) :
        peak_angle_list = attr.get_write_value()
        _SimuCamera.getFrameGetter().setPeakAngles(map(float, peak_angle_list))

    def read_diffraction_pos(self,attr) :
        x, y = _SimuCamera.getFrameGetter().getDiffractionPos()
        attr.set_value((x, y))

    def write_diffraction_pos(self,attr) :
        x, y = attr.get_write_value()
        _SimuCamera.getFrameGetter().setDiffractionPos(x, y)

    def read_diffraction_speed(self,attr) :
        sx, sy = _SimuCamera.getFrameGetter().getDiffractionSpeed()
        attr.set_value((sx, sy))

    def write_diffraction_speed(self,attr) :
        sx, sy = attr.get_write_value()
        _SimuCamera.getFrameGetter().setDiffractionSpeed(sx, sy)

    def read_nb_prefetched_frames(self,attr) :
        if (_SimuCamera.getMode() == SimuMod.Camera.MODE_GENERATOR_PREFETCH) or \
           (_SimuCamera.getMode() == SimuMod.Camera.MODE_LOADER_PREFETCH) :
            nb_prefetched_frames = _SimuCamera.getFrameGetter().getNbPrefetchedFrames()
        else :
            nb_prefetched_frames = 0
        attr.set_value(nb_prefetched_frames)

    def read_frame_dim(self,attr) :
        frame_dim = _SimuCamera.getFrameDim()
        dim_arr = self.getLongArrayFromFrameDim(frame_dim)
        attr.set_value(dim_arr)

    def write_frame_dim(self,attr) :
        dim_arr = attr.get_write_value()
        frame_dim = self.getFrameDimFromLongArray(dim_arr)
        _SimuCamera.setFrameDim(frame_dim)

class SimulatorClass(PyTango.DeviceClass):

    class_property_list = {}

    device_property_list = {
        'frame_dim':
        [PyTango.DevVarLongArray,
         "Frame dimension in the form: width, height, depth", []],
        'mode':
        [PyTango.DevString,
         "Simulator mode: GENERATOR, GENERATOR_PREFETCH, LOADER, LOADER_PREFETCH",[]],
        'nb_prefetched_frames':
        [PyTango.DevLong,
         "Number of prefetched frames",[]],
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
        "trigExternal": [[PyTango.DevVoid, ""], [PyTango.DevVoid, ""]],
    }

    attr_list = {
        # Simulator mode
        'frame_dim':
        [[PyTango.DevLong,
          PyTango.SPECTRUM,
          PyTango.READ_WRITE, 3]],
        'mode':
        [[PyTango.DevString,
          PyTango.SCALAR,
          PyTango.READ_WRITE]],
        # Simulator with prefetch
        'nb_prefetched_frames':
        [[PyTango.DevLong,
          PyTango.SCALAR,
          PyTango.READ_WRITE]],
        # Simulator in loader mode
        'file_pattern':
        [[PyTango.DevString,
          PyTango.SCALAR,
          PyTango.WRITE]],
        # Simulator in generator mode
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
_SimuInterface = None

def get_control(peaks=[], peak_angles=[], **keys) :
    global _SimuCamera, _SimuInterface
    if _SimuInterface is None:

        # If initial mode is specified, pass it to the constructor
        if 'mode' in keys:
            mode = Simulator._Mode[keys['mode']]
            _SimuCamera = SimuMod.Camera(mode)
        else:
            _SimuCamera = SimuMod.Camera()

        _SimuInterface = SimuMod.Interface(_SimuCamera)

        if peaks:
            if (type(peaks) != str and getattr(peaks, '__getitem__', None) and
                type(peaks[0]) == str):
                peaks = ','.join(peaks)
            if type(peaks) == str:
                peaks = map(float, peaks.split(','))
            gauss_peaks = Simulator.getGaussPeaksFromFloatArray(peaks)
            _SimuCamera.getFrameGetter().setPeaks(gauss_peaks)
        if peak_angles:
            if type(peak_angles) == str:
                peak_angles = peak_angles.split(',')
            if type(peak_angles[0]) == str:
                peak_angles = map(float, peak_angles)
            _SimuCamera.getFrameGetter().setPeakAngles(peak_angles)

    return Core.CtControl(_SimuInterface)

def get_tango_specific_class_n_device():
    return SimulatorClass,Simulator
