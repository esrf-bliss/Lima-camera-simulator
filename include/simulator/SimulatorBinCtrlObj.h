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

#if !defined(SIMULATOR_BINCTRLOBJ_H)
#define SIMULATOR_BINCTRLOBJ_H

#include <lima/HwInterface.h>

#include <simulator_export.h>

namespace lima {

// Forward definitions
class HwInterface;

namespace Simulator {

class Camera;

/// Control object providing simulator binning interface
class SIMULATOR_EXPORT BinCtrlObj : public HwBinCtrlObj {
public:
  BinCtrlObj(Camera &simu) : m_simu(simu) {}

  virtual void setBin(const Bin &bin);
  virtual void getBin(Bin &bin);
  virtual void checkBin(Bin &bin);

private:
  Camera &m_simu;
};

} // namespace Simulator

} // namespace lima

#endif // !defined(SIMULATOR_BINCTRLOBJ_H)
