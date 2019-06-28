import requests
from getpass import getpass


resp = requests.get('https://edms.cern.ch/ws/api/rest/helloWorld',auth=('jsirvent@cern.ch', 'Thor2401'))
#resp = requests.get('https://api.github.com')

print(resp.status_code)
print(resp.headers)
print(resp.text)

#if resp.status_code != 200:
#    # This means something went wrong.
#    raise ApiError('GET /tasks/ {}'.format(resp.status_code))

#print('{}'.format(resp.json()))

#for todo_item in resp.json():
#    print('{} {}'.format(todo_item['id'], todo_item['summary']))