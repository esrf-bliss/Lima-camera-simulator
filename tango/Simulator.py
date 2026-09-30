############################################################################
# This file is part of LImA, a Library for Image Acquisition
#
# Copyright (C) : 2009-2026
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
# ----------------------------------------------------------------------------
# The Simulator camera plugin TANGO interface
# ----------------------------------------------------------------------------

import itertools

from tango import AttrWriteType, DevState
from tango.server import Device, attribute, command, device_property

from lima.server import AttrHelper

from lima import core
from lima import simulator as SimuMod


def grouper(n, iterable, padvalue=None):
    return zip(*[itertools.chain(iterable, itertools.repeat(padvalue, n - 1))] * n)


class Simulator(Device):

    # ------------------------------------------------------------------
    #    Static properties
    # ------------------------------------------------------------------
    _SimuCamera = None
    """Reference to Lima simulator camera binding"""
    _SimuInterface = None
    """Reference to Lima simulator interface binding"""

    _Mode = {
        "GENERATOR": SimuMod.Camera.Mode.MODE_GENERATOR,
        "GENERATOR_PREFETCH": SimuMod.Camera.Mode.MODE_GENERATOR_PREFETCH,
        "LOADER": SimuMod.Camera.Mode.MODE_LOADER,
        "LOADER_PREFETCH": SimuMod.Camera.Mode.MODE_LOADER_PREFETCH,
    }

    _invMode = {v: k for k, v in _Mode.items()}

    _RotationAxis = {
        "ROTATIONX": SimuMod.FrameBuilder.RotationAxis.RotationX,
        "ROTATIONY": SimuMod.FrameBuilder.RotationAxis.RotationY,
    }

    _FillType = {
        "GAUSS": SimuMod.FrameBuilder.FillType.Gauss,
        "DIFFRACTION": SimuMod.FrameBuilder.FillType.Diffraction,
        "EMPTY": SimuMod.FrameBuilder.FillType.Empty,
    }

    core.DEB_CLASS(core.DebModule.DebModApplication, "LimaSimulator")

    # ------------------------------------------------------------------
    #    Device properties (initial hardware configuration only - the
    #    live attributes of the same name below read/write the camera
    #    directly, they don't share storage with these)
    # ------------------------------------------------------------------
    frame_dim = device_property(dtype=(int,), default_value=[])
    pixel_size = device_property(dtype=(float,), default_value=[])
    mode = device_property(dtype=str, default_value="")
    nb_prefetched_frames = device_property(dtype=int, default_value=0)
    peaks = device_property(dtype=(float,), default_value=[])
    peak_angles = device_property(dtype=(float,), default_value=[])
    fill_type = device_property(dtype=str, default_value="")
    rotation_axis = device_property(dtype=str, default_value="")

    # ------------------------------------------------------------------
    #    Device initialization
    # ------------------------------------------------------------------
    @core.DEB_MEMBER_FUNCT
    def init_device(self):
        Device.init_device(self)

        # Leagcy code used by AttrHelper.get_attr_string_value_list
        # switch to the new pyTango please
        self.__Mode = self._Mode
        self.__RotationAxis = self._RotationAxis
        self.__FillType = self._FillType

        # Apply properties if any
        if self.mode and (Simulator._Mode.get(self.mode) is not None):
            self._SimuCamera.setMode(Simulator._Mode[self.mode])

        if "PREFETCH" in self.mode and self.nb_prefetched_frames:
            self._SimuCamera.getFrameGetter().setNbPrefetchedFrames(
                self.nb_prefetched_frames
            )

        if self.frame_dim:
            frame_dim = self.getFrameDimFromLongArray(self.frame_dim)
            self._SimuCamera.setFrameDim(frame_dim)

        if self.pixel_size:
            pixel_size = self.pixel_size
            self._SimuCamera.setPixelSize(pixel_size[0], pixel_size[1])

        if self.peaks:
            peaks = self.peaks
            if isinstance(peaks, str):
                peaks = peaks.split(",")
            if isinstance(peaks[0], str):
                peaks = map(float, peaks)
            gauss_peaks = self.getGaussPeaksFromFloatArray(peaks)
            self._SimuCamera.getFrameGetter().setPeaks(gauss_peaks)

        if self.peak_angles:
            peak_angles = self.peak_angles
            if isinstance(peak_angles, str):
                peak_angles = peak_angles.split(",")
            if isinstance(peak_angles[0], str):
                peak_angles = map(float, peak_angles)
            self._SimuCamera.getFrameGetter().setPeakAngles(peak_angles)

        if self.fill_type and self.fill_type in Simulator._FillType:
            fill_type = Simulator._FillType[self.fill_type]
            self._SimuCamera.getFrameGetter().setFillType(fill_type)

        self.set_state(DevState.ON)

    @core.DEB_MEMBER_FUNCT
    def getFrameDimFromLongArray(self, dim_arr):
        width, height, depth = dim_arr
        if depth == 1:
            image_type = core.ImageType.Bpp8
        elif depth == 2:
            image_type = core.ImageType.Bpp16
        elif depth == 4:
            image_type = core.ImageType.Bpp32
        else:
            raise ValueError("Unknown pixel depth: %d" % depth)
        return core.FrameDim(width, height, image_type)

    @core.DEB_MEMBER_FUNCT
    def getLongArrayFromFrameDim(self, frame_dim):
        size = frame_dim.getSize()
        return [size.getWidth(), size.getHeight(), frame_dim.getDepth()]

    @staticmethod
    def getGaussPeaksFromFloatArray(peak_list_flat):
        peak_list = grouper(4, map(float, peak_list_flat))
        gauss_peaks = [SimuMod.GaussPeak(*p) for p in peak_list]
        return gauss_peaks

    # ------------------------------------------------------------------
    #    Commands
    # ------------------------------------------------------------------
    @command(dtype_in=str, dtype_out=(str,))
    @core.DEB_MEMBER_FUNCT
    def getAttrStringValueList(self, attr_name):
        return AttrHelper.get_attr_string_value_list(self, attr_name)

    @command
    def trigExternal(self):
        self._SimuCamera.extTrigAcq()

    # ------------------------------------------------------------------
    #    Attributes with custom read/write logic
    # ------------------------------------------------------------------
    def _frame_dim_fget(self):
        return self.getLongArrayFromFrameDim(self._SimuCamera.getFrameDim())

    def _frame_dim_fset(self, dim_arr):
        self._SimuCamera.setFrameDim(self.getFrameDimFromLongArray(dim_arr))

    frame_dim_attr = attribute(
        name="frame_dim",
        dtype=(int,),
        max_dim_x=3,
        access=AttrWriteType.READ_WRITE,
        doc="Size of the frame: width, height, depth (depth is one of 1, 2, 4)",
        fget=_frame_dim_fget,
        fset=_frame_dim_fset,
    )

    def _nb_prefetched_frames_fget(self):
        if self._SimuCamera.getMode() in (
            SimuMod.Camera.Mode.MODE_GENERATOR_PREFETCH,
            SimuMod.Camera.Mode.MODE_LOADER_PREFETCH,
        ):
            return self._SimuCamera.getFrameGetter().getNbPrefetchedFrames()
        return 0

    _, _nb_prefetched_frames_fset = AttrHelper.make_fget_fset(
        "nb_prefetched_frames", lambda self: self._SimuCamera.getFrameGetter()
    )

    nb_prefetched_frames_attr = attribute(
        name="nb_prefetched_frames",
        dtype=int,
        access=AttrWriteType.READ_WRITE,
        doc="Number of frames pre-fetched in memory (*_PREFETCH modes only)",
        fget=_nb_prefetched_frames_fget,
        fset=_nb_prefetched_frames_fset,
    )

    def _peaks_fget(self):
        gauss_peaks = self._SimuCamera.getFrameGetter().getPeaks()
        peak_list = [(p.x0, p.y0, p.fwhm, p.max) for p in gauss_peaks]
        return list(itertools.chain(*peak_list))

    def _peaks_fset(self, peak_list_flat):
        gauss_peaks = self.getGaussPeaksFromFloatArray(peak_list_flat)
        self._SimuCamera.getFrameGetter().setPeaks(gauss_peaks)

    peaks_attr = attribute(
        name="peaks",
        dtype=(float,),
        max_dim_x=4000,
        access=AttrWriteType.READ_WRITE,
        doc="The gauss peak list [x0,y0,w0,A0,x1,y1,w1,A1...]",
        fget=_peaks_fget,
        fset=_peaks_fset,
    )

    def _peak_angles_fget(self):
        return list(self._SimuCamera.getFrameGetter().getPeakAngles())

    def _peak_angles_fset(self, peak_angle_list):
        self._SimuCamera.getFrameGetter().setPeakAngles(list(map(float, peak_angle_list)))

    peak_angles_attr = attribute(
        name="peak_angles",
        dtype=(float,),
        max_dim_x=1000,
        access=AttrWriteType.READ_WRITE,
        doc="The base rotation angle for each peak",
        fget=_peak_angles_fget,
        fset=_peak_angles_fset,
    )

    def _file_pattern_fset(self, pattern):
        self._SimuCamera.getFrameGetter().setFilePattern(pattern)

    file_pattern_attr = attribute(
        name="file_pattern",
        dtype=str,
        access=AttrWriteType.WRITE,
        doc="File name pattern for the LOADER-mode frame source",
        fset=_file_pattern_fset,
    )

    def _diffraction_pos_fget(self):
        return self._SimuCamera.getFrameGetter().getDiffractionPos()

    def _diffraction_pos_fset(self, pos):
        x, y = pos
        self._SimuCamera.getFrameGetter().setDiffractionPos(x, y)

    diffraction_pos = attribute(
        dtype=(float,),
        max_dim_x=2,
        access=AttrWriteType.READ_WRITE,
        doc="The source displacement position: x and y",
        fget=_diffraction_pos_fget,
        fset=_diffraction_pos_fset,
    )

    def _diffraction_speed_fget(self):
        return self._SimuCamera.getFrameGetter().getDiffractionSpeed()

    def _diffraction_speed_fset(self, speed):
        sx, sy = speed
        self._SimuCamera.getFrameGetter().setDiffractionSpeed(sx, sy)

    diffraction_speed = attribute(
        dtype=(float,),
        max_dim_x=2,
        access=AttrWriteType.READ_WRITE,
        doc="The source displacement speed: sx and sy",
        fget=_diffraction_speed_fget,
        fset=_diffraction_speed_fset,
    )

    # ------------------------------------------------------------------
    #    Attributes fully dispatched by naming convention (no explicit
    #    logic in the legacy code either - see AttrHelper.make_fget_fset)
    # ------------------------------------------------------------------
    _mode_fget, _mode_fset = AttrHelper.make_fget_fset(
        "mode",
        lambda self: self._SimuCamera.getFrameGetter(),
        lambda self: self._SimuCamera,
        enum=_Mode,
    )
    mode_attr = attribute(
        name="mode",
        dtype=str,
        access=AttrWriteType.READ_WRITE,
        doc="Frame generation mode: GENERATOR, GENERATOR_PREFETCH, LOADER or LOADER_PREFETCH",
        fget=_mode_fget,
        fset=_mode_fset,
    )

    _fill_type_fget, _fill_type_fset = AttrHelper.make_fget_fset(
        "fill_type",
        lambda self: self._SimuCamera.getFrameGetter(),
        lambda self: self._SimuCamera,
        enum=_FillType,
    )
    fill_type_attr = attribute(
        name="fill_type",
        dtype=str,
        access=AttrWriteType.READ_WRITE,
        doc="The image fill type: Gauss or Diffraction",
        fget=_fill_type_fget,
        fset=_fill_type_fset,
    )

    _rotation_axis_fget, _rotation_axis_fset = AttrHelper.make_fget_fset(
        "rotation_axis",
        lambda self: self._SimuCamera.getFrameGetter(),
        lambda self: self._SimuCamera,
        enum=_RotationAxis,
    )
    rotation_axis_attr = attribute(
        name="rotation_axis",
        dtype=str,
        access=AttrWriteType.READ_WRITE,
        doc="The rotation axis policy: RotationX or RotationY",
        fget=_rotation_axis_fget,
        fset=_rotation_axis_fset,
    )

    _grow_factor_fget, _grow_factor_fset = AttrHelper.make_fget_fset(
        "grow_factor",
        lambda self: self._SimuCamera.getFrameGetter(),
        lambda self: self._SimuCamera,
    )
    grow_factor = attribute(
        dtype=float,
        access=AttrWriteType.READ_WRITE,
        doc="The grow factor for gauss peaks",
        fget=_grow_factor_fget,
        fset=_grow_factor_fset,
    )

    _rotation_angle_fget, _rotation_angle_fset = AttrHelper.make_fget_fset(
        "rotation_angle",
        lambda self: self._SimuCamera.getFrameGetter(),
        lambda self: self._SimuCamera,
    )
    rotation_angle = attribute(
        dtype=float,
        access=AttrWriteType.READ_WRITE,
        doc="The peak rotation angle in deg",
        fget=_rotation_angle_fget,
        fset=_rotation_angle_fset,
    )

    _rotation_speed_fget, _rotation_speed_fset = AttrHelper.make_fget_fset(
        "rotation_speed",
        lambda self: self._SimuCamera.getFrameGetter(),
        lambda self: self._SimuCamera,
    )
    rotation_speed = attribute(
        dtype=float,
        access=AttrWriteType.READ_WRITE,
        doc="The peak rotation speed in deg/frame",
        fget=_rotation_speed_fget,
        fset=_rotation_speed_fset,
    )

    _noise_level_fget, _noise_level_fset = AttrHelper.make_fget_fset(
        "noise_level", lambda self: self._SimuCamera.getFrameGetter()
    )
    noise_level = attribute(
        dtype=float,
        access=AttrWriteType.READ_WRITE,
        doc="Amount of noise added to generated frames",
        fget=_noise_level_fget,
        fset=_noise_level_fset,
    )


# ----------------------------------------------------------------------------
# Plugins
# ----------------------------------------------------------------------------


def get_control(
    peaks=[],
    peak_angles=[],
    mode=None,
    _Simulator=Simulator,
    _Camera=SimuMod.Camera,
    _Interface=SimuMod.Interface,
    **kwargs,
):
    """
    Called by LimaCCDs module to create Lima control object.

    In the simulator scope, it also create the Lima camera, Lima interface
    and register them into the Tango simulator class.

    Arguments:
        _Simulator: Tango class used to register Lima references
        _Camera: Lima class to create the camera instance
        _Interface: Lima class to create the interface instance
    """
    interface = _Simulator._SimuInterface
    camera = _Simulator._SimuCamera
    if interface is None:
        camera = _Camera()
        interface = _Interface(camera)
    control = core.CtControl(interface)
    _Simulator._SimuCamera = camera
    _Simulator._SimuInterface = interface
    return control


def get_tango_specific_class_n_device():
    return Simulator.TangoClassClass, Simulator
