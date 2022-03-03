docker run -u=$(id -u $USER):$(id -g $USER) \
           -e DISPLAY \
           -v /tmp/.X11-unix ubuntu \
           --rm \
           budget-gui-app \