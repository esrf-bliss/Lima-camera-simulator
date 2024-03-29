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
from Lima import Core, Simulator


_logger = logging.getLogger(__name__)


def wait_for(predicate, timeout = 10):
    """ Utility to wait for a given predicate until timeout """
    t = time.process_time()
    for _ in range(timeout):
        if predicate():
            break
        time.sleep(0.1)
    else:
        elapsed_time = time.process_time() - t
        assert False, f"Simulator is still running after {elapsed_time}"


class AcquisitionStatusFromImageStatusCallback(Core.CtControl.ImageStatusCallback):
    def __init__(self):
        super().__init__()
        self.last_base_image_ready = -1
        self.last_image_acquired = -1
        self.last_image_ready = -1
        self.last_image_saved = -1
        self.last_counter_ready = -1

    def imageStatusChanged(self, image_status):
        self.last_base_image_ready = image_status.LastBaseImageReady
        self.last_image_acquired = image_status.LastImageAcquired
        self.last_image_ready = image_status.LastImageReady
        self.last_image_saved = image_status.LastImageSaved
        self.last_counter_ready = image_status.LastCounterReady

def test_internal_trigger():
    cam = Simulator.Camera()
    hw = Simulator.Interface(cam)
    ct = Core.CtControl(hw)

    acq_status = AcquisitionStatusFromImageStatusCallback()
    ct.registerImageStatusCallback(acq_status)

    ct.prepareAcq()
    ct.startAcq()

    while ct.getStatus().AcquisitionStatus != Core.AcqReady:
        time.sleep(0.1)

    # Counter status are updated asynchronously (in another thread)
    wait_for(lambda : acq_status.last_image_ready == 0)
    assert acq_status.last_image_ready == 0


def test_internal_trigger_multi():
    cam = Simulator.Camera()
    hw = Simulator.Interface(cam)
    ct = Core.CtControl(hw)

    acq_status = AcquisitionStatusFromImageStatusCallback()
    ct.registerImageStatusCallback(acq_status)

    acq = ct.acquisition()
    acq.setTriggerMode(Core.IntTrigMult)
    acq.setAcqNbFrames(3)
    acq.setAcqExpoTime(0.01)

    ct.prepareAcq()
    for _ in range(3):
        time.sleep(0.1)
        ct.startAcq()
        # Make sure the detector is ready for next image
        while hw.getStatus().acq != Core.AcqReady:
            time.sleep(0.1)

    while ct.getStatus().AcquisitionStatus != Core.AcqReady:
        time.sleep(0.1)

    # Counter status are updated asynchronously (in another thread)
    wait_for(lambda : acq_status.last_image_ready == 2)
    assert acq_status.last_image_ready == 2


def test_external_trigger_single():
    cam = Simulator.Camera()
    hw = Simulator.Interface(cam)
    ct = Core.CtControl(hw)

    acq_status = AcquisitionStatusFromImageStatusCallback()
    ct.registerImageStatusCallback(acq_status)

    acq = ct.acquisition()
    acq.setTriggerMode(Core.ExtTrigSingle)
    acq.setAcqNbFrames(3)
    acq.setAcqExpoTime(0.01)

    ct.prepareAcq()
    ct.startAcq()     # arm
    cam.extTrigAcq()  # simulate an external trigger

    while ct.getStatus().AcquisitionStatus != Core.AcqReady:
        time.sleep(0.1)

    # Counter status are updated asynchronously (in another thread)
    wait_for(lambda : acq_status.last_image_ready == 2)
    assert acq_status.last_image_ready == 2


def test_external_trigger_multi():
    cam = Simulator.Camera()
    hw = Simulator.Interface(cam)
    ct = Core.CtControl(hw)

    acq_status = AcquisitionStatusFromImageStatusCallback()
    ct.registerImageStatusCallback(acq_status)

    acq = ct.acquisition()
    acq.setTriggerMode(Core.ExtTrigMult)
    acq.setAcqNbFrames(3)
    acq.setAcqExpoTime(0.01)

    ct.prepareAcq()
    ct.startAcq()         # arm
    for _ in range(3):
        cam.extTrigAcq()  # simulate an external trigger
        time.sleep(0.1)
        # Make sure the detector is ready for next image
        while hw.getStatus().acq != Core.AcqReady:
            time.sleep(0.1)

    while ct.getStatus().AcquisitionStatus != Core.AcqReady:
        time.sleep(0.1)

    # Counter status are updated asynchronously (in another thread)
    wait_for(lambda : acq_status.last_image_ready == 2)
    assert acq_status.last_image_ready == 2


