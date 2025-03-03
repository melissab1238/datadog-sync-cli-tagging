# datadog-sync-cli
Datadog cli tool to sync resources across organizations.

## FindLaw Transition [Melissa's addition]
This repo is a fork of the `datadog-sync-cli` Datadog repo along with additional Python scripting to help with tagging changes between two Datadog organizations. The added files are `do_all_changes.py` as well as everything in the `transition_tagging` folder.

Context: In December 2024, [FindLaw](findlaw.com) was sold from Thomson Reuters (TR) to Internet Brands (IB). I was tasked with transitioning FindLaw's Datadog resources (e.g. monitors, synthetic tests) from our TR-managed Datadog (DD) accounts to our IB-managed DD account.

I wrote Python code to aid in the conversion of values in the JSON files that were imported from the CLI tool. My tool works like a CLI with the ability to filter based on a specific tag and converts JSON files differently based on resource type (monitors, dashboards, synthetic tests). This code can be modified for other developers looking to transfer resources between Datadog accounts and needing to modify tagging along the way.

Impact: My code reduced manual conversion of over 2,000 resources and a dozen tags, saving over at least 80 hours of work. All of the resources were transferred within a week.

### The custom python script
The helper functions and tests are in `transition_tagging/` with the main function `do_tagging_changes` in `tagging_changes.py`.

What the script does:

- adds `business_unit:findlaw` tag
- adds `team:findlaw` tag
- changes `env:findlaw-xxx` to `env:xxx` where `xxx` is env ("prod", "stage", etc.), also changes `env: findlaw-xxx` to `env:xxx`
- changes and removes `env:findlaw-ci` to `env:dev` (removes instances of ci)
- prints resources that do not have an asset insight id. These need a manual addition of asset id (`findlaw-asset-id`)
- renames `tr_application-asset-insight-id` tag with `findlaw-asset-id`. These are unique IDs associated with TR services
- removes accidental `a` in asset id. (e.g. `findlaw-asset-id:xxxxx` > `findlaw-asset-id:xxxxx`)
- removes any accidental tags like "business" and "busines" which were added to some synthetic tests (in findlaw DD account) by accident
- removes duplicate `managed_by:datadog-sync` tags
- Ignores resources made by terraform (`created_by:terraform`) as these resources will be moved via Terraform.
- swaps private location values
- swaps global variable ids
- for smoketests (tag `smoketest`), removes extraneous tag `test_type:smoketest`

## Usage

### Step 0: Setup constants.py file
The constants file (`transition_tagging/constants.py`) should be modified to according to the changes in private locations and (synthetic) global variables in your organization.

### Step 1: Setup Config file
In `config.txt`, the query from the source (e.g. legal-np) DD account is configured.

Example `config.txt` file
```
# config

destination_api_url="https://api.datadoghq.com"
destination_api_key="<API_KEY>"
destination_app_key="<APP_KEY>"
source_api_key="<API_KEY>"
source_app_key="<APP_KEY>"
source_api_url="https://api.datadoghq.com"
resources="synthetics_tests"
# filter=["Type=Dashboards;Name=title;Value=Test screenboard", "Type=Monitors;Name=tags;Value=sync:true"]
```
Where destination would be a TR-managed DD account, and the source would be the IB-managed Avvo DD account.

### Step 2: Run dd sync cli _import_ command
Run

`datadog-sync import --config config.txt --verify-ddr-status false`.

This command will import the resources requested in the `config.txt` file into json files inside of `resources/source/`.

### Step 3: Clean up tags with Python script
For cleaning up tags between accounts, run

`python3 do_all_changes.py`.

This updates the files (just `synthetic_tests.json` for now) in `resources/source/` with the correct future tagging and cleanup needed for resources in Avvo's Datadog account.

### Step 4: Run dd sync cli _sync_ command
Run

`datadog-sync sync --config config.txt --verify-ddr-status false --skip-failed-resource-connections FALSE`

This command will push/export the resources requested in the `config.txt` file from the json files in `resources/source/` to the destination account. Additionally, the json files will be copied to `resources/destination/`.

