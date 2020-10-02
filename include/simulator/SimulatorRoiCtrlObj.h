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

#pragma once

#if !defined(SIMULATOR_ROICTRLOBJ_H)
#define SIMULATOR_ROICTRLOBJ_H

#include <lima/HwInterface.h>

#include <simulator_export.h>

namespace lima {

// Forward definitions
class HwInterface;

namespace Simulator {

class Camera;

/// Control object providing simulator roi interface
class SIMULATOR_EXPORT RoiCtrlObj : public HwRoiCtrlObj {
public:
  RoiCtrlObj(Camera &simu) : m_simu(simu) {}

  virtual void setRoi(const Roi &roi);
  virtual void getRoi(Roi &roi);
  virtual void checkRoi(const Roi &set_roi, Roi &hw_roi);

private:
  Camera &m_simu;
};

} // namespace Simulator

} // namespace lima

#endif // !defined(SIMULATOR_ROICTRLOBJ_H)
