import json
import os
from http.client import responses
from typing import List

import requests

from src.docker_client import TempCacheDir
from src.lib.tc_api_client import tc_api_version, TCApiClient


def json_file_cache(fname):
    def decorator(function):
        def wrapper(*args, **kwargs):
            temp_path = TempCacheDir().tmp_path
            full_fname = os.path.join(temp_path, fname)
            # getting job_id as a cache key
            rec_id = f"{args[1]}"
            old_cache = {}
            if os.path.isfile(full_fname):
                with open(full_fname, 'r') as f:
                    try:
                        old_cache = json.load(f)
                    except json.decoder.JSONDecodeError:
                        old_cache = {}
                    cached = old_cache.get(rec_id, None)
                    if cached:
                        return cached

            with open(full_fname, 'w') as f:
                ret = function(*args, **kwargs)
                old_cache[rec_id] = ret
                json.dump(old_cache, f)
                return ret
        return wrapper
    return decorator


class TCApiClientJobs(TCApiClient):
    def get_jobs_public(self) -> dict:
        headers = {**self._headers, **{
            'X-Tableau-Auth': self.session_token
        }}
        r = requests.get(f"{self.tc_pod_url}/api/{tc_api_version}/sites/{self.site_luid}/jobs", headers=headers)
        status_text = f"{responses[r.status_code]}"
        if r.status_code != 200:
            raise Exception(f"unable to get jobs. {status_text}, {r.content}")

        response = json.loads(r.content)
        return response

    def get_jobs_sorted(self, site_id):
        """
        get jobs from Tableau Cloud Private api
        """
        body = {
            "method": "getBackgroundJobs",
            "params": {"filter":
                {"operator": "and",
                 "clauses": [
                    {"operator": "in", "field": "taskType", "values":
                        [   "Extract",
                            "Flow",
                            "PredictiveModelFlow",
                            "Subscription",
                            "Encryption",
                            "Bridge",
                            "Acceleration"]},
                    {"operator": "eq", "field": "siteId", "value": site_id}
                ]},
               "order": [{"field": "jobRequestedTime", "ascending": False}],
               "page": {"startIndex": 0, "maxItems": 250}}
        }
        return self._post_private("/vizportal/api/web/v1/getBackgroundJobs", body)

    @json_file_cache("jobs_cache.json")
    def get_job_detail(self, job_id):
        """
        get job detail from Tableau Cloud Private api
        """
        body = {
            "method": "getBackgroundJobExtendedInfo",
            "params": {
                "backgroundJobId": job_id}
        }
        return self._post_private("/vizportal/api/web/v1/getBackgroundJobExtendedInfo", body)

    def start_tasks(self, task_ids: List[str]):
        body = {
            "method": "runExtractTasks",
            "params": {
                "ids": task_ids}
        }
        return self._post_private("/vizportal/api/web/v1/runExtractTasks", body)

    def get_tasks(self, site_id):
        body = {
            "method": "getExtractTasks",
            "params": {
                    "filter": {
                      "operator": "and",
                      "clauses": [
                        {
                          "operator": "eq",
                          "field": "siteId",
                          "value": site_id
                        }
                      ]
                    },
            },
            "order": [
                      {
                        "field": "targetName",
                        "ascending": True
                      }
                    ],
            "page": {
              "startIndex": 0,
              "maxItems": 10
            }
        }
        tasks_result = self._post_private("/vizportal/api/web/v1/getExtractTasks", body)
        tasks = tasks_result.get("result", {}).get("tasks", [])
        datasources = tasks_result.get("result", {}).get("datasources", [])
        for task in tasks:
            target_id = task["targetId"]
            matching_datasources = [ds for ds in datasources if ds["id"] == target_id]
            if matching_datasources:
                task["datasource_name"] = matching_datasources[0]["name"]
            else:
                task["datasource_name"] = "Unknown"
        return tasks_result
