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

import json

from django.http import HttpResponse   # noqa
from django.utils.translation import ugettext_lazy as _  # noqa
from django.views.generic import TemplateView  # noqa

from horizon import exceptions
from horizon import tabs

from openstack_dashboard import api
from openstack_dashboard.api import ceilometer

from openstack_dashboard.dashboards.admin.realtime_CW import tabs as \
    metering_tabs

import logging
LOG = logging.getLogger(__name__)



class IndexView(tabs.TabbedTableView):
    tab_group_class = metering_tabs.CeilometerOverviewTabs
    template_name = 'admin/realtime_CW/index.html'


class SamplesView(TemplateView):
    template_name = "admin/realtime_CW/samples.csv"

    @staticmethod
    #start fix
    #def _series_for_meter(samples, dictionary_id_name):
    def _series_for_meter(samples, dictionary_id_name, start_time, offset_time):
    #stop fix

        series = []
	vect_lines = []
	
	for sample in samples:

		#start fix
		sample_time = sample.timestamp[:10]+' '+sample.timestamp[11:19]
		tmp_sample_time = datetime.strptime(sample_time, '%Y-%m-%d %H:%M:%S')
		hours_offset = int( int(offset_time) / 60)

		if hours_offset < 0:
			new_hours_offset = -hours_offset
			sample_time = tmp_sample_time - timedelta(hours=new_hours_offset)

		else:
			sample_time = tmp_sample_time + timedelta(hours=hours_offset)

		sample_time = sample_time.strftime("%Y-%m-%dT%H:%M:%S")
		#stop fix

		flag = "False"
		if len(vect_lines) != 0:
			for line in vect_lines:
				if line['name'] == dictionary_id_name[sample.resource_id]:
					flag = "True"
					#line['data'].insert(0,{'x': sample.timestamp[:19], 'y': sample.counter_volume})
					#line['data'].insert(0,{'x': new_time, 'y': sample.counter_volume})
					line['data'].insert(0,{'x': sample_time, 'y': sample.counter_volume})
					break

		if flag == "False":
			"""
			point = {'unit': sample.counter_unit,
       	                 'name': dictionary_id_name[sample.resource_id],
               	         'data': [{'x': sample.timestamp[:19], 'y': sample.counter_volume}]}
			"""
			point = {'unit': sample.counter_unit,
			 'name': dictionary_id_name[sample.resource_id],
			 'data': [{'x': sample_time, 'y': sample.counter_volume}]}
			

			vect_lines.append(point)

	for vect in vect_lines:
		series.append(vect)		
	
        return series

    def get(self, request, *args, **kwargs):

	#This method takes all the information read from the html page and retrieves samples vm by vm and concatenate them to plot the lines
	samples = ""
	part_samples = ""
	metric = ""
	dict_id_name = {}
	flag_metric = "False"

	#start fix
	thread_start_time = ""
	offset_time = request.GET.get('offset_time', None)
	#stop fix
	#LOG.debug('Request %s', request)

	vms_selected_list = request.GET.get('vms_selected_list', None)
	#LOG.debug('VMS_SELECTED_LIST %s', vms_selected_list)

	#if vms_selected_list != None:
	if vms_selected_list != None and vms_selected_list != "":

		samples_number = request.GET.get('samples_number', None)
		thread_start_time = request.GET.get('th_start_time', None)

		vms_vector = vms_selected_list.split('&')

		#LOG.debug('VMS_LIST: %s SAMPLE_NUM: %s TH_TIME: %s', vms_selected_list, samples_number, thread_start_time);


		for vm in vms_vector:
			vm_id_name = vm.split(';')

			if flag_metric == "False":
				metric = vm_id_name[0]
				flag_metric = "True"

			#This dictionary is used to insert names of the vms in the plot legend (e.g.: {resource_id: resource_name})
			dict_id_name.update({vm_id_name[1]: vm_id_name[2]})
		
			query = [{
				"field": "resource_id",
				"op": "eq",
				"value": vm_id_name[1] }]
		

			query += [{
				"field": "timestamp",
				"op": "gt",
				"value": thread_start_time}]


			#Represents the maximum number of samples to retrieve from mongo and to plot on the graph. It is multiplied by the number of vms selected!
			limit=samples_number
               
			#We retrieve samples for each vm separately and then concatenate them to get all the samples to plot 
			part_samples = ceilometer.rt_sample_list(request, metric, query, limit)

			if samples == "":
				samples = part_samples
			else:
				samples += part_samples
                LOG.debug('len(samples): %s', len(samples))

	#start fix
	#series = self._series_for_meter(samples, dict_id_name)
	series = self._series_for_meter(samples, dict_id_name, thread_start_time, offset_time)
	#stop fix

	dict_id_name = {}
        ret = {}
        ret['series'] = series
        ret['settings'] = {}
	
        return HttpResponse(json.dumps(ret),
            mimetype='application/json')
	
