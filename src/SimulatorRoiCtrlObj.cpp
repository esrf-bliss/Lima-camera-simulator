//###########################################################################
// This file is part of LImA, a Library for Image Acquisition
//
// Copyright (C) : 2009-2011
// European Synchrotron Radiation Facility
// BP 220, Grenoble 38043
// FRANCE
//
// This is free software; you can redistribute it and/or modify
// it under the terms of the GNU General Public License as published by
// the Free Software Foundation; either version 3 of the License, or
// (at your option) any later version.
//
// This software is distributed in the hope that it will be useful,
// but WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
// GNU General Public License for more details.
//
// You should have received a copy of the GNU General Public License
// along with this program; if not, see <http://www.gnu.org/licenses/>.
//###########################################################################

#include "simulator/SimulatorRoiCtrlObj.h"
#include "simulator/SimulatorCamera.h"
#include "simulator/SimulatorFrameBuilder.h"

using namespace lima;
using namespace lima::Simulator;
using namespace std;

void RoiCtrlObj::setRoi(const Roi &roi)
{
  FrameBuilder *builder = m_simu.getFrameBuilder();
  if (builder) builder->setRoi(roi);
}

void RoiCtrlObj::getRoi(Roi &roi)
{
  FrameBuilder *builder = m_simu.getFrameBuilder();
  if (builder) builder->getRoi(roi);
}

void RoiCtrlObj::checkRoi(const Roi &set_roi, Roi &hw_roi)
{
  FrameBuilder *builder = m_simu.getFrameBuilder();
  hw_roi = set_roi;
  if (builder)
    builder->checkRoi(hw_roi);
  else {
    Size max_size;
    m_simu.getMaxImageSize(max_size);
    hw_roi = Roi({0, 0}, max_size);
  }
}