def test_small_detector_size():
    """Change the size of the simulator

    Make sure the hardware detector size matches the request
    """
    cam = Simulator.Camera()
    hw = Simulator.Interface(cam)
    ct = Core.CtControl(hw)
    cam.setFrameDim(Core.FrameDim(100, 100, Core.Bpp32))
    dim = ct.image().getImageDim()
    assert dim.getSize() == Core.Size(100, 100)

    detinfo = hw.getHwCtrlObj(Core.HwCap.DetInfo)
    assert detinfo.getMaxImageSize() == Core.Size(100, 100)


def test_big_detector_size():
    """Change the size of the simulator

    Make sure the hardware detector size matches the request
    """
    cam = Simulator.Camera()
    hw = Simulator.Interface(cam)
    ct = Core.CtControl(hw)
    cam.setFrameDim(Core.FrameDim(2048, 2000, Core.Bpp32))
    dim = ct.image().getImageDim()
    assert dim.getSize() == Core.Size(2048, 2000)

    detinfo = hw.getHwCtrlObj(Core.HwCap.DetInfo)
    assert detinfo.getMaxImageSize() == Core.Size(2048, 2000)


def test_update_mode():
    """Change the simulator mode of the detector

    Check that the size have not changed
    """
    cam = Simulator.Camera()
    hw = Simulator.Interface(cam)
    ct = Core.CtControl(hw)
    cam.setFrameDim(Core.FrameDim(100, 100, Core.Bpp32))
    dim = ct.image().getImageDim()
    assert dim.getSize() == Core.Size(100, 100)

    new_mode = Simulator.Camera.MODE_GENERATOR_PREFETCH
    cam.setMode(new_mode)

    dim = ct.image().getImageDim()
    assert dim.getSize() == Core.Size(100, 100)


def test_default_pixel_size():
    """Create the simulator camera

    Check the default pixel size
    """
    cam = Simulator.Camera()
    hw = Simulator.Interface(cam)
    detInfo = hw.getHwCtrlObj(Core.HwCap.DetInfo)
    pixelsize = detInfo.getPixelSize()
    assert pixelsize == (1e-6, 1e-6)


def test_custom_pixel_size():
    """Change the simulator pixel size

    Check that the pixel size is the expected one
    """
    cam = Simulator.Camera()
    cam.setPixelSize(1e-3, 1e-4)
    hw = Simulator.Interface(cam)
    detInfo = hw.getHwCtrlObj(Core.HwCap.DetInfo)
    pixelsize = detInfo.getPixelSize()
    assert pixelsize == (1e-3, 1e-4)

def test_custom_frame():

    process_count = 0

    class MyCamera(Simulator.Camera):
        def fillData(self, data):
            nonlocal process_count
            assert data.frameNumber == 0
            assert data.buffer.shape == (1024, 1024)
            assert data.buffer.dtype == numpy.uint32
            # The buffer is writable
            data.buffer[0, 0] = 1
            data.buffer[-1, -1] = 1
            process_count += 1

    cam = MyCamera()
    hw = Simulator.Interface(cam)
    ct = Core.CtControl(hw)

    ct.prepareAcq()
    ct.startAcq()

    wait_for(lambda: ct.getStatus().AcquisitionStatus != Core.AcqRunning, 100)
    assert process_count == 1


def test_gauss_fill():
    """
    Test that the gauss fill increase frame after frame
    """
    processed_frames = []

    class MyCamera(Simulator.Camera):
        def fillData(self, data):
            nonlocal processed_frames
            s = numpy.sum(data.buffer)
            processed_frames.append(s)

    cam = MyCamera()
    hw = Simulator.Interface(cam)
    ct = Core.CtControl(hw)

    acq = ct.acquisition()
    acq.setTriggerMode(Core.IntTrig)
    acq.setAcqNbFrames(3)
    acq.setAcqExpoTime(0.01)

    ct.prepareAcq()
    ct.startAcq()

    wait_for(lambda: ct.getStatus().AcquisitionStatus != Core.AcqRunning, 100)
    assert processed_frames == [1096524, 2225892, 3356544]


def test_empty_fill():
    """
    Test that the empty fill provides empty frames
    """
    processed_frames = []

    class MyCamera(Simulator.Camera):
        def fillData(self, data):
            nonlocal processed_frames
            s = numpy.sum(data.buffer)
            processed_frames.append(s)

    cam = MyCamera()
    cam.getFrameGetter().setFillType(Simulator.FrameBuilder.Empty)
    hw = Simulator.Interface(cam)
    ct = Core.CtControl(hw)

    acq = ct.acquisition()
    acq.setTriggerMode(Core.IntTrig)
    acq.setAcqNbFrames(3)
    acq.setAcqExpoTime(0.01)

    ct.prepareAcq()
    ct.startAcq()

    wait_for(lambda: ct.getStatus().AcquisitionStatus != Core.AcqRunning, 100)
    assert processed_frames == [0, 0, 0]
