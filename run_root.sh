#!/bin/bash
docker run --rm -it -v $PWD:/home/local --workdir /home/local rootproject/root:6.22.00-conda /bin/bash
