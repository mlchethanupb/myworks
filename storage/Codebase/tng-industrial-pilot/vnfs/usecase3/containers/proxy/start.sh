#!/bin/bash
squid -N -f /etc/squid/squid.conf -z &
squid -f /etc/squid/squid.conf -NYCd 1

