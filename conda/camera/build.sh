#!/bin/bash
cmake -Bbuild -H. -GNinja -DCMAKE_BUILD_TYPE=RelWithDebInfo -DCMAKE_INSTALL_PREFIX=$PREFIX -DPYTHON_SITE_PACKAGES_DIR=$SP_DIR -DCMAKE_FIND_ROOT_PATH=$PREFIX -DLIMA_ENABLE_PYTHON=1 -DLIMA_ENABLE_CAMERA_TESTS=1
cmake --build build --target install
