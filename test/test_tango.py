"""
This file can be used with `pytest`.

The following way to execute the whole tests.
```
pytest test/test.py
```

Or the following way to execute a single test.
```
pytest test/test.py::test_internal_trigger
```

"""

import numpy
import time
import logging
import pytest
from Lima import Core
from unittest import mock

try:
    from Lima.Server.camera import Simulator

    Camera = Simulator.Simulator
except:
    # Skip this tests if lima-camera-simulator-tango was not installed
    pytestmark = pytest.mark.skip

    class Camera:
        pass


_logger = logging.getLogger(__name__)


class MockedSimulator(Camera):
    def __init__(self, properties=None):
        """
        Attributes:
            properties: Simulate the tango device properties
        """
        if properties is None:
            properties = {}
        for k, v in Simulator.SimulatorClass.device_property_list.items():
            setattr(self, k, v[2])
        for k, v in properties.items():
            setattr(self, k, v)
        with mock.patch("PyTango.Device_4Impl.__init__"):
            super(MockedSimulator, self).__init__()

    def set_state(self, state):
        self.__state = state

    def get_device_properties(self, ds_class=None):
        pass


@pytest.fixture(scope="function")
def cleanup_simulator():
    Simulator.Simulator._SimuCamera = None
    Simulator.Simulator._SimuInterface = None
    yield
    Simulator.Simulator._SimuCamera = None
    Simulator.Simulator._SimuInterface = None


def test_property_mode(cleanup_simulator):
    """Setup the mode from tango properties

    Check that the mode was set
    """
    ct = Simulator.get_control()
    properties = {"mode": "LOADER"}
    tango = MockedSimulator(properties)
    camera = tango._SimuCamera
    assert camera.getMode() == Simulator.Simulator._Mode["LOADER"]


def test_property_peaks_str(cleanup_simulator):
    """Setup the mode from tango properties

    Check that the mode was set
    """
    ct = Simulator.get_control()
    properties = {"peaks": "10,20,30,40"}
    tango = MockedSimulator(properties)
    camera = tango._SimuCamera
    peaks = camera.getFrameGetter().getPeaks()
    assert len(peaks) == 1
    assert peaks[0].x0 == 10
    assert peaks[0].max == 40


def test_property_peaks_list(cleanup_simulator):
    """Setup the mode from tango properties

    Check that the mode was set
    """
    ct = Simulator.get_control()
    properties = {"peaks": [10, 20, 30, 40]}
    tango = MockedSimulator(properties)
    camera = tango._SimuCamera
    peaks = camera.getFrameGetter().getPeaks()
    assert len(peaks) == 1
    assert peaks[0].x0 == 10
    assert peaks[0].max == 40


@pytest.mark.skip(reason="setPeakAngles is not usable with list")
def test_property_peak_angles_str(cleanup_simulator):
    """Setup the mode from tango properties

    Check that the mode was set
    """
    ct = Simulator.get_control()
    properties = {"peak_angles": "10,20,30,40"}
    tango = MockedSimulator(properties)
    camera = tango._SimuCamera
    peaks = camera.getFrameGetter().getPeakAngles()
    assert len(peaks) == 4
    assert peaks == [10, 20, 30, 40]


@pytest.mark.skip(reason="setPeakAngles is not usable with list")
def test_property_peak_angles_list(cleanup_simulator):
    """Setup the mode from tango properties

    Check that the mode was set
    """
    ct = Simulator.get_control()
    properties = {"peak_angles": [10, 20, 30, 40]}
    tango = MockedSimulator(properties)
    camera = tango._SimuCamera
    peaks = camera.getFrameGetter().getPeakAngles()
    assert len(peaks) == 4
    assert peaks == [10, 20, 30, 40]


def test_property_frame_dim(cleanup_simulator):
    """Setup frame_dim as tango property

    Check that the frame_dim was set
    """
    ct = Simulator.get_control()
    properties = {"frame_dim": [10, 20, 4]}
    tango = MockedSimulator(properties)
    camera = tango._SimuCamera
    frame_dim = camera.getFrameDim()
    assert frame_dim.getSize().getWidth() == 10
    assert frame_dim.getSize().getHeight() == 20
    assert frame_dim.getImageType() == Core.Bpp32


def test_property_fill_type(cleanup_simulator):
    """Setup the fill_type from tango properties

    Check that the fill_type was set
    """
    ct = Simulator.get_control()
    properties = {"fill_type": "EMPTY"}
    tango = MockedSimulator(properties)
    camera = tango._SimuCamera
    fill_type = camera.getFrameGetter().getFillType()
    assert fill_type == Simulator.Simulator._FillType["EMPTY"]
