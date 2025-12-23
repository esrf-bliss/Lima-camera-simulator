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
from lima import core, simulator


_logger = logging.getLogger(__name__)


def wait_for(predicate, timeout=10):
    """ Utility to wait for a given predicate until timeout """
    t = time.process_time()
    for _ in range(timeout):
        if predicate():
            break
        time.sleep(0.1)
    else:
        elapsed_time = time.process_time() - t
        assert False, f"simulator is still running after {elapsed_time}"


class AcquisitionStatusFromImageStatusCallback(core.CtControl.ImageStatusCallback):
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
    cam = simulator.Camera()
    hw = simulator.Interface(cam)
    ct = core.CtControl(hw)

    acq_status = AcquisitionStatusFromImageStatusCallback()
    ct.registerImageStatusCallback(acq_status)

    ct.prepareAcq()
    ct.startAcq()

    while ct.getStatus().AcquisitionStatus != core.AcqReady:
        time.sleep(0.1)

    # Counter status are updated asynchronously (in another thread)
    wait_for(lambda: acq_status.last_image_ready == 0)
    assert acq_status.last_image_ready == 0


def test_internal_trigger_multi():
    cam = simulator.Camera()
    hw = simulator.Interface(cam)
    ct = core.CtControl(hw)

    acq_status = AcquisitionStatusFromImageStatusCallback()
    ct.registerImageStatusCallback(acq_status)

    acq = ct.acquisition()
    acq.setTriggerMode(core.IntTrigMult)
    acq.setAcqNbFrames(3)
    acq.setAcqExpoTime(0.01)

    ct.prepareAcq()
    for _ in range(3):
        time.sleep(0.1)
        ct.startAcq()
        # Make sure the detector is ready for next image
        while hw.getStatus().acq != core.AcqReady:
            time.sleep(0.1)

    while ct.getStatus().AcquisitionStatus != core.AcqReady:
        time.sleep(0.1)

    # Counter status are updated asynchronously (in another thread)
    wait_for(lambda: acq_status.last_image_ready == 2)
    assert acq_status.last_image_ready == 2


def test_external_trigger_single():
    cam = simulator.Camera()
    hw = simulator.Interface(cam)
    ct = core.CtControl(hw)

    acq_status = AcquisitionStatusFromImageStatusCallback()
    ct.registerImageStatusCallback(acq_status)

    acq = ct.acquisition()
    acq.setTriggerMode(core.ExtTrigSingle)
    acq.setAcqNbFrames(3)
    acq.setAcqExpoTime(0.01)

    ct.prepareAcq()
    ct.startAcq()     # arm
    cam.extTrigAcq()  # simulate an external trigger

    while ct.getStatus().AcquisitionStatus != core.AcqReady:
        time.sleep(0.1)

    # Counter status are updated asynchronously (in another thread)
    wait_for(lambda: acq_status.last_image_ready == 2)
    assert acq_status.last_image_ready == 2


def test_external_trigger_multi():
    cam = simulator.Camera()
    hw = simulator.Interface(cam)
    ct = core.CtControl(hw)

    acq_status = AcquisitionStatusFromImageStatusCallback()
    ct.registerImageStatusCallback(acq_status)

    acq = ct.acquisition()
    acq.setTriggerMode(core.ExtTrigMult)
    acq.setAcqNbFrames(3)
    acq.setAcqExpoTime(0.01)

    ct.prepareAcq()
    ct.startAcq()         # arm
    for _ in range(3):
        cam.extTrigAcq()  # simulate an external trigger
        time.sleep(0.1)
        # Make sure the detector is ready for next image
        while hw.getStatus().acq != core.AcqReady:
            time.sleep(0.1)

    while ct.getStatus().AcquisitionStatus != core.AcqReady:
        time.sleep(0.1)

    # Counter status are updated asynchronously (in another thread)
    wait_for(lambda: acq_status.last_image_ready == 2)
    assert acq_status.last_image_ready == 2


def test_small_detector_size():
    """Change the size of the simulator

    Make sure the hardware detector size matches the request
    """
    cam = simulator.Camera()
    hw = simulator.Interface(cam)
    ct = core.CtControl(hw)
    cam.setFrameDim(core.FrameDim(100, 100, core.Bpp32))
    dim = ct.image().getImageDim()
    assert dim.getSize() == core.Size(100, 100)

    detinfo = hw.getHwCtrlObj(core.HwCap.DetInfo)
    assert detinfo.getMaxImageSize() == core.Size(100, 100)


def test_big_detector_size():
    """Change the size of the simulator

    Make sure the hardware detector size matches the request
    """
    cam = simulator.Camera()
    hw = simulator.Interface(cam)
    ct = core.CtControl(hw)
    cam.setFrameDim(core.FrameDim(2048, 2000, core.Bpp32))
    dim = ct.image().getImageDim()
    assert dim.getSize() == core.Size(2048, 2000)

    detinfo = hw.getHwCtrlObj(core.HwCap.DetInfo)
    assert detinfo.getMaxImageSize() == core.Size(2048, 2000)


