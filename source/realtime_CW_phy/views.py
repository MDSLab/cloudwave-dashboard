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

from datetime import datetime  # noqa
from datetime import timedelta  # noqa

import json, os, subprocess, requests

from django.http import HttpResponse   # noqa
from django.utils.translation import ugettext_lazy as _  # noqa
from django.views.generic import TemplateView  # noqa

from horizon import exceptions
from horizon import tabs

from openstack_dashboard import api
from openstack_dashboard.api import ceilometer

from openstack_dashboard.dashboards.admin.realtime_CW_phy import tabs as \
    metering_tabs

import logging
LOG = logging.getLogger(__name__)

import keystoneclient.v2_0.client as ksclient


#Admin token and delta_t initialization
ENV_HEAT_OS_API_VERSION = "1"
ENV_OS_AUTH_URL = "http://keystone:35357/v2.0"
ENV_OS_USERNAME = "admin"
ENV_OS_TENANT_NAME = "admin"
ENV_OS_PASSWORD = "0penstack"

headers = {}

class IndexView(tabs.TabbedTableView):
    tab_group_class = metering_tabs.CeilometerOverviewTabs
    template_name = 'admin/realtime_CW_phy/index.html'

    #Admin token and headers section
    global headers

    keystone = ksclient.Client(
        auth_url=ENV_OS_AUTH_URL,
        username=ENV_OS_USERNAME,
        password=ENV_OS_PASSWORD,
        tenant_name= ENV_OS_TENANT_NAME
    )

    #Headers used to retrieve data from mongo using ceilometerclient
    headers = {'User-Agent': 'ceilometerclient.openstack.common.apiclient',  'X-Auth-Token': keystone.auth_token, 'Content-Type': 'application/json'}


