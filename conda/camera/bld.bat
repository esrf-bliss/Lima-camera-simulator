cmake -Bbuild -H. -GNinja -DCMAKE_BUILD_TYPE=RelWithDebInfo -DCMAKE_INSTALL_PREFIX=%LIBRARY_PREFIX% -DPYTHON_SITE_PACKAGES_DIR=%SP_DIR% -DCMAKE_FIND_ROOT_PATH=%LIBRARY_PREFIX% -DLIMA_ENABLE_PYTHON=1 -DCAMERA_ENABLE_TESTS=1
IF %ERRORLEVEL% NEQ 0 exit /b %ERRORLEVEL%

cmake --build build --target install
IF %ERRORLEVEL% NEQ 0 exit /b %ERRORLEVEL%
