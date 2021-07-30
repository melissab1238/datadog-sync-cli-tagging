# Unless explicitly stated otherwise all files in this repository are licensed
# under the 3-clause BSD style license (see LICENSE).
# This product includes software developed at Datadog (https://www.datadoghq.com/).
# Copyright 2019 Datadog, Inc.

import re

from requests.exceptions import HTTPError
from typing import List, Dict, Optional

from datadog_sync.utils.base_resource import BaseResource, ResourceConfig
from datadog_sync.utils.custom_client import CustomClient


class SyntheticsPrivateLocations(BaseResource):
    resource_type = "synthetics_private_locations"
    resource_config = ResourceConfig(
        base_path="/api/v1/synthetics/private-locations",
        excluded_attributes=[
            "root['id']",
            "root['modifiedAt']",
            "root['createdAt']",
            "root['metadata']",
            "root['secrets']",
            "root['config']",
        ],
    )
    # Additional SyntheticsPrivateLocations specific attributes
    base_locations_path = "/api/v1/synthetics/locations"
    pl_id_regex = re.compile("^pl:.*")

    def get_resources(self, client: CustomClient) -> List[Dict]:
        try:
            resp = client.get(self.base_locations_path).json()
        except HTTPError as e:
            self.config.logger.error("error importing synthetics_private_locations: %s", e)
            return []

        return resp["locations"]

    def import_resource(self, resource: Dict) -> None:
        source_client = self.config.source_client
        if self.pl_id_regex.match(resource["id"]):
            try:
                pl = source_client.get(self.resource_config.base_path + f"/{resource['id']}").json()
            except HTTPError as e:
                self.config.logger.error(
                    "error getting synthetics_private_location %s: %s",
                    resource["id"],
                    e.response.text,
                )
                return None
            self.resource_config.source_resources[resource["id"]] = pl

    def pre_resource_action_hook(self, resource: Dict) -> None:
        pass

    def pre_apply_hook(self, resources: Dict[str, Dict]) -> Optional[list]:
        pass

    def create_resource(self, _id: str, resource: Dict) -> None:
        destination_client = self.config.destination_client

        try:
            resp = destination_client.post(self.resource_config.base_path, resource).json()["private_location"]
        except HTTPError as e:
            self.config.logger.error("error creating synthetics_private_location: %s", e.response.text)
            return
        self.resource_config.destination_resources[_id] = resp

    def update_resource(self, _id: str, resource: Dict) -> None:
        destination_client = self.config.destination_client

        try:
            resp = destination_client.put(
                self.resource_config.base_path + f"/{self.resource_config.destination_resources[_id]['id']}", resource
            ).json()
        except HTTPError as e:
            self.config.logger.error("error creating synthetics_private_location: %s", e.response.text)
            return
        self.resource_config.destination_resources[_id].update(resp)

    def connect_id(self, key: str, r_obj: Dict, resource_to_connect: str) -> None:
        super(SyntheticsPrivateLocations, self).connect_id(key, r_obj, resource_to_connect)
