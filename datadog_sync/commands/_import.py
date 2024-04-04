# Unless explicitly stated otherwise all files in this repository are licensed
# under the 3-clause BSD style license (see LICENSE).
# This product includes software developed at Datadog (https://www.datadoghq.com/).
# Copyright 2019 Datadog, Inc.

import asyncio

from click import command

from datadog_sync.constants import Command
from datadog_sync.commands.shared.options import common_options, source_auth_options
from datadog_sync.utils.resources_handler import run_cmd_async


@command(Command.IMPORT.value, short_help="Import Datadog resources.")
@source_auth_options
@common_options
def _import(**kwargs):
    """Import Datadog resources."""
    asyncio.run(run_cmd_async(Command.IMPORT, **kwargs))
