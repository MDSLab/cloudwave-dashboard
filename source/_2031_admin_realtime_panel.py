# The slug of the panel to be added to HORIZON_CONFIG. Required.
PANEL = 'realtime_CW_phy'
# The slug of the dashboard the PANEL associated with. Required.
PANEL_DASHBOARD = 'admin'
# The slug of the panel group the PANEL is associated with.
PANEL_GROUP = 'admin'

# Python panel class of the PANEL to be added.
ADD_PANEL = 'openstack_dashboard.dashboards.admin.realtime_CW_phy.panel.RealtimeCloudWavePhysical'
