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

import horizon
from openstack_dashboard.dashboards.admin import dashboard


class Event_CW(horizon.Panel):
    name = _("CW Events")
    slug = 'event_CW'
    permissions = ('openstack.services.metering', 'openstack.roles.admin', )


dashboard.Admin.register(Event_CW)
