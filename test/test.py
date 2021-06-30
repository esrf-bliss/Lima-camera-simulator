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

import time
from Lima import Core, Simulator


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

    while ct.getStatus().AcquisitionStatus != Core.AcqReady:
        time.sleep(0.1)

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
    cam.extTrigAcq()  # simulate an external trigger

    while ct.getStatus().AcquisitionStatus != Core.AcqReady:
        time.sleep(0.1)

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
    for _ in range(3):
        cam.extTrigAcq()  # simulate an external trigger
        time.sleep(0.1)

    while ct.getStatus().AcquisitionStatus != Core.AcqReady:
        time.sleep(0.1)

    assert acq_status.last_image_ready == 2


def test_detector_size():
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
