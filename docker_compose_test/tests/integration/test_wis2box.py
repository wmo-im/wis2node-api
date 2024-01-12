###############################################################################
#
# Licensed to the Apache Software Foundation (ASF) under one
# or more contributor license agreements.  See the NOTICE file
# distributed with this work for additional information
# regarding copyright ownership.  The ASF licenses this file
# to you under the Apache License, Version 2.0 (the
# 'License'); you may not use this file except in compliance
# with the License.  You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# 'AS IS' BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.
#
###############################################################################

# integration tests assume that the workflow in
# .github/workflows/wis2box_test.yml has been executed

import json
import time
import requests
import os

import paho.mqtt.client as mqtt

URL = 'http://localhost:4343'
API_URL = f'{URL}/oapi'


def store_message(message, channel):
    """store message in current directory with filename

    :param message: received message
    :param filename: filename
    """
    # decode message payload as json
    message = json.loads(message.payload.decode())
    # if message matches channel store it
    if message['channel'] == channel:
        filename = message['channel'].replace('/', '_') + '.json'
        # store message in current directory with filename
        with open(filename, 'w') as f:
            json.dump(message, f, indent=4)
    else:
        print(f'channel {message["channel"]} does not match {channel}')


def transform_to_bufr(process_name: str, data: str, expected_response: dict):
    """Transform data to bufr

    :param process_name: name of the process
    :param data: data to be transformed
    :param expected_response: expected response

    """

    url = f'{API_URL}/processes/{process_name}/execution'

    headers = {
        'accept': 'application/json',
        'Content-Type': 'application/json'
    }

    response = requests.post(url, headers=headers, json=data)

    assert response.status_code == 200

    response_json = response.json()

    # assert response_json['result'] == expected_response['result']
    assert response_json['messages transformed'] == expected_response['messages transformed'] # noqa
    assert response_json['messages published'] == expected_response['messages published'] # noqa
    assert response_json['errors'] == expected_response['errors']
    # assert response_json['warnings'] == expected_response['warnings']

    # wait for the message to be received
    time.sleep(1)

    filename = data['inputs']['channel'].replace('/', '_') + '.json'

    # check that the file has been created
    try:
        # open the received message
        with open(filename) as f:
            message = json.load(f)
    except Exception as e:
        assert False, f'Error opening file: {e}'

    # rm the file
    os.remove(filename)

    # create the expected message
    expected_message = {
        'EventName': 'wis2box:DataPublishRequest',
        'channel': expected_response['data_items'][0]['channel'],
        'filename': expected_response['data_items'][0]['filename'],
        'data': expected_response['data_items'][0]['data'],
        'meta': expected_response['data_items'][0]['meta']
    }

    # compare the received message with the expected message
    assert message['EventName'] == expected_message['EventName']
    assert message['channel'] == expected_message['channel']
    assert message['filename'] == expected_message['filename']
    assert message['data'] == expected_message['data']
    assert message['meta'] == expected_message['meta']


def test_synop2bufr():
    """Test synop2bufr"""

    process_name = 'wis2box-synop2bufr'
    data = {
        'inputs': {
            'channel': 'synop/test',
            'year': 2023,
            'month': 1,
            'notify': True,
            'data': 'AAXX 19064 64400 36/// /0000 10102 20072 30068 40182 53001 333 20056 91003 555 10302 91018=' # noqa
        }
    }
    expected_response = {
        'result': 'success',
        'messages transformed': 1,
        'messages published': 1,
        'data_items': [
            {
                'data': 'QlVGUgABgAQAABYAAAAAAAAAAAJuHgAH5wETBgAAAAALAAABgMGWx2AAAVMABOIAAANjQ0MDAAAAAAAAAAAAAAAIDIGxoaGBgAAAAAAAAAAAAAAAAAAAAPzimYBA/78kmTlBBUCDB///////////////////////////+dUnxn1P///////////26vbYOl////////////////////////////////////////////////////////////////AR////gJH///+T/x/+R/yf////////////7///v9f/////////////////////////////////+J/b/gAff2/4Dz/X/////////////////////////////////////7+kAH//v6QANnH//////AAf/wAF+j//////////////v0f//////f//+/R/+////////////////////fo//////////////////3+oAP///////////////////8A3Nzc3', # noqa
                'filename': 'WIGOS_0-20000-0-64400_20230119T060000.bufr4',
                'meta': {
                    'id': 'WIGOS_0-20000-0-64400_20230119T060000',
                    'wigos_station_identifier': '0-20000-0-64400',
                    'data_date': '2023-01-19T06:00:00',
                    'geometry': {
                        'type': 'Point',
                        'coordinates': [11.8817, -4.8045]
                    }
                },
                'channel': 'synop/test'
            }
        ],
        'errors': [],
        'warnings': []
    }
    # start mqtt client
    client = mqtt.Client('wis2box-synop2bufr')
    # user credentials wis2box:wis2box
    client.username_pw_set('wis2box', 'wis2box')
    # connect to the broker
    client.connect('localhost', 5883, 60)
    # subscribe to the topic
    client.subscribe('wis2box/#')
    # define callback function for received messages
    client.on_message = lambda client, userdata, message: store_message(message, channel='synop/test') # noqa
    # start the loop
    client.loop_start()
    transform_to_bufr(process_name, data, expected_response)
    # stop the loop
    client.loop_stop()
    # disconnect from the broker
    client.disconnect()


