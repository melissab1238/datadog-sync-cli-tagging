import re
from concurrent.futures import ThreadPoolExecutor, wait

from requests.exceptions import HTTPError

from datadog_sync.utils.base_resource import BaseResource


RESOURCE_TYPE = "synthetics_private_locations"
EXCLUDED_ATTRIBUTES = [
    "root['id']",
    "root['modifiedAt']",
    "root['createdAt']",
    "root['metadata']",
    "root['secrets']",
    "root['config']",
]
BASE_LOCATIONS_PATH = "/api/v1/synthetics/locations"
BASE_PATH = "/api/v1/synthetics/private-locations"
PL_ID_REGEX = re.compile("^pl:.*")


class SyntheticsPrivateLocations(BaseResource):
    resource_type = "synthetics_private_locations"

    source_resources = {}
    destination_resources = {}

    def __init__(self, config):
        super().__init__(
            config,
            RESOURCE_TYPE,
            BASE_PATH,
            excluded_attributes=EXCLUDED_ATTRIBUTES,
        )

    def import_resources(self):
        source_client = self.config.source_client

        try:
            resp = source_client.get(BASE_LOCATIONS_PATH).json()
        except HTTPError as e:
            self.logger.error("error importing synthetics_private_locations: %s", e)
            return

        self.import_resources_concurrently(resp["locations"])

    def process_resource_import(self, synthetics_private_location):
        source_client = self.config.source_client
        if PL_ID_REGEX.match(synthetics_private_location["id"]):
            try:
                pl = source_client.get(self.base_path + f"/{synthetics_private_location['id']}").json()
            except HTTPError as e:
                self.logger.error(
                    "error getting synthetics_private_location %s: %s",
                    synthetics_private_location["id"],
                    e.response.text,
                )
                return
            self.source_resources[synthetics_private_location["id"]] = pl

    def apply_resources(self):
        self.open_resources()
        connection_resource_obj = self.get_connection_resources()
        self.apply_resources_concurrently(self.source_resources, connection_resource_obj)

    def prepare_resource_and_apply(self, _id, synthetics_private_location, connection_resource_obj=None):
        if self.resource_connections:
            self.connect_resources(synthetics_private_location, connection_resource_obj)

        if _id in self.destination_resources:
            self.update_resource(_id, synthetics_private_location)
        else:
            self.create_resource(_id, synthetics_private_location)

    def create_resource(self, _id, synthetics_private_location):
        destination_client = self.config.destination_client
        self.remove_excluded_attr(synthetics_private_location)

        try:
            resp = destination_client.post(self.base_path, synthetics_private_location).json()["private_location"]
        except HTTPError as e:
            self.logger.error("error creating synthetics_private_location: %s", e.response.text)
            return
        self.destination_resources[_id] = resp

    def update_resource(self, _id, synthetics_private_location):
        destination_client = self.config.destination_client
        self.remove_excluded_attr(synthetics_private_location)

        diff = self.check_diff(synthetics_private_location, self.destination_resources[_id])
        if diff:
            try:
                resp = destination_client.put(
                    self.base_path + f"/{self.destination_resources[_id]['id']}", synthetics_private_location
                ).json()
            except HTTPError as e:
                self.logger.error("error creating synthetics_private_location: %s", e.response.text)
                return
            self.destination_resources[_id].update(resp)
