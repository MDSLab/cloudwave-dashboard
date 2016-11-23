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


#LIBERTY START
import keystoneclient.v2_0.client as ksclient
from heatclient import client as heat_client

ENV_HEAT_OS_API_VERSION = "1"
ENV_OS_AUTH_URL = "http://keystone:35357/v2.0"
ENV_OS_USERNAME = "admin"
ENV_OS_TENANT_NAME = "admin"
ENV_OS_PASSWORD = "0penstack"
#LIBERTY STOP

#RESTYLE ADDINGS
#-----------------------------------------------------------------------
import ConfigParser
import os, threading


instance_metrics = []
stacks_obj = []

samples = []

config = ConfigParser.RawConfigParser()
config.read(os.path.join(os.path.dirname(__file__), 'realtime.cfg'))
instance_metrics = [e.strip() for e in config.get('Metrics', 'metrics_list').split(',')]
hosts_list = [e.strip() for e in config.get('Hosts', 'hosts_list').split(',')]
fake_phy_resource_ids = [e.strip() for e in config.get('Resource_ids', 'fake_phy_resourceid_list').split(',')]


# Static heat parameters
#heat_service_id = "81d0e80a8f0b4c19b99e8234e787b6e1"
fixed_heat_endpoint = "http://heat:8004/v1/%(tenant_id)s"
heat_endpoint = "http://heat:8004/v1/e24ab9cae3ad4cf4a5658a4dbacbd2ac"
#-----------------------------------------------------------------------


