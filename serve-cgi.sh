#! /bin/sh
# Convenience wrapper for executing the python CGI HTTP server so we
# don't need to run apache on the raspberry pi. 

cd /opt/ttycommands
python -m CGIHTTPServer
