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

#include <cctype> //For std::isspace

#include <algorithm>
#include <iostream>
#include <fstream>
#include <map>
#include <memory>

#include "lima/Debug.h"
#include "lima/Exceptions.h"
#include "lima/SizeUtils.h"

using namespace lima;


// Note: Use Boost string algo rather than this
/// Trim both sides of a string using std::isspace
static std::string& trim(std::string&& s)
{
	s.erase(s.begin(), std::find_if_not(s.begin(), s.end(), [](char c) { return std::isspace(c); }));
	s.erase(std::find_if_not(s.rbegin(), s.rend(), [](char c) { return std::isspace(c); }).base(), s.end());
	return s;
}

// Parse EDf header and add the result to headers map
static void parseEDFHeader(std::istream& input_file, std::map<std::string, std::string>& headers)
{
	// Assume the header to be a multiple of 512 bytes
	std::string buffer(0x200, '\0');

	input_file.read(&buffer[0], buffer.size());
	if (buffer[0] != '{') throw LIMA_EXC(CameraPlugin, Error, "Invalid EDF file");

	std::stringstream ss;
	ss << buffer;

	// More buffer in header?
	size_t header_end_pos;
	while (((header_end_pos = buffer.rfind('}')) == std::string::npos) && !input_file.eof()) {
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

static ImageType getImageType(const std::string& type)
{
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

int main(int argc, char* argv[])
{
	if (argc != 2)
	{
		std::cout << "test_edf_parser <filename>";
		return 0;
	}

	try {
		// Open the file and parse the header
		std::ifstream input_file(argv[1], std::ios::binary);

		std::map<std::string, std::string> headers;
		parseEDFHeader(input_file, headers);

		// Interpret header
		Point p;
		p.x = std::stoi(headers["Dim_1"]); // C++11
		p.y = std::stoi(headers["Dim_2"]);
		Size size = p;

		ImageType image_type;
		auto val = headers.find("DataType");
		if (val != headers.end())
			image_type = getImageType(val->second);
		else
			throw LIMA_EXC(CameraPlugin, Error, "Missing DataType header in EDF file");

		FrameDim frame_dim = FrameDim(size, image_type);
		const int mem_size = frame_dim.getMemSize();

		auto ptr = std::make_unique<char[]>(mem_size);

		// Read the frame data
		input_file.read(ptr.get(), mem_size);
		if (input_file.fail())
		{
			std::cerr << "Read " << input_file.gcount() << ", " << mem_size << " expected";
			throw LIMA_EXC(CameraPlugin, Error, "Failed to read data section of EDF file");
		}
	}
	catch (Exception& e) {
		std::cerr << "LIMA Exception:" << e.getErrMsg() << std::endl;
	}

	return 0;
}