class GlobalStatsTab(tabs.Tab):
    name = _("Stats")
    slug = "stats"
    template_name = ("admin/realtime_CW_phy/realtime.html")
    preload = False

    #stacks_obj = []

    def get_context_data(self, request):
	global stacks_obj
	stacks_obj = []

	# STACKS MANAGEMENT IN MULTITENANCY
	#-------------------------------------------------------------------------------------------------------------
	flag_demo = True

	if flag_demo:
		stacks_obj = [{'stack_id': u'94c6d43b-21b5-48a9-abd4-f831c69caf2d', 'stack_name': u'cw-stress', 'resources': [{'resource_name': u'cw-iperf', 'resource_id': u'9bca4d12-098b-4695-9b17-4c12cc4a45c5'}]}, {'stack_id': u'64f65e49-14a1-41f5-a24a-1a506a43232e', 'stack_name': u'wordpress', 'resources': [{'resource_name': u'wordpress', 'resource_id': u'0fc44f1c-6435-4d6a-af39-3ca458ced25c'}, {'resource_name': u'db-wp-unime', 'resource_id': u'2216b369-600a-466b-a550-387a475a437c'}]}, {'stack_id': u'a582aa8b-c164-451c-8add-a2f9176cf543', 'stack_name': u'DAND_DELETEME1', 'resources': [{'resource_name': u'DANDvm1', 'resource_id': u'30e3729a-d36d-4067-b854-037778a4579d'}]}, {'stack_id': u'bee8123c-7f56-4e05-a287-cabf82a63241', 'stack_name': u'unime', 'resources': [{'resource_name': u'test_ubu_double_1', 'resource_id': u'f4533a60-ad29-488e-a223-7a238e249316'}, {'resource_name': u'test_ubu_double_2', 'resource_id': u'43f9fb70-f975-46d0-9f5a-9ba514e35b9d'}]}, {'stack_id': u'9d26dfe6-f142-45f1-ae4c-d79d7eccea53', 'stack_name': u'noisy', 'resources': [{'resource_name': u'noisy-big-3', 'resource_id': u'd374f4b8-d78a-413a-8266-fa9e5e4b57fa'}, {'resource_name': u'noisy-big-2', 'resource_id': u'03d05707-9e0d-4bc5-98dd-c627f2b9b3eb'}, {'resource_name': u'noisy-big-1', 'resource_id': u'1bb0ec39-cb5f-4f6d-9f8b-eec48135db5f'}, {'resource_name': u'noisy-iperf', 'resource_id': u'dea9616c-eb31-4623-b3e5-6b992a7c8c43'}]}, {'stack_id': u'893e4d07-a15f-40f7-aa0a-be23d59108eb', 'stack_name': u'testONE', 'resources': [{'resource_name': u'testONE-cw-ubuntu-umpb54clhfyx', 'resource_id': u'b37fee18-b3c0-44cf-98af-65e2c6efb715'}]}, {'stack_id': u'9def8647-024d-4d59-b802-8e34559fe11b', 'stack_name': u'CWPROBE', 'resources': [{'resource_name': u'CWPROBE-ubu14-nm4iy3slwnr5', 'resource_id': u'ae55c6ae-babd-4567-96bd-95817a73f05d'}, {'resource_name': u'CWPROBE-ubu15-gba7lnvltenz', 'resource_id': u'994f9958-cb94-4d81-9ede-db8293ced902'}]}, {'stack_id': u'8c44594b-93d3-4519-9261-8141a520d36a', 'stack_name': u'ti-y2', 'resources': [{'resource_name': u'demofe', 'resource_id': u'1f8aeeeb-625f-4720-a3ce-2b7a633dd181'}, {'resource_name': u'demotmff1', 'resource_id': u'6a4e50dc-226c-44eb-ae79-3e2bc8c10d0a'}, {'resource_name': u'ti-demols', 'resource_id': u'ae758abc-eccc-4359-8b71-d4396956b227'}]}, {'stack_id': u'a1a66cb7-f43b-4357-8b36-e500175083f8', 'stack_name': u'ti-app', 'resources': [{'resource_name': u'ti-app', 'resource_id': u'dfbe88b7-0f6e-4f8b-9c7e-a53cebea8375'}]}, {'stack_id': u'5ce549cd-5fe2-49ec-9e06-71f18e89e6d9', 'stack_name': u'cloudmore', 'resources': [{'resource_name': u'cw-lg', 'resource_id': u'1771c6db-c9f8-4d44-9b6d-07216d553d13'}, {'resource_name': u'cw-fe', 'resource_id': u'fcf41156-a0d7-47b8-af6e-5fd01d1471ab'}, {'resource_name': u'cw-ms', 'resource_id': u'b63c155f-69ad-4917-bb2b-ecc07cc66ff3'}, {'resource_name': u'cw-test', 'resource_id': u'315f6fca-a3c7-471c-bf3f-ff5795eba7d4'}]}, {'stack_id': u'2446704b-a1e0-4606-8647-1895558a1c4c', 'stack_name': u'load_gen', 'resources': [{'resource_name': u'vlan3_loadgen2', 'resource_id': u'f561d259-3458-4e96-9bf2-08345c3a5677'}, {'resource_name': u'vlan3_loadgen3', 'resource_id': u'de286354-d852-4081-9e98-02bc79efd8ee'}, {'resource_name': u'vlan2_loadgen1', 'resource_id': u'c86e2aaa-2380-4f1c-a320-51b8710855f5'}, {'resource_name': u'vlan2_loadgen2', 'resource_id': u'063397d3-efb3-4bf7-acc5-53d4411ee0ce'}, {'resource_name': u'vlan2_loadgen3', 'resource_id': u'a5797df7-5cce-4654-b073-eeb69095bbb4'}, {'resource_name': u'vlan3_loadgen1', 'resource_id': u'5b9e214d-4fcb-46e1-a356-d20cb15b6cdd'}, {'resource_name': u'vlan1_loadgen1', 'resource_id': u'ea2386ec-1b37-4342-a27d-1cf0dadc84da'}, {'resource_name': u'vlan1_loadgen2', 'resource_id': u'c3e9c4a5-7917-43f7-96d6-57de535ef62c'}, {'resource_name': u'vlan1_loadgen3', 'resource_id': u'76363e6b-067b-4d97-bba4-39125cffc790'}]}]

	else:
		#Retrieve heat_service_id and heat_endpoint from keystone
		keystone = ksclient.Client(
			auth_url=ENV_OS_AUTH_URL,
			username=ENV_OS_USERNAME,
			password=ENV_OS_PASSWORD,
			tenant_name= ENV_OS_TENANT_NAME
		)

		#Retrieve stacks from stack_list
		heat = heat_client.Client(
			ENV_HEAT_OS_API_VERSION,
			endpoint = heat_endpoint,
			token = keystone.auth_token
		)

		stacks_threads = []

		for stack in heat.stacks.list(global_tenant=True):
			LOG.debug('STACK NAME: %s', stack.stack_name)
			t = threading.Thread(target=getStackResourcesThread, args=(request, stack))
			stacks_threads.append(t)

			t.setDaemon(True)
			t.start()

		for t in stacks_threads: t.join()

	stacks_obj = sorted(stacks_obj, key=lambda k: k["stack_name"], reverse = False)
	LOG.debug('STACKS: %s', stacks_obj)
	#-------------------------------------------------------------------------------------------------------------

       	#LOG.debug('STACK AND RESOURCES WRAP: %s', stacks_obj)
	context = {'vmmeters': instance_metrics, 'hosts': hosts_list, 'stacks_info': stacks_obj, 'fake_phy_resource_ids': fake_phy_resource_ids}

        return context


class CeilometerOverviewTabs(tabs.TabGroup):
    slug = "ceilometer_overview"
    tabs = (GlobalStatsTab,)
    sticky = True



#TRHEADS SECTION
#---------------------------------------------------------------------------------------------------------------------------
def getStackResourcesThread(request, stack):
	# LOG.info('\n\n\nStack: %s - %s - Project: %s\n\n', stack.id, stack.stack_name, stack.project)
	#global fixed_heat_endpoint
	global stacks_obj
	temp_endpoint = fixed_heat_endpoint.replace('%(tenant_id)s', stack.project )

	keystone_temp = ksclient.Client(
		auth_url=ENV_OS_AUTH_URL,
		username=ENV_OS_USERNAME,
		password=ENV_OS_PASSWORD,
		tenant_id=stack.project
	)

	heat_temp = heat_client.Client(
		ENV_HEAT_OS_API_VERSION,
		endpoint = temp_endpoint,
		token = keystone_temp.auth_token
	)

	resources_obj = []
	for resource in heat_temp.resources.list(stack.id):
		if resource.resource_type == "OS::Nova::Server":
			server = nova.server_get(request, resource.physical_resource_id)
			resources_obj.append({"resource_id": resource.physical_resource_id, "resource_name": server.name})

	stacks_obj.append({"stack_id": stack.id, "stack_name": stack.stack_name, "resources": resources_obj})
#---------------------------------------------------------------------------------------------------------------------------
