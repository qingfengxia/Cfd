#!/bin/bash

# clone this repo has been done by Travis, and cd to <user_name>/<repo_name>
#- git clone https://github.com/qingfengxia/Cfd.git
# this $(pwd) does not work!
echo "current working dir is $(pwd), current user is $(id)"

if [ $TRAVIS_OS_NAME = 'linux' ]; then

    # Install some custom requirements on macOS
    # e.g. brew install pyenv-virtualenv

    case "${TOXENV}" in
        FC_DAILY)
            #
            sudo add-apt-repository -y ppa:freecad-maintainers/freecad-daily
            sudo apt-get -q update
            sudo apt-get -y install freecad-daily
            #
            sudo apt-get update -q
            sudo apt-get install  -y python3-matplotlib python3-numpy git openfoam
            sudo pip3 install PyFoam

            # install to user home (/home/travis/), simulate the addon manager
            cd .. &&  mkdir -p ~/.FreeCAD/Mod 
            if [ ! -e "~/.FreeCAD/Mod/Cfd" ]; then ln -s Cfd ~/.FreeCAD/Mod/Cfd; fi
            ;;
        FC_STABLE)
            sudo add-apt-repository -y ppa:freecad-maintainers/freecad-stable
            sudo apt-get -q update
            sudo apt-get -y install freecad
            # OpenFOAM version may be too low for this test
            sudo apt-get update -q
            sudo apt-get install  -y python3-matplotlib python3-numpy git openfoam
            sudo pip3 install PyFoam

            # install to user home (/home/travis/), simulate the addon manager
            cd .. &&  mkdir -p ~/.FreeCAD/Mod 
            if [ ! -e "~/.FreeCAD/Mod/Cfd" ]; then ln -s Cfd ~/.FreeCAD/Mod/Cfd; fi
            ;;
    esac
else
    # Install some custom requirements on Linux
    exit 0
fi
