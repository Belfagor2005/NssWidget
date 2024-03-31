#!/bin/sh
pyv="$(python -V 2>&1)"
echo "$pyv"
echo "Checking Dependencies"
echo
# [[ "$(python3 -V)" =~ "Python 3" ]] && echo "Python 3 is installed"
if [ -d /etc/opkg ]; then
    echo "updating feeds"
    opkg update
    echo
    if [[ $pyv =~ "Python 3" ]]; then
        echo "checking python3-requests"
        if python -c "import requests" &> /dev/null; then
            echo "Requests library already installed"
        else
            opkg install python3-requests
        fi
    else
        echo "checking python-requests"
        if python -c "import requests" &> /dev/null; then
            echo "Requests library already installed"
        else
            opkg install python-requests
        fi
    fi
else
    echo "updating feeds"
    apt-get update
    if [[ $pyv =~ "Python 3" ]]; then
        echo "checking python3-requests"
        if python -c "import requests" &> /dev/null; then
            echo "Requests library already installed"
        else
            apt-get -y install python3-requests
        fi
    else
        echo "checking python-requests"
        if python -c "import requests" &> /dev/null; then
            echo "Requests library already installed"
        else
            apt-get -y install python-requests
        fi
    fi
fi
exit 0