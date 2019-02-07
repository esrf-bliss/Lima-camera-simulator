import time
from Lima import Core, Simulator

cam = Simulator.Camera()
hw = Simulator.Interface(cam)
ct = Core.CtControl(hw)

ct.prepareAcq()
ct.startAcq()

time.sleep(1)
