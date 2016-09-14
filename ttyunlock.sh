#! /bin/sh
# Convenience script to remove /tmp/ttylock lockfile which blocks other
# components from interrupting by sending output to the loop. 

rm /tmp/ttylock
