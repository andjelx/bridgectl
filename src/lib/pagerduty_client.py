import requests


class PagerDutyClient:
    def __init__(self, service_key):
        self.service_key = service_key #= os.getenv('pager_duty_routing_key')

    def has_service_key(self):
        return bool(self.service_key)

    def trigger_pagerduty_alert(self, incident_title, incident_details):
        url = "https://events.pagerduty.com/v2/enqueue"
        headers = {
            'Content-Type': 'application/json',
        }
        payload = {
            "routing_key": self.service_key,
            "event_action": "trigger",
            "payload": {
                "summary": incident_title,
                "source": "bridgectl",  # Customize this as per your source tool
                "severity": "error",  # Can be 'info', 'warning', 'error', or 'critical'
                "custom_details": incident_details
            }
        }

        response = requests.post(url, json=payload, headers=headers)
        if response.status_code == 202:
            print("Alert triggered successfully in PagerDuty.")
        else:
            print(f"Failed to trigger alert: {response.text}")
