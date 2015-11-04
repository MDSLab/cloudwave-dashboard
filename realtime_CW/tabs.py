# Copyright 2014 University of Messina (UniMe)
#
# Author: Carmelo Romeo <caromeo@unime.it>
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

# -*- encoding: utf-8 -*-
#
# Author: Carmelo Romeo <caromeo@unime.it>
#
#


from django.utils.translation import ugettext_lazy as _  # noqa

from horizon import exceptions
from horizon import tabs
from openstack_dashboard import api
from openstack_dashboard.api import ceilometer, heat

#Logging and novaclient imports
import logging
LOG = logging.getLogger(__name__)
from openstack_dashboard.api import nova


class GlobalStatsTab(tabs.Tab):
    name = _("Stats")
    slug = "stats"
    template_name = ("admin/realtime_CW/realtime.html")
    preload = False

    @staticmethod
    def _get_flavor_names(request):
        try:
            flavors = api.nova.flavor_list(request, None)
            return [f.name for f in flavors]
        except Exception:
            return ['m1.tiny', 'm1.small', 'm1.medium',
                    'm1.large', 'm1.xlarge']

    def get_context_data(self, request):
        query = [{"field": "metadata.OS-EXT-AZ:availability_zone",
                  "op": "eq",
                  "value": "nova"}]
        try:
            instances = ceilometer.resource_list(request, query,
                ceilometer_usage_object=None)
            meters = ceilometer.meter_list(request)
        except Exception:
            instances = []
            meters = []
            exceptions.handle(request,
                              _('Unable to retrieve Nova Ceilometer '
                                'metering information.'))
        instance_ids = set([i.resource_id for i in instances])
        instance_meters = set([m.name for m in meters
                               if m.resource_id in instance_ids])

        meter_titles = {"instance": _("Duration of instance"),
                        "memory": _("Volume of RAM in MB"),
                        "cpu": _("CPU time used"),
                        "cpu_util": _("Average CPU utilisation"),
                        "vcpus": _("Number of VCPUs"),
                        "disk.read.requests": _("Number of read requests"),
                        "disk.write.requests": _("Number of write requests"),
                        "disk.read.bytes": _("Volume of reads in B"),
                        "disk.write.bytes": _("Volume of writes in B"),
                        "disk.root.size": _("Size of root disk in GB"),
                        "disk.ephemeral.size": _("Size of ephemeral disk "
                            "in GB"),
                        "network.incoming.bytes": _("Number of incoming bytes "
                            "on the network for a VM interface"),
                        "network.outgoing.bytes": _("Number of outgoing bytes "
                            "on the network for a VM interface"),
                        "network.incoming.packets": _("Number of incoming "
                            "packets for a VM interface"),
                        "network.outgoing.packets": _("Number of outgoing "
                            "packets for a VM interface")}

        for flavor in self._get_flavor_names(request):
            name = 'instance:%s' % flavor
            hint = (_('Duration of instance type %s (openstack flavor)') %
                    flavor)
            meter_titles[name] = hint

        class MetersWrap(object):
            """ A quick wrapper for meter and associated titles. """
            def __init__(self, meter, meter_titles):
                self.name = meter
                self.title = meter_titles.get(meter, "")

        meters_objs = [MetersWrap(meter, meter_titles)
                       for meter in sorted(instance_meters)]



        class MetersAndInstanceWrap(object):
	    """
            def __init__(self, meter, meter_titles, instance_name):
                self.name = meter
                self.title = meter_titles.get(meter, "")
                self.resource_id = list(instance_name)[0]
	    """
            def __init__(self, meter, instance_name):
                self.name = meter
                self.resource_id = instance_name

            def get_name(self):
                return self.name
	    """
            def get_title(self):
                return self.title
	    """
            def get_resourceid(self):
                return self.resource_id

        servers, more = nova.server_list(request)
        #LOG.debug('entire server_list: %s', servers)


        instance_metrics = []

        for vm in servers:
                query_metric = [{"field": "resource_id", "op": "eq", "value": vm.id }]

                vm_meter_list = ceilometer.meter_list(request, query_metric)
                #LOG.debug('VM_METER_LIST: %s', vm_meter_list)

		for metric in vm_meter_list:
			instance_metrics.append(MetersAndInstanceWrap(metric.name, metric.resource_id))

        #Wrapper for Stack_id and Resources
        class StackAndResourcesWrap(object):
            def __init__(self, stack_id, stack_name, resources_number, stack_resources):
					self.stack_id = stack_id
					self.stack_name = stack_name
					self.resources_number = resources_number
					self.stack_resources = stack_resources

	#Wrapper for Resources
	class ResourceWrap(object):
	    def __init__(self, stack_resource_id, stack_resource_name):
					self.stack_resource_id = stack_resource_id
					self.stack_resource_name = stack_resource_name


	stacks_obj = []
	stacks, more, moreandmore = heat.stacks_list(request)
	#LOG.debug('stack-list %s', stacks)

	for stack in stacks:
		resources_x_stack = heat.resources_list(request,stack.stack_name)
		#LOG.debug('RESOURCES: %s', len(resources_x_stack))

		resources_obj = []
		for resource in resources_x_stack:
			if resource.resource_type == "OS::Nova::Server":
				resources_obj.append(ResourceWrap(resource.physical_resource_id, resource.resource_name))
				#LOG.debug('resource_type %s', resource.resource_type)
		stacks_obj.append(StackAndResourcesWrap(stack.id, stack.stack_name, len(resources_obj), resources_obj))

       	#LOG.debug('STACK AND RESOURCES WRAP: %s', stacks_obj)


        context = {'vms': servers, 'vmmeters': instance_metrics, 'stacks_info': stacks_obj}
        #context = {'meters': meters_objs}

        return context

class CeilometerOverviewTabs(tabs.TabGroup):
    slug = "ceilometer_overview"
    tabs = (GlobalStatsTab,)
    sticky = True
