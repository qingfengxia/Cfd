#!/bin/bash

echo "start test script in the current working dir of $(pwd)"

#cache the output file for debug purpose

if [ $TRAVIS_OS_NAME = 'linux' ]; then
    case "${TOXENV}" in
        FC_DAILY)
            # test should be done in daily build of FreeCAD
            if  [ -d 'Cfd/TestCfd.py' ] ; then 
                freecadcmd-daily Cfd/TestCfd.py > $HOME/.cache/Cfd/freecadcmd_output.log
            fi
            echo "start test script in the current working dir of $(pwd)"
            #freecad-daily Cfd/test_files/test_cfd_gui.py
            ;;
        FC_STABLE)
            # test should be done in stable build of FreeCAD
            if  [ -d 'Cfd/TestCfd.py' ] ; then 
                freecadcmd Cfd/TestCfd.py > $HOME/.cache/Cfd/freecadcmd_output.log
            fi
            echo "start test script in the current working dir of $(pwd)"
            #freecad Cfd/test_files/test_cfd_gui.py
            ;;
    esac
else
    # Install some custom requirements on Linux
    exit 0
fi