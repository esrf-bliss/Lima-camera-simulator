from Lima import Core, Simulator

cam = Simulator.Camera()
hw = Simulator.Interface(cam)
ct = Core.CtControl(hw)

ct.prepareAcq()
ct.startAcq()

while ct.getStatus().AcquisitionStatus != Core.AcqReady:
    sleep(0.1)
