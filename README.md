# cloudwave-dashboard
Openstack dashboard for the EU project CloudWave.

During the three years of the project it was necessary to monitor, in a realtime fashion, the metrics coming from the Openstack services and from the specific components developed in years by the partners involved. The charts developed inside the ``CloudWave Realtime`` Horizon panel are inspired by the default and static ``Resource Usage`` which doesn't allow to see how the metric samples change in time (unless you reload the entire page) and also to have multiple charts (1 per metric) on the same page.
With the new panel the project had a graphical way to monitor how the actions taking place into the other partners' components change the values of the interested plotted metrics. This allowed them to have a visual feedback on what was going on inside the testbed by checking multiple metrics in a glance updated every ``x`` seconds.
In function of the Openstack version released among the years the panel was tested on Havana, Juno and Liberty but the code in this repo refers to Liberty which was used during CloudWave Y3.

##Installation
1. Requirements:
  * Openstack Liberty
2. Download the RPM package:
  * wget https://github.com/MDSLab/cloudwave-dashboard/blob/master/packages/cw-dashboard-3.1.0-155.x86_64.rpm
3. Install:
  * rpm -Uvh cw-dashboard-3.1.0-155.x86_64.rpm

##Configuration guide
Inside the panel it was created a configuration file (``realtime.cfg``) where it is possibile to specify the metrics that will appear in the panel menù, included those related to the network interfaces.