Before running `sync`, you can optionally run `diffs` as a dry-run. `datadog-sync diffs --config config.txt --verify-ddr-status false --skip-failed-resource-connections FALSE`.

### Note
Please do not check in resource-specific json files to version control. See/edit `.gitignore`.

### Testing `tagging_changes.py`
Tests have been written using `Pytest`.
Run

`pytest transition_tagging/tests.py`

# Table of Contents
- [Quick Start](#quick-start)
- [Purpose](#purpose)
- [Installing](#installing)
  - [Installing from source](#installing-from-source)
  - [Installing from Releases](#installing-from-releases)
    - [MacOS and Linux](#macos-and-linux)
    - [Windows](#windows)
  - [Using docker and building the image](#using-docker-and-building-the-image)
- [Usage](#usage)
  - [API URL](#api-url)
  - [Filtering](#filtering)
    - [Top resources level filtering](#top-resources-level-filtering)
    - [Per resource level filtering](#per-resource-level-filtering)
      - [SubString and ExactMatch Deprecation](#substring-and-exactmatch-deprecation)
  - [Config file](#config-file)
  - [Cleanup flag](#cleanup-flag)
  - [Verify DDR Status Flag](#verify-ddr-status-flag)
  - [State Files](#state-files)
  - [Supported resources](#supported-resources)
- [Best practices](#best-practices)

## Quick Start

See [Installing](#installing) section for guides on how to install and setup the tool.

Run the `import` command to read the specified resources from the source organization and store them locally into JSON files in the directory `resources/source`.

Then, you can run the `sync` command which will use the stored files from previous `import` command (unless `--force-missing-dependencies` flag is passed) to create/modify the resources on the destination organization. The pushed resources are saved in the directory `resources/destination`.

The `migrate` command will run an `import` followed immediately by a `sync`.

The `reset` command will delete resources at the destination; however, by default it backs up those resources first and fails if it cannot. You can (but probably shouldn't) skip the backup by using the `--do-not-backup` flag.

*Note*: The tool uses the `resources` directory as the source of truth for determining what resources need to be created and modified. Hence, this directory should not be removed or corrupted.

**Example Usage**
```
# Import resources from parent organization and store them locally
$ datadog-sync import \
    --source-api-key="..." \
    --source-app-key="..." \
    --source-api-url="https://api.datadoghq.com"

> 2024-03-14 14:53:54,280 - INFO - Starting import...
> ...
> 2024-03-14 15:00:46,100 - INFO - Finished import

# Check diff output to see what resources will be created/modified
$ datadog-sync diffs \
    --destination-api-key="..." \
    --destination-app-key="..." \
    --destination-api-url="https://api.datadoghq.eu"

> 2024-03-14 15:46:22,014 - INFO - Starting diffs...
> ...
> 2024-03-14 14:51:15,379 - INFO - Finished diffs

# Sync the resources to the child organization from locally stored files and save the output locally
$ datadog-sync sync \
    --destination-api-key="..." \
    --destination-app-key="..." \
    --destination-api-url="https://api.datadoghq.eu"

> 2024-03-14 14:55:56,535 - INFO - Starting sync...
> ...
> 2024-03-14 14:56:00,797 - INFO - Finished sync: 1 successes, 0 errors
```

## Purpose

The purpose of the datadog-sync-cli package is to provide an easy way to sync Datadog resources across Datadog organizations.

***Note:*** this tool does not, nor is intended, for migrating intake data such as **ingested** logs, metrics, etc.

The source organization will not be modified, but the destination organization will have resources created and updated by the `sync` command.

## Installing

### Installing from source

***Note:***: Instlling from source requires Python >= v3.9

1) Clone the project repo and CD into the directory `git clone https://github.com/DataDog/datadog-sync-cli.git; cd datadog-sync-cli`
2) Install datadog-sync-cli tool using pip `pip install .`
3) Invoke the cli tool using `datadog-sync <command> <options>`

### Installing from Releases

#### MacOS and Linux

1) Download the executable from the [Releases page](https://github.com/DataDog/datadog-sync-cli/releases)
2) Provide the executable with executable permission `chmod +x datadog-sync-cli-{system-name}-{machine-type}`
3) Move the executable to your bin directory `sudo mv datadog-sync-cli-{system-name}-{machine-type} /usr/local/bin/datadog-sync`
4) Invoke the CLI tool using `datadog-sync <command> <options>`

#### Windows

1) Download the executable with extension `.exe` from the [Releases page](https://github.com/DataDog/datadog-sync-cli/releases)
2) Add the directory containing the `exe` file to your [path](https://learn.microsoft.com/en-us/windows-server/administration/windows-commands/path)
3) Invoke the CLI tool in cmd/powershell using the file name and omitting the extension: `datadog-sync-cli-windows-amd64 <command> <options>`

### Using docker and building the image
1) Clone the project repo and CD into the directory `git clone https://github.com/DataDog/datadog-sync-cli.git; cd datadog-sync-cli`
2) Build the provided Dockerfile `docker build . -t datadog-sync`
3) Run the Docker image using entrypoint below:
```
docker run --rm -v <PATH_TO_WORKING_DIR>:/datadog-sync:rw \
  -e DD_SOURCE_API_KEY=<DATADOG_API_KEY> \
  -e DD_SOURCE_APP_KEY=<DATADOG_APP_KEY> \
  -e DD_SOURCE_API_URL=<DATADOG_API_URL> \
  -e DD_DESTINATION_API_KEY=<DATADOG_API_KEY> \
  -e DD_DESTINATION_APP_KEY=<DATADOG_APP_KEY> \
  -e DD_DESTINATION_API_URL=<DATADOG_API_URL> \
  datadog-sync:latest <command> <options>
```

The `docker run` command mounts a specified `<PATH_TO_WORKING_DIR>` working directory to the container.


## Usage

#### API URL

Available URL's for the source and destination API URLs are:

- `https://api.datadoghq.com`
- `https://api.datadoghq.eu`
- `https://api.us5.datadoghq.com`
- `https://api.us3.datadoghq.com`
- `https://api.ddog-gov.com`
- `https://api.ap1.datadoghq.com`

For all available regions, see [Getting Started with Datadog Sites](https://docs.datadoghq.com/getting_started/site/).

#### Filtering

Filtering is done on two levels, at top resources level and per individual resource level using `--resources` and `--filter` respectively.

##### Top resources level filtering

By default all resources are imported, synced, etc. If you would like to perform actions on a specific top level resource, or subset of resources, use `--resources` option. For example, the command `datadog-sync import --resources="dashboard_lists,dashboards"` will import ALL dashboards and dashboard lists in your Datadog organization.

##### Per resource level filtering

Individual resources can be further filtered using the `--filter` flag. For example, the following command `datadog-sync import --resources="dashboards,dashboard_lists" --filter='Type=dashboard_lists;Name=name;Value=My custom list'`, will import ALL dashboards and ONLY dashboard lists with the `name` attribute equal to `My custom list`.

Filter option (`--filter`) accepts a string made up of `key=value` pairs separated by `;`.
```
--filter 'Type=<resource>;Name=<attribute_name>;Value=<attribute_value>;Operator=<operator>'
```
Available keys:

- `Type`: Resource such as Monitors, Dashboards, and more. [required]
- `Name`: Attribute key to filter on. This can be any attribute represented in dot notation (such as `attributes.user_count`). [required]
- `Value`: Regex to filter attribute value by. Note: special regex characters need to be escaped if filtering by raw string. [required]
- `Operator`: Available operators are below. All invalid operator's default to `ExactMatch`.
  - `Not`: Match not equal to `Value`.
  - `SubString` (*Deprecated*): Sub string matching. (This operator will be removed in future releases. See [SubString and ExactMatch Deprecation](#substring-and-exactmatch-deprecation)  section.)
  - `ExactMatch` (*Deprecated*): Exact string match. (This operator will be removed in future releases. See [SubString and ExactMatch Deprecation](#substring-and-exactmatch-deprecation)  section.)

By default, if multiple filters are passed for the same resource, `OR` logic is applied to the filters. This behavior can be adjusted using the `--filter-operator` option.

##### SubString and ExactMatch Deprecation

In future releases the `SubString` and `ExactMatch` Operator will be removed. This is because the `Value` key supports regex so both of these scenarios are covered by just writing the appropriate regex.  Below is an example:

Let's take the scenario where you would like to filter for monitors that have the `filter test` in the `name` attribute:

| Operator | Command |
| :-: | :-: |
| `SubString` | `--filter 'Type=monitors;Name=name;Value=filter test;Operator=SubString'` |
| Using `Value` | `--filter 'Type=monitors;Name=name;Value=.*filter test.*` |
| `ExactMatch` | `--filter 'Type=monitors;Name=name;Value=filter test;Operator=ExactMatch'` |
| Using `Value` | `--filter 'Type=monitors;Name=name;Value=^filter test$` |

#### Config file

A Custom config text file can be passed in place of options. 

This is an example config file:

```
# config

destination_api_url="https://api.datadoghq.eu"
destination_api_key="<API_KEY>"
destination_app_key="<APP_KEY>"
source_api_key="<API_KEY>"
source_app_key="<APP_KEY>"
source_api_url="https://api.datadoghq.com"
filter=["Type=Dashboards;Name=title;Value=Test screenboard", "Type=Monitors;Name=tags;Value=sync:true"]
```

Then, run: `datadog-sync import --config config`

#### Cleanup flag

The tools `sync` command provides a cleanup flag (`--cleanup`). Passing the cleanup flag will delete resources from the destination organization which have been removed from the source organization. The resources to be deleted are determined based on the difference between the state files of source and destination organization.

For example, `ResourceA` and `ResourceB` are imported and synced, followed by deleting `ResourceA` from the source organization. Running the `import` command will update the source organizations state file to only include `ResourceB`. The following `sync --cleanup=Force` command will now delete `ResourceA` from the destination organization.

#### Verify DDR status flag

By default all commands check the Datadog Disaster Recovery (DDR) status of both the source and destination organizations before running. This behavior is controlled by the boolean flag `--verify-ddr-status` or the environment variable `DD_VERIFY_DDR_STATUS`. 


#### State files

By default, a `resources` directory is generated in the current working directory of the user. This directory contains `json` mapping of resources between the source and destination organization. To avoid duplication and loss of mapping, this directory should be retained between tool usage. To override these directories use the `--source-resources-path` and `--destination-resource-path`.

When running againts multiple destination organizations, a seperate working directory should be used to ensure seperation of data. 

#### Supported resources

| Resource                               | Description                                                          |
|----------------------------------------|----------------------------------------------------------------------|
| authn_mappings                         | Sync Datadog authn mappings.                                         |
| dashboard_lists                        | Sync Datadog dashboard lists.                                        |
| dashboards                             | Sync Datadog dashboards.                                             |
| downtime_schedules                     | Sync Datadog downtimes.                                              |
| downtimes (**deprecated**)             | Sync Datadog downtimes.                                              |
| host_tags                              | Sync Datadog host tags.                                              |
| logs_archives                          | Sync Datadog logs archives. Requires GCP, Azure, or AWS integration. |
| logs_archives_order                    | Sync Datadog logs archives order.                                    |
| logs_custom_pipelines (**deprecated**) | Sync Datadog logs custom pipelines.                                  |
| logs_indexes                           | Sync Datadog logs indexes.                                           |
| logs_indexes_order                     | Sync Datadog logs indexes order.                                     |
| logs_metrics                           | Sync Datadog logs metrics.                                           |
| logs_pipelines                         | Sync Datadog logs OOTB integration and custom pipelines.             |
| logs_pipelines_order                   | Sync Datadog logs pipelines order.                                   |
| logs_restriction_queries               | Sync Datadog logs restriction queries.                               |
| metric_percentiles                     | Sync Datadog metric percentiles.                                     |
| metric_tag_configurations              | Sync Datadog metric tags configurations.                             |
| metrics_metadata                       | Sync Datadog metric metadata.                                        |
| monitors                               | Sync Datadog monitors.                                               |
| notebooks                              | Sync Datadog notebooks.                                              |
| powerpacks                             | Sync Datadog powerpacks.                                             |
| restriction_policies                   | Sync Datadog restriction policies.                                   |
| roles                                  | Sync Datadog roles.                                                  |
| sensitive_data_scanner_groups          | Sync SDS groups                                                      |
| sensitive_data_scanner_groups_order    | Sync SDS groups order                                                |
| sensitive_data_scanner_rules           | Sync SDS rules                                                       |
| service_level_objectives               | Sync Datadog SLOs.                                                   |
| slo_corrections                        | Sync Datadog SLO corrections.                                        |
| spans_metrics                          | Sync Datadog spans metrics.                                          |
| synthetics_global_variables            | Sync Datadog synthetic global variables.                             |
| synthetics_private_locations           | Sync Datadog synthetic private locations.                            |
| synthetics_tests                       | Sync Datadog synthetic tests.                                        |
| teams                                  | Sync Datadog teams (excluding users and permissions).                |
| users                                  | Sync Datadog users.                                                  |

***Note:*** `logs_custom_pipelines` resource has been deprecated in favor of `logs_pipelines` resource which supports both logs OOTB integration and custom pipelines. To migrate to the new resource, rename the existing state files from `logs_custom_pipelines.json` to `logs_pipelines.json` for both source and destination files.

## Best practices

Many Datadog resources are interdependent. For example, some Datadog resource can reference `roles` and `dashboards`, which includes widgets that may use Monitors or Synthetics data. The datadog-sync tool syncs these resources in order to ensure dependencies are not broken.

If importing/syncing subset of resources, users should ensure that dependent resources are imported and synced as well.

See [Supported resources](#supported-resources) section below for potential resource dependencies.

| Resource                               | Dependencies                                                     |
|----------------------------------------|------------------------------------------------------------------|
| authn_mappings                         | roles, teams                                                     |
| dashboard_lists                        | dashboards                                                       |
| dashboards                             | monitors, roles, powerpacks, service_level_objectives            |
| downtime_schedules                     | monitors                                                         |
| downtimes (**deprecated**)             | monitors                                                         |
| host_tags                              | -                                                                |
| logs_archives                          | - (Requires manual setup of AWS, GCP or Azure integration)       |
| logs_archives_order                    | logs_archives                                                    |
| logs_custom_pipelines (**deprecated**) | -                                                                |
| logs_indexes                           | -                                                                |
| logs_indexes_order                     | logs_indexes                                                     |
| logs_metrics                           | -                                                                |
| logs_pipelines                         | -                                                                |
| logs_pipelines_order                   | logs_pipelines                                                   |
| logs_restriction_queries               | roles                                                            |
| metric_percentiles                     | -                                                                |
| metric_tag_configurations              | -                                                                |
| metrics_metadata                       | -                                                                |
| monitors                               | roles, service_level_objectives                                  |
| notebooks                              | -                                                                |
| powerpacks                             | monitors, service_level_objectives                               |
| restriction_policies                   | dashboards, service_level_objectives, notebooks, users, roles    |
| roles                                  | -                                                                |
| sensitive_data_scanner_groups          | -                                                                |
| sensitive_data_scanner_groups_order    | sensitive_data_scanner_groups                                    |
| sensitive_data_scanner_rules           | sensitive_data_scanner_groups                                    |
| service_level_objectives               | monitors, synthetics_tests                                       |
| slo_corrections                        | service_level_objectives                                         |
| spans_metrics                          | -                                                                |
| synthetics_global_variables            | synthetics_tests                                                 |
| synthetics_private_locations           | -                                                                |
| synthetics_tests                       | synthetics_private_locations, synthetics_global_variables, roles |
| teams                                  | -                                                                |
| users                                  | roles                                                            |
