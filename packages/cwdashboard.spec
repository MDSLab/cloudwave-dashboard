Name            : cw-dashboard
Summary         : CloudWave Openstack Dashboards - Liberty
Version         : 3.1.0
Release 	: %{?BUILD_NUMBER}
#Group           : Applications/Programming
License         : GPL
BuildArch       : x86_64
BuildRoot       : %{_tmppath}/%{name}-%{version}-root



# Description gives information about the rpm package. This can be expanded up to multiple lines.
%description
CloudWave Openstack Dashboards - Liberty


# Prep is used to set up the environment for building the rpm package
%prep

# Used to compile and to build the source
%build

# The installation steps. 
%install

rm -rf $RPM_BUILD_ROOT
install -d -m 755 $RPM_BUILD_ROOT/var/www/html/
install -d -m 755 $RPM_BUILD_ROOT/usr/lib/python2.7/site-packages/horizon/templatetags/
install -d -m 755 $RPM_BUILD_ROOT/usr/share/openstack-dashboard/openstack_dashboard/enabled/
install -d -m 755 $RPM_BUILD_ROOT/usr/share/openstack-dashboard/openstack_dashboard/dashboards/admin/
install -d -m 755 $RPM_BUILD_ROOT/usr/share/openstack-dashboard/static/dashboard/js/
install -d -m 755 $RPM_BUILD_ROOT/usr/lib/python2.7/site-packages/horizon/static/horizon/js/

cp ../SOURCES/local_settings_changes.sh $RPM_BUILD_ROOT/var/www/html/.
cp ../SOURCES/set_var.py $RPM_BUILD_ROOT/usr/lib/python2.7/site-packages/horizon/templatetags/.
cp ../SOURCES/_2031_admin_realtime_panel.py $RPM_BUILD_ROOT/usr/share/openstack-dashboard/openstack_dashboard/enabled/.
cp -r ../SOURCES/realtime_CW_phy $RPM_BUILD_ROOT/usr/share/openstack-dashboard/openstack_dashboard/dashboards/admin/.
cp ../SOURCES/horizon.d3linechart.js $RPM_BUILD_ROOT/var/www/html/.


# Post installation steps
%post

echo -e "  Configuring:"

#
# Setup permissions
#
chmod -R +x /usr/share/openstack-dashboard/openstack_dashboard/dashboards/admin/realtime_CW_phy/templates/


#
# Add CW realtime functionalities and customizations (modify js and css files)
#
#Modify interpolation type (from cardinal to linear)   [rickshaw.js]
cwstr="interpolation: 'linear',"
cwvar=`cat /usr/share/javascript/rickshaw/rickshaw.js | grep "interpolation: 'linear',"`
if [[ $cwvar == *"$cwstr"* ]]; then
	echo "\t CLOUDWAVE realtime linear interpolation already added!\n"
else
	from="interpolation: 'cardinal',"
	to="\/\/CLOUDWAVE: Start realtime changes\n\t\t\t\/\/interpolation: 'cardinal',\n\t\t\tinterpolation: 'linear',"
	sed -i "s/$from/$to/g" /usr/share/javascript/rickshaw/rickshaw.js

	from="min: undefined,"
	to="\/\/min: undefined,\n\t\t\tmin: auto,\n\t\t\t\/\/CLOUDWAVE: Stop realtime changes"
	sed -i "s/$from/$to/g" /usr/share/javascript/rickshaw/rickshaw.js
fi

#Modify chart popup width [rickshaw.css]
cwstr="opacity: 1;"$'\n'$'\t'"background: rgba(0, 0, 0, 0.8);"$'\n'$'\t'"//CLOUDWAVE: Start css changes"
cwvar=`cat /usr/share/javascript/rickshaw/rickshaw.css | grep "opacity: 1;"$'\n'$'\t'"background: rgba(0, 0, 0, 0.8);"$'\n'$'\t'"//CLOUDWAVE: Start css changes"`

if [[ $cwvar == *"$cwstr"* ]]; then

	echo "\t CLOUDWAVE realtime chart popup width already added!\n"
else
	from="background: rgba(0, 0, 0, 0.8);"
	to="background: rgba(0, 0, 0, 0.8);\n\t\/\/CLOUDWAVE: Start css changes\n\twidth: 300px;\n\t\/\/CLOUDWAVE: Stop css changes"

	sed -i "s/$from/$to/g" /usr/share/javascript/rickshaw/rickshaw.css
fi


#
# Modify Openstack local_settings to enable Horizon logging to /var/log/horizon/horizon.log
#

cd /var/www/html
echo -e "\t Changing Openstack local_settings file"
./local_settings_changes.sh
chmod 640 /etc/openstack-dashboard/local_settings
chown root:apache /etc/openstack-dashboard/local_settings

touch /var/log/horizon/horizon.log
chown apache:apache /var/log/horizon/horizon.log


#
# Backup horizon.d3linechart.js and install the modified one
#
if [ ! -f /usr/lib/python2.7/site-packages/horizon/static/horizon/js/horizon.d3linechart_ORIG.js ]; then
	cp /usr/lib/python2.7/site-packages/horizon/static/horizon/js/horizon.d3linechart.js /usr/lib/python2.7/site-packages/horizon/static/horizon/js/horizon.d3linechart_ORIG.js
	mv /var/www/html/horizon.d3linechart.js /usr/lib/python2.7/site-packages/horizon/static/horizon/js/horizon.d3linechart.js
fi

#
# Restart http server
#
echo -e "\t Restarting http server..."
systemctl restart httpd
echo -e "\t Restarted http server\n"

echo -e "\t Openstack Dashboards configured\n\n"




# Contains a list of the files that are part of the package
%files
%attr(755, root, -) /var/www/html/local_settings_changes.sh
%attr(755, root, -) /var/www/html/horizon.d3linechart.js
%attr(644, root, -) /usr/share/openstack-dashboard/openstack_dashboard/dashboards/admin/realtime_CW_phy/*
%attr(644, root, -) /usr/lib/python2.7/site-packages/horizon/templatetags/set_var.py
%attr(644, root, -) /usr/share/openstack-dashboard/openstack_dashboard/enabled/_2031_admin_realtime_panel.py


# Used to store any changes between versions
%changelog


%postun
echo -e "\t Removing panels folders..."
	rm -rf /usr/share/openstack-dashboard/openstack_dashboard/dashboards/admin/realtime_CW_phy

echo -e "\t Panels folders removed!\n"

#
# Restart http server
#
echo -e "\t Restarting http server..."
	systemctl restart httpd
echo -e "\t Restarted http server\n"