def test_csv2bufr():
    """Test csv2bufr"""

    process_name = 'wis2box-csv2bufr'
    data = {
        'inputs': {
            'data': 'wsi_series,wsi_issuer,wsi_issue_number,wsi_local,wmo_block_number,wmo_station_number,station_type,year,month,day,hour,minute,latitude,longitude,station_height_above_msl,barometer_height_above_msl,station_pressure,msl_pressure,geopotential_height,thermometer_height,air_temperature,dewpoint_temperature,relative_humidity,method_of_ground_state_measurement,ground_state,method_of_snow_depth_measurement,snow_depth,precipitation_intensity,anemometer_height,time_period_of_wind,wind_direction,wind_speed,maximum_wind_gust_direction_10_minutes,maximum_wind_gust_speed_10_minutes,maximum_wind_gust_direction_1_hour,maximum_wind_gust_speed_1_hour,maximum_wind_gust_direction_3_hours,maximum_wind_gust_speed_3_hours,rain_sensor_height,total_precipitation_1_hour,total_precipitation_3_hours,total_precipitation_6_hours,total_precipitation_12_hours,total_precipitation_24_hours\n0,20000,0,15015,15,15,1,2022,3,31,0,0,47.77706163,23.94046026,503,504.43,100940,20104,1448,5,298.15,294.55,80.4,3,1,1,0,0.004,10,-10,30,3,30,5,40,9,20,11,2,4.7,5.3,7.9,9.5,11.4', # noqa
            'channel': 'csv/test',
            'notify': True,
            'template': 'aws-template'
        }
    }
    expected_response = {
        'result': 'partial success',
        'messages transformed': 1,
        'messages published': 1,
        'data_items': [
            {
                'data': 'QlVGUgABgAQAABYAAAAAAAAAAAJuHgAH5gMfAAAAAAALAAABgMGWx2AAAVMABOIAAAMTUwMTUAAAAAAAAAAAAAAB4H//////////////////////////+vzG+ABpHZUm5gfCNGEap///////////////////////////+du////////+CZAB9P/3R3cw+h////////////////////////////////////////////////8wiAAX//////////Af////gP////////////////////////////////////+AyP//////////////////////////+J/YPAPff2DwGT4goBadMCgN3//////////////////////////////////////////A+j/f/AMH/QDZ/oBQf0AYH6AHP////////////////////////////////////////////////////////////////////////////////////8A3Nzc3', # noqa
                'filename': 'WIGOS_0-20000-0-15015_20220331T000000.bufr4',
                'meta': {
                    'id': 'WIGOS_0-20000-0-15015_20220331T000000',
                    'wigos_station_identifier': '0-20000-0-15015',
                    'data_date': '2022-03-31T00:00:00',
                    'geometry': {
                        'type': 'Point',
                        'coordinates': [23.94046026, 47.77706163]
                    }
                    },
                'channel': 'csv/test'
            }
        ],
        'errors': [],
        'warnings': [
            '#1#pressureReducedToMeanSeaLevel: Value (20104.0) out of valid range (50000 - 150000).; Element set to missing' # noqa
        ]
    }

    # start mqtt client
    client = mqtt.Client('wis2box-csv2bufr')
    # user credentials wis2box:wis2box
    client.username_pw_set('wis2box', 'wis2box')
    # connect to the broker
    client.connect('localhost', 5883, 60)
    # subscribe to the topic
    client.subscribe('wis2box/#')
    # define callback function for received messages
    client.on_message = lambda client, userdata, message: store_message(message, channel='csv/test') # noqa
    # start the loop
    client.loop_start()
    # transform bufr message
    transform_to_bufr(process_name, data, expected_response)
    # stop the loop
    client.loop_stop()
    # disconnect from the broker
    client.disconnect()