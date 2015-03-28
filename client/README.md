# REDHAWK RTL Demo Client

## Description

Contains the REDHAWK RTL Demo front end client

## REDHAWK Documentation

REDHAWK Website: [www.redhawksdr.org](http://www.redhawksdr.org)

## Copyrights

This work is protected by Copyright. Please refer to the [Copyright File](COPYRIGHT) for updated copyright information.

## License

The REDHAWK RTL Demo Client is licensed under the GNU Lesser General Public License (LGPL).

## Running

The REDHAWK RTL Demo Client is a frontend application and requires a backend REST service to run. It has been built to
support the REDHAWK RTL Demo Application project and can be used by downloading that project and placing the contents
(or symbolic link) of this repository in a directory `static/rtldemo` of the RTL Demo Application project. Follow the
steps listed in RTL Demo Application to run both parts of the application.

The rtl demo can then be viewed by going to `http://<location:port>/apps/rtldemo/`.

Dependencies for this project can be downloaded using `npm` with the following commands:

    npm install
    node_modules/bower/bin/bower install

Distribution versions of this project by running:

    node_modules/grunt/bin/grunt dist

