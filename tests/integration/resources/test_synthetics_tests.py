# Unless explicitly stated otherwise all files in this repository are licensed
# under the 3-clause BSD style license (see LICENSE).
# This product includes software developed at Datadog (https://www.datadoghq.com/).
# Copyright 2019 Datadog, Inc.

from datadog_sync.models import SyntheticsTests
from tests.integration.helpers import BaseResourcesTestClass


class TestSyntheticsTestsResources(BaseResourcesTestClass):
    resource_type = SyntheticsTests.resource_type
    field_to_update = "message"
