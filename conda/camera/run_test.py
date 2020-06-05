import time
from Lima import Core, Simulator

#Core.DebParams.setTypeFlags(Core.DebParams.AllFlags)

cam = Simulator.Camera()
hw = Simulator.Interface(cam)
ct = Core.CtControl(hw)

ct.prepareAcq()
ct.startAcq()

while ct.getStatus().AcquisitionStatus != Core.AcqReady:
    time.sleep(0.1)
