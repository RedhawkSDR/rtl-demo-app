# REDHAWK RTL Demo Application

## Description

Contains the REDHAWK RTL Demo backend server application

## REDHAWK Documentation

REDHAWK Website: [www.redhawksdr.org](http://www.redhawksdr.org)

## Copyrights

This work is protected by Copyright. Please refer to the [Copyright File](src/COPYRIGHT) for updated copyright information.

## License

The REDHAWK RTL Demo Application is licensed under the GNU Lesser General Public License (LGPL).

## Running

For Development/Test environments there are scripts to automatically create a local environment and run the server. 

    ./setup.py install
    ./start.sh --port=<desired_port>

The tools above will create a virtual environment in the current directory. 

For a more permanent solution, consult the `requirements.txt` and run the following command as a service:

     ./server/server.py --port=<desired_port>

`supervisord` is a common tool for running commands as a service and a sample configuration snippet 
can be found at `deploy/rest-python-supervisor.conf`.

Once running the REST Interface can be tested at `http://localhost:<desired_port>/rtl/survey`.