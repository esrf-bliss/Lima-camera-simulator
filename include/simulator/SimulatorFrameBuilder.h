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

#if !defined(SIMULATOR_FRAMEBUILDER_H)
#define SIMULATOR_FRAMEBUILDER_H

#include <vector>

#include <lima/SizeUtils.h>
#include <lima/Exceptions.h>

#include <simulator_export.h>

#include "simulator/SimulatorFrameGetter.h"

namespace lima {

namespace Simulator {

struct SIMULATOR_EXPORT GaussPeak {
  double x0, y0; //<! The center of the peak
  double fwhm;   //<! Full Width at Half Maximum
  double max;    //<! The maximum value

  GaussPeak() : x0(0), y0(0), fwhm(0), max(0) {}
  GaussPeak(const GaussPeak &o) : x0(o.x0), y0(o.y0), fwhm(o.fwhm), max(o.max) {}
  GaussPeak(double x, double y, double w, double m) : x0(x), y0(y), fwhm(w), max(m) {}
};

/// This class configures and generates frames for the Simulator
class SIMULATOR_EXPORT FrameBuilder : public FrameGetter {

  DEB_CLASS_NAMESPC(DebModCamera, "FrameBuilder", "Simulator");

public:
  static const bool is_thread_safe = true;

  enum FillType {
    Gauss,
    Diffraction,
    Empty,
  };
  enum RotationAxis {
    Static,
    RotationX,
    RotationY,
  };

  typedef std::vector<struct GaussPeak> PeakList;

  FrameBuilder();
  FrameBuilder(FrameDim &frame_dim, Bin &bin, Roi &roi, const PeakList &peaks, double grow_factor);
  ~FrameBuilder();

  Camera::Mode getMode() const { return Camera::MODE_GENERATOR; }

  void getFrameDim(FrameDim &dim) const;
  void setFrameDim(const FrameDim &dim);

  void getEffectiveFrameDim(FrameDim &dim) const;

  void getBin(Bin &bin) const;
  void setBin(const Bin &bin);
  void checkBin(Bin &bin) const;

  void getRoi(Roi &roi) const;
  void setRoi(const Roi &roi);
  void checkRoi(Roi &roi) const;

  void getPeaks(PeakList &peaks) const;
  void setPeaks(const PeakList &peaks);

  void getPeakAngles(std::vector<double> &angles) const;
  void setPeakAngles(const std::vector<double> &angles);

  void getFillType(FillType &fill_type) const;
  void setFillType(FillType fill_type);

  void getRotationAxis(RotationAxis &rot_axis) const;
  void setRotationAxis(RotationAxis rot_axis);

  void getRotationAngle(double &a) const;
  void setRotationAngle(const double &a);

  void getRotationSpeed(double &s) const;
  void setRotationSpeed(const double &s);

  void getGrowFactor(double &grow_factor) const;
  void setGrowFactor(const double &grow_factor);

  void getDiffractionPos(double &x, double &y) const;
  void setDiffractionPos(const double &x, const double &y);

  void getDiffractionSpeed(double &sx, double &sy) const;
  void setDiffractionSpeed(const double &sx, const double &sy);

  bool getFrame(unsigned long frame_nr, unsigned char *ptr) override;
  void prepareAcq() {}

  /// Gets the maximum "hardware" image size
  void getMaxImageSize(Size &max_size) const
  { max_size = m_frame_dim.getSize(); }

private:
  FrameDim m_frame_dim; //<! Generated frame dimensions
  Bin m_bin;            //<! "Hardware" Bin
  Roi m_roi;            //<! "Hardware" RoI
  PeakList m_peaks;     //<! Peaks to put in each frame
  double m_grow_factor; //<! Peaks grow % with each frame
  FillType m_fill_type;
  RotationAxis m_rot_axis;
  double m_rot_angle;
  double m_rot_speed;
  std::vector<double> m_peak_angles;

  double m_diffract_x;
  double m_diffract_y;
  double m_diffract_sx;
  double m_diffract_sy;

  void init(FrameDim &frame_dim, Bin &bin, Roi &roi, const PeakList &peaks, double grow_factor);

  void checkValid(const FrameDim &frame_dim, const Bin &bin, const Roi &roi);
  void checkPeaks(PeakList const &peaks);
  double dataXY(unsigned long frame_nr, const PeakList &peaks, int x, int y) const;
  double dataDiffract(double x, double y) const;
  template <class depth>
  void fillData(unsigned long frame_nr, unsigned char *ptr) const;

  PeakList getGaussPeaksFrom3d(double angle) const;
  static double gauss2D(double x, double y, double x0, double y0, double fwhm, double max);
};

} // namespace Simulator

} // namespace lima

#endif // !defined(SIMULATOR_FRAMEBUILDER_H)
