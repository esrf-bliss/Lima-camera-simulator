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

#if !defined(SIMULATOR_FRAMELOADER_H)
#define SIMULATOR_FRAMELOADER_H

#include <string>
#include <fstream>
#include <memory>

#include <lima/Debug.h>
#include <lima/HwInterface.h>

#include <simulator_export.h>

#include <simulator/SimulatorFrameGetter.h>

namespace lima {

namespace Simulator {

class SIMULATOR_EXPORT FrameLoader : public FrameGetter {
  DEB_CLASS_NAMESPC(DebModCamera, "FrameLoader", "Simulator");

public:
  static const bool is_thread_safe = false;

  FrameLoader() : m_current_stream(std::make_shared<std::ifstream>()) {}
  
  Camera::Mode getMode() const { return Camera::MODE_LOADER; }

  void setFilePattern(const std::string &file_pattern);
  void getFilePattern(std::string &file_pattern) const { file_pattern = m_file_pattern; }

  bool getNextFrame(unsigned long frame_nr, unsigned char *ptr) override;
  void prepareAcq();

  void setFrameDim(const FrameDim &frame_dim)
  {
    LIMA_EXC(CameraPlugin, Error, "setFrameDim not supported with FrameLoader");
  }
  void getFrameDim(FrameDim &frame_dim) const { frame_dim = m_frame_dim; }

  void getEffectiveFrameDim(FrameDim &frame_dim) const { frame_dim = m_frame_dim; }

  void getMaxImageSize(Size &max_image_size) const { max_image_size = m_frame_dim.getSize(); }

private:
  typedef std::vector<std::string> files_t;
    
  std::string m_file_pattern;                //<! The file pattern used to load the frames
  files_t m_files;                           //<! The filenames that matches the pattern above
  files_t::const_iterator m_it_current_file; //<! An iterator to the filename that is currently read

  std::shared_ptr<std::ifstream> m_current_stream; //<! The current stream

  FrameDim m_frame_dim;
};

} // namespace Simulator

} // namespace lima

#endif // !defined(SIMULATOR_FRAMELOADER_H)
