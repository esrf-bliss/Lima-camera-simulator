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

#if !defined(SIMULATOR_FRAMEPREFETCHER_H)
#define SIMULATOR_FRAMEPREFETCHER_H

#include <cassert>
#include <cstring>

#include <memory>
#include <sstream>
#include <vector>

#include <lima/SizeUtils.h>
#include <lima/Exceptions.h>

#include <simulator_export.h>

#include <simulator/SimulatorFrameGetter.h>

namespace lima {

namespace Simulator {

/// A FrameGetter adapter that prefetches a given number of frames in memory from an underlying FrameGetter
/// implementation
template <class FrameGetterImpl>
class FramePrefetcher : public FrameGetterImpl {
  DEB_CLASS_NAMESPC(DebModCamera, "FramePrefetcher", "Simulator");

  typedef std::unique_ptr<unsigned char[]> buffer_t;

public:
  FramePrefetcher() : m_frame_nr(0) {}

  FramePrefetcher(const FramePrefetcher &) = delete;
  FramePrefetcher & operator=(const FramePrefetcher &) = delete;

  Camera::Mode getMode() const { return static_cast<Camera::Mode>(FrameGetterImpl::getMode() + 1); }

  void getNbPrefetchedFrames(unsigned int &nb_prefetched_frames) const
  {
    nb_prefetched_frames = (unsigned int)m_prefetched_frame_buffers.size();
  }

  void setNbPrefetchedFrames(unsigned int nb_prefetched_frames)
  {
    m_prefetched_frame_buffers.resize(nb_prefetched_frames);
  }

  void prepareAcq()
  {
    DEB_MEMBER_FUNCT();

    // Call implementation preparation
    FrameGetterImpl::prepareAcq();

    // If we use prefetched frame
    if (!m_prefetched_frame_buffers.empty()) {
      FrameDim frame_dim;

      // Get the frame dimension
      FrameGetterImpl::getEffectiveFrameDim(frame_dim);

      // Allocate the buffers for the prebuilt frames
      m_mem_size = frame_dim.getMemSize();
      for (buffer_t& frame_buffer : m_prefetched_frame_buffers) {
        //In C++14, use std::make_unique<unsigned char[]>(m_mem_size);
        frame_buffer = std::unique_ptr<unsigned char[]>(new unsigned char[m_mem_size]);

        if (!frame_buffer) {
          std::ostringstream msg;
          msg << "Attempting to allocate Simulator buffers for prefetched frames failed:" << DEB_VAR1(m_mem_size);
          throw LIMA_EXC(CameraPlugin, Error, msg.str());
        }
      }

      if (FrameGetterImpl::is_thread_safe) {
// Parallel for loop
#pragma omp parallel for
        for (int i = 0; i < m_prefetched_frame_buffers.size(); i++)
          FrameGetterImpl::getNextFrame(m_prefetched_frame_buffers[i].get());
      } else
        // Serial for loop
        for (size_t i = 0; i < m_prefetched_frame_buffers.size(); i++)
          FrameGetterImpl::getNextFrame(m_prefetched_frame_buffers[i].get());
    }
  }

  bool getNextFrame(unsigned char *ptr)
  {
    DEB_MEMBER_FUNCT();

    unsigned long idx = m_frame_nr % m_prefetched_frame_buffers.size();
    assert(idx < m_prefetched_frame_buffers.size());

    unsigned char *src = m_prefetched_frame_buffers[idx].get();
    std::memcpy(ptr, src, m_mem_size);

    ++m_frame_nr;
    return true;
  }

  unsigned long getFrameNr() const { return m_frame_nr; }
  void resetFrameNr(unsigned long frame_nr = 0) { m_frame_nr = frame_nr; };

private:
  unsigned long m_frame_nr;                           //<! The current frame number
  std::vector<buffer_t> m_prefetched_frame_buffers;   //<! A vector of frame buffers
  int m_mem_size;                                     //<! The size of a mem buffer
};

} // namespace Simulator

} // namespace lima

#endif // !defined(SIMULATOR_FRAMEPREFETCHER_H)
