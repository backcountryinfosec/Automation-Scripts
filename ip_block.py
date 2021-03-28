
from json import loads
from kafka import KafkaConsumer
import subprocess
from ipwhois import IPWhois
from pymisp import PyMISP


misp_url = ""
misp_api_key = ""
misp_verifycert = True
misp_ipblacklist_event = 3


def init(misp_url, misp_api_key):
    #return PyMISP(misp_url, misp_api_key, True, 'json')
    return PyMISP(misp_url, misp_api_key, True, False)

def ipLookup(ip):
    obj = IPWhois(ip)
    res = obj.lookup_whois()
    country = res["nets"][0]['country']
    description = res["nets"][0]['description']
    if description is None:
        description="None"
    return country, description

while True:
    consumer = KafkaConsumer(
        'elastalert-alert',
        bootstrap_servers=['kafka_host:9092'],
        auto_offset_reset='earliest',
        enable_auto_commit=True,
        group_id='python_kafka_consumer_v2',
        value_deserializer=lambda x: loads(x.decode('utf-8'))
    )
    for message in consumer:
        message = message.value
        sourceip = message['sourceip']
        country, description = ipLookup(sourceip)
        if 'Verizon' in description and country == 'US':
            print("IP Was Verizon")
            pass
        else:
            print(f"IP was from {country} and carrier was {description}")
            subprocess.check_output(f"ssh root@10.0.2.1 easyrule block wan {sourceip}; 0; exit 0", stderr=subprocess.STDOUT, shell=True)
            misp = init(misp_url, misp_api_key)
            try:
                event = misp.add_attribute(misp_ipblacklist_event, {'type': 'ip-src', 'value': sourceip, 'comment': 'IP Seen Portscanning', 'Tag': 'tlp:green'}, pythonify=True)
                print(event)
                misp.tag(event['uuid'], 'tlp:green')
                misp.tag(event['uuid'], 'osint:source-type=\"automatic-collection\"')
            except:
                print("IP Already To Misp")
