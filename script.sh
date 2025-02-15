#!/bin/bash
python3 monitoring.py &
python3 port_monitor.py &
wait