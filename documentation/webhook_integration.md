Webhook Integration Guide
Endpoint Details
URL: http://172.16.234.39/sigfox
Methods: GET, POST
Required Parameters:
name: Display identifier (wc, bathroom, eva)
duration: Time in seconds
Example Requests
GET Request
curl "http://172.16.234.39/sigfox?name=wc&duration=60"

POST Request
curl -X POST -H "Content-Type: application/json" \
     -d '{"name":"wc","duration":"60"}' \
     http://172.16.234.39/sigfox


Response Codes
200: Success
400: Invalid parameters
500: Server error
Display Names
WC: "wc"
Bathroom: "bathroom"
Eva: "eva"