def test_update_mode():
    """Change the simulator mode of the detector

    Check that the size have not changed
    """
    cam = simulator.Camera()
    hw = simulator.Interface(cam)
    ct = core.CtControl(hw)
    cam.setFrameDim(core.FrameDim(100, 100, core.Bpp32))
    dim = ct.image().getImageDim()
    assert dim.getSize() == core.Size(100, 100)

    new_mode = simulator.Camera.MODE_GENERATOR_PREFETCH
    cam.setMode(new_mode)

    dim = ct.image().getImageDim()
    assert dim.getSize() == core.Size(100, 100)


def test_default_pixel_size():
    """Create the simulator camera

    Check the default pixel size
    """
    cam = simulator.Camera()
    hw = simulator.Interface(cam)
    detInfo = hw.getHwCtrlObj(core.HwCap.DetInfo)
    pixelsize = detInfo.getPixelSize()
    assert pixelsize == (1e-6, 1e-6)


def test_custom_pixel_size():
    """Change the simulator pixel size

    Check that the pixel size is the expected one
    """
    cam = simulator.Camera()
    cam.setPixelSize(1e-3, 1e-4)
    hw = simulator.Interface(cam)
    detInfo = hw.getHwCtrlObj(core.HwCap.DetInfo)
    pixelsize = detInfo.getPixelSize()
    assert pixelsize == (1e-3, 1e-4)


def test_custom_frame():

    process_count = 0

    class MyCamera(simulator.Camera):
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
    hw = simulator.Interface(cam)
    ct = core.CtControl(hw)

    ct.prepareAcq()
    ct.startAcq()

    wait_for(lambda: ct.getStatus().AcquisitionStatus != core.AcqRunning, 100)
    assert process_count == 1


def test_custom_frame_exception():
    """
    Setup a simulated camera which raise an exception at the second frame.

    Expect it to stop the acquisition.
    """

    process_count = 0

    class MyCamera(simulator.Camera):
        def fillData(self, data):
            nonlocal process_count

            process_count += 1
            if process_count > 1:
                raise RuntimeError("Oups")

    cam = MyCamera()
    hw = simulator.Interface(cam)
    ct = core.CtControl(hw)

    acq = ct.acquisition()
    acq.setTriggerMode(core.IntTrigMult)
    acq.setAcqNbFrames(3)
    acq.setAcqExpoTime(0.01)

    ct.prepareAcq()
    imageStatus = ct.getImageStatus()
    assert imageStatus.LastImageReady == -1, imageStatus

    def wait_for_next_frame_ready():
        def check_next_frame_ready():
            status = hw.getStatus()
            ready = status.det == core.DetIdle or status.det & core.DetWaitForTrigger
            return bool(ready)
        wait_for(check_next_frame_ready, 100)

    # The first frame is properly acquired
    ct.startAcq()
    wait_for_next_frame_ready()
    imageStatus = ct.getImageStatus()
    assert imageStatus.LastImageReady == 0, imageStatus

    # The second frame trigges an internal error
    ct.startAcq()
    wait_for(lambda: ct.getStatus().AcquisitionStatus == core.AcqFault, 100)
    imageStatus = ct.getImageStatus()
    assert imageStatus.LastImageReady == 0, imageStatus


def test_gauss_fill():
    """
    Test that the gauss fill increase frame after frame
    """
    processed_frames = []

    class MyCamera(simulator.Camera):
        def fillData(self, data):
            nonlocal processed_frames
            s = numpy.sum(data.buffer)
            processed_frames.append(s)

    cam = MyCamera()
    hw = simulator.Interface(cam)
    ct = core.CtControl(hw)

    acq = ct.acquisition()
    acq.setTriggerMode(core.IntTrig)
    acq.setAcqNbFrames(3)
    acq.setAcqExpoTime(0.01)

    ct.prepareAcq()
    ct.startAcq()

    wait_for(lambda: ct.getStatus().AcquisitionStatus != core.AcqRunning, 100)
    assert processed_frames == [1096524, 2225892, 3356544]


def test_empty_fill():
    """
    Test that the empty fill provides empty frames
    """
    processed_frames = []

    class MyCamera(simulator.Camera):
        def fillData(self, data):
            nonlocal processed_frames
            s = numpy.sum(data.buffer)
            processed_frames.append(s)

    cam = MyCamera()
    cam.getFrameGetter().setFillType(simulator.FrameBuilder.Empty)
    hw = simulator.Interface(cam)
    ct = core.CtControl(hw)

    acq = ct.acquisition()
    acq.setTriggerMode(core.IntTrig)
    acq.setAcqNbFrames(3)
    acq.setAcqExpoTime(0.01)

    ct.prepareAcq()
    ct.startAcq()

    wait_for(lambda: ct.getStatus().AcquisitionStatus != core.AcqRunning, 100)
    assert processed_frames == [0, 0, 0]