class SamplesView(TemplateView):
    template_name = "admin/realtime_CW_phy/samples.csv"

    @staticmethod
    def _series_for_meter(samples, dictionary_id_name, start_time, offset_time):
    #def _series_for_meter(samples, dictionary_id_name, start_time, offset_time, events):

        series = []
	vect_lines = []
	highest_value = 0


	LOG.debug('DICT: %s', dictionary_id_name)


	for sample in samples:

		sample_time = sample["timestamp"][:10]+' '+sample["timestamp"][11:19]

		tmp_sample_time = datetime.strptime(sample_time, '%Y-%m-%d %H:%M:%S')
		hours_offset = int( int(offset_time) / 60)

		if hours_offset < 0:
			new_hours_offset = -hours_offset
			sample_time = tmp_sample_time - timedelta(hours=new_hours_offset)
		else:
			sample_time = tmp_sample_time + timedelta(hours=hours_offset)

		sample_time = sample_time.strftime("%Y-%m-%dT%H:%M:%S")


		if sample["volume"] > highest_value:
			highest_value = sample["volume"]



		flag = False
		if len(vect_lines) != 0:
			for line in vect_lines:
				same_time = False

				if line["name"] == sample["resource_name"]:
					#This for is necessary because the vlan samples in CW are sent multiple times with the same timestamp because of infrastructure necessities
					for x in line["data"]:
						if x["x"] == sample_time:
							same_time = True
							break
					if not same_time:
						line['data'].insert(0,{'x': sample_time, 'y': sample["volume"]})

					flag = True
					break


		if not flag:
			point = {'unit': sample["unit"],
				'name': sample["resource_name"],
				'data': [{'x': sample_time, 'y': sample["volume"]}], 'renderer': 'line'}

			vect_lines.append(point)
			
	#LOG.debug('VECT LINES: %s', vect_lines)

	for vect in vect_lines:
		#LOG.debug('PRE VECT: %s', vect)
		vect["data"] = sorted(vect["data"], key=lambda k: k["x"], reverse = False)
		#LOG.debug('POST VECT: %s', vect)

		series.append(vect)
	#LOG.debug('PRE SERIES: %s', series)
	series = sorted(series, key=lambda k: k["name"], reverse = True)
	#LOG.debug('POST SERIES: %s', series)
        return series

    def get(self, request, *args, **kwargs):

	#This method takes all the information read from the html page and retrieves samples vm by vm and concatenate them to plot the lines
	samples = []

	metric = ""
	dict_id_name = []

	thread_start_time = ""
	offset_time = request.GET.get('offset_time', None)

	vms_selected_list = request.GET.get('vms_selected_list', None)

	#if vms_selected_list != None:
	if vms_selected_list != None and vms_selected_list != "":

		samples_number = request.GET.get('samples_number', None)
		thread_start_time = request.GET.get('th_start_time', None)

		vms_vector = vms_selected_list.split('&')

		metric = request.GET.get('stack_metrics', None)
		query_resources = ""

		limit_size = int(samples_number) * len(vms_vector)

		start = r'{\">\":{\"timestamp\":\"'+thread_start_time+r'\"}},'
		orderby = r'"orderby" : "[{\"timestamp\": \"DESC\"}, {\"counter_name\": \"ASC\"}]"'
		limit = r'"limit":'+str(limit_size)
		counter_name = r'{\"=\":{\"counter_name\":\"'+str(metric)+r'\"}}'


		count = 0
		#vlan_unique = ""
		LOG.debug('VMS VECTOR: %s', vms_vector)
		for vm in vms_vector:
			vm_id_name = vm.split(';')

			dict_id_name.append({"resource_id": vm_id_name[0], "resource_name": vm_id_name[1]})

			if query_resources == "":
				query_resources = r'{\"=\":{\"resource_id\":\"'+vm_id_name[0]+r'\"}}'
			else:
				query_resources += r',{\"=\":{\"resource_id\":\"'+vm_id_name[0]+r'\"}}'
			count += 1

		if count == 1:
			query_rt = r'{"filter": "{\"and\":['+str(counter_name)+r','+start+str(query_resources)+r']}",'+str(orderby)+r','+str(limit)+'}'
		else:
			query_rt = r'{"filter": "{\"and\":['+str(counter_name)+r','+start+r'{\"or\":['+str(query_resources)+r']}]}",'+str(orderby)+r','+str(limit)+'}'


		LOG.debug('QUERY: %s', query_rt)

                output = requests.post('http://ceilometer:8777/v2/query/samples', headers=headers, data=query_rt).text
		result = json.loads(output)
		#LOG.debug('RESULT: %s', result)
		#LOG.debug('len(result): %s', len(result))

		for i in range(len(result)):
			json_sample = result[i]

			unit = json_sample["unit"]
			volume = json_sample["volume"]


			#This for is necessary because the vlan samples in CW are sent multiple times with the same timestamp because of infrastructure necessities
			#--------------------------------------------------------------
			if json_sample["meter"] == "vlan.bandwidth":

				unit = "Mb/s"
				volume = round((8* json_sample["volume"] / 1000 / 1000),3)


				if json_sample["metadata"]["unique"] == "1":
					resource_name = json_sample["resource_id"]
				else:
					continue

			elif json_sample["meter"] == "vlan.saturation" or "host" in json_sample["meter"] or "load" in json_sample["meter"]:
				resource_name = json_sample["resource_id"]

			elif "network" in json_sample["meter"]:
				unit = "Mb/s"
				volume = round((8* json_sample["volume"] / 1000 / 1000),3)
				resource_name = json_sample["resource_id"]

			elif json_sample["metadata"]["display_name"] == "ti-logcollector": 
				resource_name = "ti-app"

			else: resource_name = json_sample["metadata"]["display_name"]
			#--------------------------------------------------------------

			if len(samples) != 0:
				flag_insert = True
				for sample in samples:
					if sample["timestamp"] == json_sample["timestamp"] and sample["resource_name"] == resource_name:
						flag_insert = False
						break
				if flag_insert:
					samples.append({"resource_name": resource_name, "timestamp": json_sample["timestamp"], "volume": volume, "unit": unit})
			else:
				samples.append({"resource_name": resource_name, "timestamp": json_sample["timestamp"], "volume": volume, "unit": unit})


		samples = sorted(samples, key=lambda k: k["timestamp"], reverse = False)

		LOG.debug('SAMPLES: %s', samples)
		LOG.debug('len(samples): %s', len(samples))



	series = self._series_for_meter(samples, dict_id_name, thread_start_time, offset_time)
	#series = self._series_for_meter(samples, dict_id_name, thread_start_time, offset_time, events)

	dict_id_name = {}
        ret = {}
        ret['series'] = series
        ret['settings'] = {}
	
        #return HttpResponse(json.dumps(ret), mimetype='application/json')
	return HttpResponse(json.dumps(ret), content_type='application/json')
	
