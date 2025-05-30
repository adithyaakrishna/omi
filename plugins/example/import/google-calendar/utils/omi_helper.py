import os
import requests
from typing import Dict, Any

class OMIClient:
    def __init__(self):
        self.app_id = os.getenv('OMI_APP_ID')
        self.api_key = os.getenv('OMI_API_KEY')
        self.api_url = f"https://api.omi.me/v2/integrations/{self.app_id}/user/facts"
    
    def submit_memory(self, user_id: str, memory: str) -> Dict[str, Any]:
        """Submit a single memory to OMI"""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        memory_data = {
            "text": memory,
            "text_source": "google_calendar",
            "text_source_spec": "event"
        }
        
        response = requests.post(
            f"{self.api_url}?uid={user_id}",
            headers=headers,
            json=memory_data
        )
        
        return {
            "memory": memory,
            "success": response.status_code == 200,
            "status_code": response.status_code,
            "response": response.json() if response.status_code == 200 else response.text
        }
