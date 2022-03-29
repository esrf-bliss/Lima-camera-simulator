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

#include <unistd.h>

#include <cassert>
#include <cmath>
#include <cstring>
#include <cctype>

#include <algorithm>
#include <string>
#include <fstream>
#include <iterator>
#include <utility>
#include <map>

#if defined(_WIN32)
#include <windows.h>
#include <shlwapi.h>
#pragma comment(lib, "shlwapi.lib") // This tells msvc to link with shlwapi.lib
#else
#include <glob.h>
#endif // (_WIN32)

//#include <processlib/Data.h>

#include "lima/Exceptions.h"
#include "lima/SizeUtils.h"

#include "simulator/SimulatorFrameLoader.h"

using namespace lima;
using namespace lima::Simulator;

DEB_GLOBAL(DebModCamera);

// Note: Use Boost string algo rather than this
/// Trim both sides of a string using std::isspace
static std::string &trim(std::string &&s)
{
  s.erase(s.begin(), std::find_if_not(s.begin(), s.end(), [](char c) { return std::isspace(c); }));
  s.erase(std::find_if_not(s.rbegin(), s.rend(), [](char c) { return std::isspace(c); }).base(), s.end());
  return s;
}

// Parse EDf header and add the result to headers map
// Parse EDF header and add the result to headers map
static void parseEDFHeader(std::istream& input_file, std::map<std::string, std::string>& headers)
{
  DEB_GLOBAL_FUNCT();

  // Assume the header to be a multiple of 512 bytes
  std::string buffer(512, '\0');

  input_file.read(&buffer[0], buffer.size());
  if (buffer[0] != '{')
    throw LIMA_EXC(CameraPlugin, Error, "Invalid EDF file");

  std::stringstream ss;
  ss << buffer;

  // More buffer in header?
  while ((buffer.rfind('}') == std::string::npos) && !input_file.eof()) {
    input_file.read(&buffer[0], buffer.size());
    ss << buffer;
  }

  // Parse header
  while (!ss.eof()) {
    std::string line;
    std::getline(ss, line);

    // Get rid of any comment
    std::string::size_type comment = line.rfind(';');
    if (comment != std::string::npos)
      line.resize(comment);

    // Tokenize
    std::string::size_type token_pos = line.find('=');
    if (token_pos != std::string::npos)
      headers.insert(std::make_pair(trim(line.substr(0, token_pos)), trim(line.substr(token_pos + 1))));
  }
}

static ImageType getImageType(const std::string &type)
{
  DEB_GLOBAL_FUNCT();
  
  ImageType res;

  if (type == "UnsignedByte")
    res = ImageType::Bpp8;
  else if (type == "SignedByte")
    res = ImageType::Bpp8S;
  else if (type == "UnsignedShort")
    res = ImageType::Bpp16;
  else if (type == "SignedShort")
    res = ImageType::Bpp16S;
  else if (type == "UnsignedInteger")
    res = ImageType::Bpp32;
  else if (type == "SignedInteger")
    res = ImageType::Bpp32S;
  // else if (type == "Unsigned64")
  //	res = ImageType::Bpp32;
  // else if (type == "Signed64")
  //	res = ImageType::Bpp32;
  else if (type == "FloatValue")
    res = ImageType::Bpp32F;
  // else if (type == "DoubleValue")
  //	res = ImageType::Bpp32;
  else
    throw LIMA_EXC(CameraPlugin, Error, "Unsupported pixel type in EDF file format");

  return res;
}

static void findFiles(const std::string &path_pattern, std::vector<std::string> &files)
{
  DEB_GLOBAL_FUNCT();
  
  if (path_pattern.empty()) return;

#if defined(_WIN32)
  // Extract the folder part
  std::string folder = path_pattern;
  folder.push_back('\0');
  PathRemoveFileSpec(&folder[0]);

  WIN32_FIND_DATA FindFileData;
  HANDLE hFind = FindFirstFile(path_pattern.c_str(), &FindFileData);
  if (hFind == INVALID_HANDLE_VALUE) {
    printf("FindFirstFile failed (%d)\n", GetLastError());
    return;
  } else {
    std::string path(MAX_PATH, '\0');
    PathCombine(&path[0], folder.c_str(), FindFileData.cFileName);
    files.push_back(path);

    while (FindNextFile(hFind, &FindFileData)) {
      PathCombine(&path[0], folder.c_str(), FindFileData.cFileName);
      files.push_back(path);
    }

    FindClose(hFind);
  }
#else
  glob_t glob_result;
  glob(path_pattern.c_str(), GLOB_TILDE, NULL, &glob_result);

  for (unsigned int i = 0; i < glob_result.gl_pathc; ++i)
    files.push_back(std::string(glob_result.gl_pathv[i]));

  globfree(&glob_result);
#endif // _WIN32
}

