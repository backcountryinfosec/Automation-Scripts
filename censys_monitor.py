import censys.certificates
import json
import requests
import os
import random

#UID = ""
#SECRET = ""


#api for remynseit and remynse
UIDS = ["UID1", "UID2", "UID3"]
SECRETS = {"secret": "value", "secret2": "value2"}

'''
Search
(utah.edu.*) AND NOT parsed.subject_dn.raw:/.*utah.edu/
'''

alert_webhook = ''
known_certs = []


def getCerts():
    UID = random.choice(UIDS)
    SECRET = SECRETS[UID]
    c = censys.certificates.CensysCertificates(UID, SECRET)
    certs = c.search("(utah.edu.* OR utahedu.*) AND NOT parsed.subject_dn.raw:/.*utah.edu/")
    return certs


def knownCerts():
    known_certs = []
    if os.path.isfile('/opt/censys/certs.txt'):
        with open('/opt/censys/certs.txt') as f:
            for line in f:
                known_certs.append(line.rstrip())
            return known_certs
    else:
        pass
def alert(cert):
    text = f"New SSL Cert Detected:\n Sha256: {cert['parsed.fingerprint_sha256']}\n SubjectCN: {cert['parsed.subject_dn']}"
    message = {"text": text}
    resp = requests.post(alert_webhook, data=json.dumps(message), headers={'Content-Type': 'application/json'})
    if resp.status_code != 200:
        raise ValueError(f'Status Code: {resp.status_code}, Error: {resp.text}')

def main():
    known_certs = knownCerts()
    new_certs = getCerts()
    for i in new_certs:
        if known_certs:
            if i['parsed.fingerprint_sha256'] in known_certs:
                pass
            else:
                alert(i)
                print("Found New Cert")
                with open('/opt/censys/certs.txt', 'a+') as f:
                    f.write(i['parsed.fingerprint_sha256'] + "\r\n")
        else:
            print("First Run, adding certs and alerting")
            alert(i)
            with open('/opt/censys/certs.txt', 'a+') as f:
                f.write(i['parsed.fingerprint_sha256'] + "\r\n")


if __name__ == "__main__":
    main()
