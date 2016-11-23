#!/bin/bash


#Backupping the old version of local_settings
DATE=$(date +'%d-%m-%Y')
cp /etc/openstack-dashboard/local_settings /etc/openstack-dashboard/local_settings_$DATE

#Inserting formatter
cwstr="'formatters': {"
cwvar=`cat /etc/openstack-dashboard/local_settings | grep formatters`
if [[ $cwvar == *"$cwstr"* ]]; then
        echo -e "\t\t local_settings: Formatter already added!"
else
        text_formatter="    'disable_existing_loggers': False,\n    'formatters': {\n        'verbose': {\n            'format': '%(asctime)s %(process)d %(levelname)s %(name)s '\n                      '%(message)s'\n        },\n    },"

        sed -i "s/    'disable_existing_loggers': False,/$text_formatter/g" /etc/openstack-dashboard/local_settings
        echo -e "\t\t local_settings: Formatter just added!"
fi

#Inserting file handler
cwstr="'file': {"
cwvar=`cat /etc/openstack-dashboard/local_settings | grep "'file': {"`
if [[ $cwvar == *"$cwstr"* ]]; then
        echo -e "\t\t local_settings: File Handler already added!"
else
        text_console="        'console': {"
        text_handler="        'file': {\n            'level': 'DEBUG',\n            'class': 'logging.FileHandler',\n            'filename': '\/var\/log\/horizon\/horizon.log',\n            'formatter': 'verbose',\n        },\n        'console': {"

        sed -i "s/$text_console/$text_handler/g" /etc/openstack-dashboard/local_settings
        echo -e "\t\t local_settings: File Handler just added!"
fi

#Inserting file handlers into horizon and openstack_dashboard loggers
num=`sed -n "/#'handlers': \['console'\],/p" /etc/openstack-dashboard/local_settings | wc -l`

if [[ $num == 2 ]]; then
        echo -e "\t\t local_settings: Horizon and openstack_dashboard handlers already added!\n"
else
        sed -i "/        'horizon':.*/{n;s/.*/            #'handlers': ['console'],\n            'handlers': ['file'],/}" /etc/openstack-dashboard/local_settings


        sed -i "/        'openstack_dashboard':.*/{n;s/.*/            #'handlers': ['console'],\n            'handlers': ['file'],/}" /etc/openstack-dashboard/local_settings

        echo -e "\t\t local_settings: Horizon and openstack_dashboard handlers just added!\n"
fi
