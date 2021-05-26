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

#include "simulator/SimulatorInterface.h"
#include "simulator/SimulatorFrameGetter.h"
#include "simulator/SimulatorFrameLoader.h"
#include "simulator/SimulatorFrameBuilder.h"
#include "simulator/SimulatorFramePrefetcher.h"
#include "lima/CtTestApp.h"

DEB_GLOBAL(DebModTest);

using namespace lima;
using namespace lima::Simulator;

auto MODE_GENERATOR = Camera::MODE_GENERATOR;
auto MODE_GENERATOR_PREFETCH = Camera::MODE_GENERATOR_PREFETCH;
auto MODE_LOADER = Camera::MODE_LOADER;
auto MODE_LOADER_PREFETCH = Camera::MODE_LOADER_PREFETCH;

class TestApp : public CtTestApp
{
	DEB_CLASS_NAMESPC(DebModTest, "TestApp", "Simulator");

 public:
	class Pars : public CtTestApp::Pars
	{
		DEB_CLASS_NAMESPC(DebModTest, "TestApp::Pars", "Simulator");
	public:
		Camera::Mode cam_mode{MODE_GENERATOR};
		int cam_nb_prefetched_frames{10};
		std::string cam_file_pattern{"./data/test_*.edf"};
		FrameDim cam_frame_dim;
		Pars();
	};

	TestApp(int argc, char *argv[]) : CtTestApp(argc, argv) {}

 protected:
	virtual CtTestApp::Pars *getPars();
	virtual CtControl *getCtControl();
	virtual index_map getIndexMap() { return {}; }
	virtual void configureAcq(const index_map& indexes);

	AutoPtr<Pars> m_pars;
	AutoPtr<Camera> m_cam;
	AutoPtr<HwInterface> m_interface;
	AutoPtr<CtControl> m_ct;
};

TestApp::Pars::Pars()
{
	DEB_CONSTRUCTOR();

#define AddOpt(var, opt, par)				\
	m_opt_list.insert(MakeOpt(var, "", opt, par))

	AddOpt(cam_mode, "--cam-mode", "camera mode");

	AddOpt(cam_nb_prefetched_frames, "--cam-nb-prefetched-frames",
	       "nb prefetched frames");

	AddOpt(cam_file_pattern, "--cam-file-pattern", "image file pattern");

	AddOpt(cam_frame_dim, "--cam-frame-dim", "generated frame dim");
}

CtTestApp::Pars *TestApp::getPars()
{
	m_pars = new Pars();
	return m_pars;
}

CtControl *TestApp::getCtControl()
{
	DEB_MEMBER_FUNCT();

	m_cam = new Camera();

	DEB_ALWAYS() << "Camera: " << DEB_VAR1(m_pars->cam_mode);
	m_cam->setMode(m_pars->cam_mode);
	if ((m_pars->cam_mode == MODE_GENERATOR_PREFETCH) ||
	    (m_pars->cam_mode == MODE_LOADER_PREFETCH)) {
		DEB_ALWAYS() << DEB_VAR1(m_pars->cam_nb_prefetched_frames);
		FramePrefetcher<FrameBuilder> *fbp= m_cam->getFrameBuilderPrefetched();
		fbp->setNbPrefetchedFrames(m_pars->cam_nb_prefetched_frames);
	}
	if ((m_pars->cam_mode == MODE_LOADER) ||
	    (m_pars->cam_mode == MODE_LOADER_PREFETCH)) {
		DEB_ALWAYS() << DEB_VAR1(m_pars->cam_file_pattern);
		FrameLoader *fl= m_cam->getFrameLoader();
		fl->setFilePattern(m_pars->cam_file_pattern);
	}

	if (m_pars->cam_frame_dim.isValid())
		m_cam->setFrameDim(m_pars->cam_frame_dim);

	m_interface = new Interface(*m_cam);
	m_ct = new CtControl(m_interface);
	return m_ct;
}

void TestApp::configureAcq(const index_map& indexes)
{
	DEB_MEMBER_FUNCT();

	FrameDim effective_dim;
	FrameGetter *fg = m_cam->getFrameGetter();
	fg->getEffectiveFrameDim(effective_dim);
	DEB_ALWAYS() << DEB_VAR1(effective_dim);
}


int main(int argc, char *argv[])
{
	DEB_GLOBAL_FUNCT();
        try {
		TestApp app(argc, argv);
		app.run();
        } catch (Exception& e) {
	        DEB_ERROR() << "LIMA Exception:" << e.getErrMsg();
        }
	return 0;
}

