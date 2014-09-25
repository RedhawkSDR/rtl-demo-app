#
# This file is protected by Copyright. Please refer to the COPYRIGHT file
# distributed with this source distribution.
#
# This file is part of REDHAWK core.
#
# REDHAWK core is free software: you can redistribute it and/or modify it under
# the terms of the GNU Lesser General Public License as published by the Free
# Software Foundation, either version 3 of the License, or (at your option) any
# later version.
#
# REDHAWK core is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE.  See the GNU Lesser General Public License for more
# details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this program.  If not, see http://www.gnu.org/licenses/.
#
%define _prefix /var/redhawk/web
%define _rtl_demo %{_prefix}/rtl-demo
%define _rtl_app %{_rtl_demo}/app
%define _rtl_client %{_rtl_demo}/client
%define _supervisor /etc/redhawk-web/supervisor.d
%define _nginx /etc/nginx/conf.d/redhawk-sites

%define bower node_modules/bower/bin/bower
%define grunt node_modules/grunt-cli/bin/grunt


Prefix:         %{_prefix}
Name:		redhawk-rtl-demo
Version:	0.1
Release:	1%{?dist}
Summary:	A sample REDHAWK web application that uses an RTL device.

License:	GPL
BuildRoot:	%(mktemp -ud %{_tmppath}/%{name}-%{version}-%{release}-XXXXXX)
Source0:        %{name}-%{version}.tar.gz

Requires:       python
Requires:       redhawk >= 1.10
Requires:       redhawk-devel
Requires:       redhawk-web
Requires:       rhweb-python-tornado
Requires:       rhweb-python-gevent
BuildRequires:  npm
BuildRequires:  git

%description
%{summary}
 * Commit: __REVISION__
 * Source Date/Time: __DATETIME__

%prep
%setup -q

%build

%install
cd rtl-demo-client
npm install
%{bower} install
%{grunt} dist
cd -

mkdir -p $RPM_BUILD_ROOT%{_rtl_demo}
cp -R rtl-demo-client/dist $RPM_BUILD_ROOT%{_rtl_client}

mkdir -p $RPM_BUILD_ROOT%{_rtl_app}
cp -R rtl-demo-app/bin rtl-demo-app/server $RPM_BUILD_ROOT%{_rtl_app}
cp rtl-demo-app/start.sh          $RPM_BUILD_ROOT%{_rtl_app}


mkdir -p $RPM_BUILD_ROOT%{_supervisor}
cp rtl-demo-app/deploy/rtl-demo-supervisor.conf $RPM_BUILD_ROOT%{_supervisor}/redhawk-rtl-demo.conf

mkdir -p $RPM_BUILD_ROOT%{_nginx}/redhawk-sites
cp rtl-demo-app/deploy/rtl-demo-nginx.conf $RPM_BUILD_ROOT%{_nginx}/rtl-demo.enabled

%clean
rm -rf %{buildroot}

%files
%defattr(-,redhawk,redhawk,-)
%dir %{_rtl_demo}

%dir %{_rtl_app}
%{_rtl_app}/start.sh
%{_rtl_app}/bin
%{_rtl_app}/server

%dir %{_rtl_client}
%{_rtl_client}/index.html
%{_rtl_client}/js
%{_rtl_client}/lib

%defattr(-,root,root,-)
%{_nginx}/rtl-demo.enabled
%{_supervisor}/redhawk-rtl-demo.conf

