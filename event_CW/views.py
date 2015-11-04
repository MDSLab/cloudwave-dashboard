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

from openstack_dashboard.dashboards.admin.event_CW import tabs as \
    metering_tabs

import logging, string
LOG = logging.getLogger(__name__)



class IndexView(tabs.TabbedTableView):
    tab_group_class = metering_tabs.CeilometerOverviewTabs
    template_name = 'admin/event_CW/index.html'


class SamplesView(TemplateView):

    @staticmethod
    def _series_for_meter(samples, dictionary_id_name, event_type, event_time, offset_time, start_time, end_time):
        series = []
	vect_lines = []
	highest_value = 0
	hours_offset = 0

	#LOG.debug('EVENT_TYPE: %s EVENT_TIME: %s OFFSET: %s', event_type, event_time, offset_time)

	if event_time:
		hours_offset = int( int(offset_time) / 60)
		tmp_event_time = datetime.strptime(event_time, '%Y-%m-%d %H:%M:%S')

		if hours_offset < 0:
			new_hours_offset = -hours_offset
			event_time = tmp_event_time - timedelta(hours=new_hours_offset)
		else:
			event_time = tmp_event_time + timedelta(hours=hours_offset)

		event_time = event_time.strftime("%Y-%m-%dT%H:%M:%S")

		#Creating event bar
		event_point = {'unit': '(event)', 'name': event_type, 'data': [{'x': event_time, 'y': 0}], 'renderer': 'bar'}
		vect_lines.append(event_point)

	#Count samples before and after the centered event
	samples_before_event = {}
	samples_after_event = {}
	first_sample_in_time = {}
	last_sample_in_time = {}

	if start_time and end_time:
		if hours_offset < 0:
			new_hours_offset = -hours_offset
			start_time -= timedelta(hours=new_hours_offset)
			end_time -= timedelta(hours=new_hours_offset)
		else:
			start_time += timedelta(hours=hours_offset)
			end_time += timedelta(hours=hours_offset)


	for sample in samples:

		#start fix date offset
		sample_time = sample.timestamp[:10]+' '+sample.timestamp[11:19]
		tmp_sample_time = datetime.strptime(sample_time, '%Y-%m-%d %H:%M:%S')

		if hours_offset < 0:
			new_hours_offset = -hours_offset
			sample_time = tmp_sample_time - timedelta(hours=new_hours_offset)

		else:
			sample_time = tmp_sample_time + timedelta(hours=hours_offset)

		sample_time = sample_time.strftime("%Y-%m-%dT%H:%M:%S")

		#LOG.debug('NEW_TIME: %s', sample_time)
		#stop fix date offset

		#Saving highest value of the samples
		if sample.counter_volume > highest_value:
			highest_value = sample.counter_volume

		flag = "False"
		if len(vect_lines) != 0:
			for line in vect_lines:
				if line['name'] == dictionary_id_name[sample.resource_id]:
					flag = "True"
					#line['data'].append({'x': sample.timestamp[:19], 'y': sample.counter_volume})
					line['data'].insert(0,{'x': sample_time, 'y': sample.counter_volume})

					#Updating left and right samples numbers
					if sample_time <= event_time:
						samples_before_event[str(line['name'])] += 1
					elif sample_time > event_time:
						samples_after_event[str(line['name'])] += 1


					if first_sample_in_time[str(line['name'])] > sample_time:
						first_sample_in_time[str(line['name'])] = sample_time
					if last_sample_in_time[str(line['name'])] < sample_time:
						last_sample_in_time[str(line['name'])] = sample_time

					break

		if flag == "False":
			point = {'unit': sample.counter_unit,
       	                 'name': dictionary_id_name[sample.resource_id],
               	         'data': [{'x': sample_time, 'y': sample.counter_volume}], 'renderer': 'line'}

			vect_lines.append(point)

			#Updating left and right samples numbers
			if sample_time <= event_time:
				samples_before_event[dictionary_id_name[sample.resource_id]] = 1
				samples_after_event[dictionary_id_name[sample.resource_id]] = 0

			elif sample_time > event_time:
				samples_before_event[dictionary_id_name[sample.resource_id]] = 0
				samples_after_event[dictionary_id_name[sample.resource_id]] = 1

			first_sample_in_time[dictionary_id_name[sample.resource_id]] = sample_time
			last_sample_in_time[dictionary_id_name[sample.resource_id]] = sample_time
			#ADDED - stop

	#Some LOGs
	#LOG.debug('DICT_BEFORE: %s DICT_AFTER: %s', samples_before_event, samples_after_event)
	#LOG.debug('First_sample_in_time: %s Last_sample_in_time: %s', first_sample_in_time, last_sample_in_time)

	for line in vect_lines:
		if line['name'] == event_type:
			#LOG.debug('LINEA: %s X: %s', line['data'], line['data'][0]['x'])
			line['data'][0]['y'] = highest_value 

		#To center the event's bar we need to add samples to the left and right sides of the rickshaw graph
		else:
			if int(len(samples) / 2) > samples_before_event[str(line['name'])]:
				#LOG.debug('Increment left')
				#diff_time = abs((datetime.strptime(first_sample_in_time[str(line['name'])], '%Y-%m-%dT%H:%M:%S') - start_time).seconds)
				#LOG.debug('LEFT INCREMENT (%s) ---> First_sample: %s Start_time: %s    DIFF in seconds: %s', str(line['name']), datetime.strptime(first_sample_in_time[str(line['name'])], '%Y-%m-%dT%H:%M:%S'), start_time, diff_time)

				null_point_time = start_time.strftime("%Y-%m-%dT%H:%M:%S")
				line['data'].insert(0,{'x': null_point_time, 'y': None })

			if int(len(samples) / 2) > samples_after_event[str(line['name'])]:
				#LOG.debug('Increment right')
				#diff_time = abs((end_time - datetime.strptime(last_sample_in_time[str(line['name'])], '%Y-%m-%dT%H:%M:%S')).seconds)
				#LOG.debug('RIGHT INCREMENT (%s) ---> Last_sample: %s End_time: %s    DIFF in seconds: %s', str(line['name']), datetime.strptime(last_sample_in_time[str(line['name'])], '%Y-%m-%dT%H:%M:%S'), end_time, diff_time)

				null_point_time = end_time.strftime("%Y-%m-%dT%H:%M:%S")
				line['data'].append({'x': null_point_time, 'y': None })

		series.append(line)

        return series




    def get(self, request, *args, **kwargs):

	#This method takes all the information read from the html page and retrieves samples vm by vm and concatenate them to plot the lines
	samples = ""
	part_samples = ""
	metric = ""
	dict_id_name = {}
	event_time = ""
	flag_metric = "False"
	start_time = 0
	end_time = 0

	#LOG.debug('Request %s', request)

	offset_time = request.GET.get('offset_time', None)
	vms_selected_list = request.GET.get('vms_selected_list', None)
	event_type = request.GET.get('stackevent_types', None)
	LOG.debug('VMS_SELECTED_LIST: %s  EVENT_TYPE: %s', vms_selected_list, event_type)


	if vms_selected_list != None and vms_selected_list != "":

		samples_number = request.GET.get('samples_number', None)
		delta_t = request.GET.get('delta_t', None)
		half_window_size = int( int(samples_number) * int(delta_t) / 2 )

		timestamp = request.GET.get('timestamp', None)
		event_time = timestamp[:10]+' '+timestamp[11:19]
		tmp_time = datetime.strptime(event_time, '%Y-%m-%d %H:%M:%S')

		start_time = tmp_time - timedelta(seconds=half_window_size)
		end_time = tmp_time + timedelta(seconds=half_window_size)

		#LOG.debug('COMPLEX: %s \n START: %s \n   END: %s', search_time, start_time, end_time)
		vms_vector = vms_selected_list.split('&')


		for vm in vms_vector:
			LOG.debug('VM: %s', vm)
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
		
			#Query FROM
			query += [{
				"field": "timestamp",
				"op": "gt",
				"value": start_time}]


			#Query TO
			query += [{
				"field": "timestamp",
				"op": "lt",
				"value": end_time}]


			#In this panel it is not necessary to limit the number of samples retrieved from mongo because they are limited by the "time window" itself. We retrieve samples for each vm separately and then concatenate them to get all the samples to plot 
			part_samples = ceilometer.sample_list(request, metric, query)

			if samples == "":
				samples = part_samples
			else:
				samples += part_samples

		LOG.debug('len(samples): %s', len(samples))

	series = self._series_for_meter(samples, dict_id_name, event_type, event_time, offset_time, start_time, end_time)

	dict_id_name = {}
        ret = {}
        ret['series'] = series
        ret['settings'] = {}
	
        return HttpResponse(json.dumps(ret),
            mimetype='application/json')
	