void FrameLoader::setFilePattern(const std::string &file_pattern)
{
  DEB_MEMBER_FUNCT();

  if (m_file_pattern != file_pattern)
    m_file_pattern = file_pattern;

  // Clear the file list
  m_files.clear();

  // Find the files using the new pattern
  findFiles(file_pattern, m_files);

  if (!m_files.empty()) {
    // Get the first file
    const std::string &file = m_files.front();

    // Get the file path and extension
#if defined(_WIN32)
    // std::string path(MAX_PATH, '\0');
    // PathCombine(&path[0], m_folder.c_str(), file.c_str());
    const std::string extension(PathFindExtension(file.c_str()));
#else
    // std::string path = folder + "/" + file;
    const size_t pos            = file.rfind('.');
    const std::string extension = pos == 0 ? std::string() : file.substr(pos);
#endif // _WIN32

    Size size;
    ImageType image_type;

    if (extension == ".edf") {
      // Open the file and parse the header
      std::ifstream input_file(file.c_str(), std::ios::binary);
      if (!input_file.is_open()) throw LIMA_EXC(CameraPlugin, Error, "Failed to open EDF file");

      std::map<std::string, std::string> headers;
      parseEDFHeader(input_file, headers);

      Point p;
      p.x  = std::stoi(headers["Dim_1"]); // C++11
      p.y  = std::stoi(headers["Dim_2"]);
      size = p;

      // Interpret header
      auto val = headers.find("DataType");
      if (val != headers.end())
        image_type = getImageType(val->second);
      else
        throw LIMA_EXC(CameraPlugin, Error, "Missing DataType header in EDF file");
    }

    m_frame_dim = FrameDim(size, image_type);

    DEB_TRACE() << DEB_VAR1(m_frame_dim);

    // Signal LiMA core that the frame properties may have changed
    maxImageSizeChanged(size, image_type);
  } else
    throw LIMA_EXC(CameraPlugin, Error, "No file found with the given pattern");
}

void FrameLoader::prepareAcq()
{
  DEB_MEMBER_FUNCT();

  if (!m_files.empty()) {
    if (m_current_stream->is_open())
      // Close the current file
      m_current_stream->close();
    
    // Position the iterator
    m_it_current_file = m_files.begin();

    // Open the file
    m_current_stream->open(m_it_current_file->c_str(), std::ios::binary);
    DEB_TRACE() << "Open file " << *m_it_current_file;
    if (!m_current_stream->is_open())
      throw LIMA_EXC(CameraPlugin, Error, "Failed to open file");
  }
}

bool FrameLoader::getFrame(unsigned long frame_nr, unsigned char *ptr)
{
  DEB_MEMBER_FUNCT();

  if (m_it_current_file != m_files.end()) {
    Size size;
    ImageType image_type;

    const std::string &file = *m_it_current_file;

    FrameDim frame_dim;

    // Get the file extension
#if defined(_WIN32)
    // std::string path(MAX_PATH, '\0');
    // PathCombine(&path[0], m_folder.c_str(), file.c_str());
    const std::string extension(PathFindExtension(file.c_str()));
#else
    // std::string path = m_folder + "/" + file;
    const size_t pos            = file.rfind('.');
    const std::string extension = pos == 0 ? std::string() : file.substr(pos);
#endif // _WIN32

    if (extension == ".edf") {
      if (m_current_stream->peek() == EOF) {
        DEB_TRACE() << "EOF " << *m_it_current_file << " skip to next file";
        
        m_current_stream->close();

        // Skip to next file
        m_it_current_file++;

        if (m_it_current_file != m_files.end())
        {
          // Open next file
          m_current_stream->open(m_it_current_file->c_str(), std::ios::binary);
          DEB_TRACE() << "Open file " << *m_it_current_file;
          if (!m_current_stream->is_open())
            throw LIMA_EXC(CameraPlugin, Error, "Failed to open file");
        }
        else
          throw LIMA_EXC(CameraPlugin, Error, "End of file list");
      }

      // Check if the file is still open
      if (!m_current_stream->is_open())
        throw LIMA_EXC(CameraPlugin, Error, "Failed to open EDF file");

      // Parse the header
      std::map<std::string, std::string> headers;
      parseEDFHeader(*m_current_stream, headers);

      Point p;
      p.x  = std::stoi(headers["Dim_1"]); // C++11
      p.y  = std::stoi(headers["Dim_2"]);
      size = p;

      // Interpret header
      auto val = headers.find("DataType");
      if (val != headers.end())
        image_type = getImageType(val->second);

      frame_dim          = FrameDim(size, image_type);
      const int mem_size = frame_dim.getMemSize();

      DEB_TRACE() << DEB_VAR2(frame_dim, mem_size);

      assert(frame_dim.getMemSize() == std::stol(headers["Size"]));
      
      if (m_frame_dim != frame_dim)
        throw LIMA_EXC(CameraPlugin, Error, "Frame dimensions do not match");

      // Read the frame data
      m_current_stream->read(reinterpret_cast<char *>(ptr), mem_size);
      if (m_current_stream->fail())
        throw LIMA_EXC(CameraPlugin, Error, "Failed to read data section of EDF file");
      
      std::stringstream os;
      unsigned short* data = (unsigned short*) ptr;
      os << std::hex << data[0] << ' ' << data[1] << ' '<< data[2] << ' '<< data[3];
      DEB_TRACE() << "data: " << os.str();
    } else
      throw LIMA_EXC(CameraPlugin, Error, "Unsupported file format");

  } else
    return false;

  return true;
}
