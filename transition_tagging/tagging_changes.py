import re
from transition_tagging.constants import GLOBAL_VARIABLE_IDS, PRIVATE_LOCATIONS


def count_items(data):
    count = 0
    for key, value in data.items():
        if "tags" in value:
            count += 1
    return count


def add_tag(data, tag):
    count = 0
    for key, value in data.items():
        if tag not in value["tags"]:
            value["tags"].append(tag)
            count += 1
    if count > 0:
        print(f"Added tag {tag} in {count} items.")


def change_tick_options_to_weekly(data):
    count = 0
    for key, value in data.items():
        if "options" in value:
            options = value["options"]
            if "tick_every" in options:
                count += 1
                options["tick_every"] = 604800
    if count > 0:
        print(f"Changed tick_every to weekly (604800) in {count} items.")


def change_retry_to_0(data):
    count = 0
    for key, value in data.items():
        if "options" in value:
            options = value["options"]
            if "retry" in options:
                count += 1
                options["retry"]["count"] = 0
    if count > 0:
        print(f"Changed retry to 0 in {count} items.")


def add_friday_scheduling(data):
    count = 0
    for key, value in data.items():
        if "options" in value:
            options = value["options"]
            if "scheduling" not in options:
                count += 1
                options["scheduling"] = {
                    "timezone": "America/Chicago",
                    "timeframes": [{"day": 5, "from": "07:00", "to": "12:00"}],
                }
    if count > 0:
        print(f"Added Friday scheduling in {count} items.")


def swap_tag_key(data, tagkey1, tagkey2):
    count = 0
    for key, value in data.items():
        if "tags" in value:
            for i, tag in enumerate(value["tags"]):
                if tag.startswith(tagkey1):
                    value["tags"][i] = tag.replace(tagkey1, tagkey2)
                    count += 1
    return count


def getEnv(item):
    if "tags" in item:
        for tag in item["tags"]:
            match = re.search(r"env:(?:findlaw-)?(\w+)", tag)
            if match:
                return match.group(1)
            continue
    print("no env found")
    return None


# helper function
def is_env_findlaw_x(tag, x):
    match = re.match(rf"env:\s*findlaw-{x}\s*", tag, re.IGNORECASE)
    return match


def replace_env_findlaw_x_with_env_x(data):
    count_dev = 0
    count_ci = 0
    count_qa = 0
    count_stage = 0
    count_prod = 0
    for key, value in data.items():
        if "tags" not in value:
            print(f'TODO - no "tags" key found for {key}')
            continue
        tags = value["tags"]
        if not any("env:" in tag for tag in tags):
            print(f'TODO - no "env:" tag found for {key}')
        for i, tag in enumerate(tags):
            if is_env_findlaw_x(tag, "dev"):
                count_dev += 1
                if not any("env:dev" in tag for tag in tags):
                    tags[i] = "env:dev"
                else:
                    tags.remove(tag)
            elif is_env_findlaw_x(tag, "ci"):
                count_ci += 1
                if not any("env:dev" in tag for tag in tags):
                    tags[i] = "env:dev"
                else:
                    tags.remove(tag)
            elif is_env_findlaw_x(tag, "qa"):
                count_qa += 1
                tags.remove(tag)
                tags.append("env:qa")
            elif is_env_findlaw_x(tag, "stage"):
                count_stage += 1
                tags.remove(tag)
                tags.append("env:stage")
            elif is_env_findlaw_x(tag, "prod"):
                count_prod += 1
                tags.remove(tag)
                tags.append("env:prod")
            else:
                # print("not an env tag:", tag)
                continue


def rename_tr_asset_insight_id_with_findlaw_asset_id(data):
    swap_tag_key(data, "tr_application-asset-insight-id", "findlaw-asset-id")


def drop_a_from_asset_ids(data):
    for key, value in data.items():
        if "tags" not in value:
            print(f'No "tags" key found for {key}')
            continue
        tags = value["tags"]
        for i, tag in enumerate(tags):
            if tag.startswith("findlaw-asset-id:a"):
                tags[i] = re.sub(
                    r"(?i)findlaw-asset-id:a(\w+)", r"findlaw-asset-id:\1", tag
                )


def remove_tag(data, tag):
    count = 0
    for key, value in data.items():
        if tag in value["tags"]:
            value["tags"].remove(tag)
            count += 1
    return count


def remove_business_and_busines_accidental_tags(data):
    count = remove_tag(data, "business")
    if count > 0:
        print(f'Removed {count} accidental "business:" tags')
    count = remove_tag(data, "busines")
    if count > 0:
        print(f'Removed {count} accidental "busines:" tags')


def remove_duplicate_managed_by_datadogsync_tag(data):
    tag = "managed_by:datadog-sync"
    count = 0
    for key, value in data.items():
        if "tags" in value:
            tags = value["tags"]
            if tags.count(tag) > 1:
                count += 1
                while tags.count(tag) > 1:
                    tags.remove(tag)


def delete_items_with_tag(data, tag):
    keys_to_remove = [key for key, value in data.items() if tag in value["tags"]]
    for key in keys_to_remove:
        del data[key]
    print(f"Removed {len(keys_to_remove)} items with tag {tag}")


def skip_created_by_terraform_resources(data):
    delete_items_with_tag(data, "created_by:terraform")

def filter_by_names(data, names):
    keys_to_remove = [
        key for key, value in data.items() if value.get("name") not in names
    ]
    print(len(keys_to_remove), "items to remove")
    for key in keys_to_remove:
        del data[key]
    if len(keys_to_remove) > 0:
        print(f"Removed {len(keys_to_remove)} items that did not have name in {names}")


def filter_by_tag(data, tag):
    keys_to_remove = [
        key for key, value in data.items() if tag not in value.get("tags", [])
    ]
    for key in keys_to_remove:
        del data[key]
    print(f'Removed {len(keys_to_remove)} items that did not have tag "{tag}"')

# output objects in json that do not contain a tag in tags containing "tr_application-asset-insight-id"
def identify_resources_without_asset_ids(data):
    missing_tags = []
    for key, value in data.items():
        tags = value["tags"]
        if not any(
            "tr_application-asset-insight-id" in tag or "findlaw-asset-id" in tag
            for tag in tags
        ):
            missing_tags.append(key)
    if len(missing_tags) > 0:
        print(
            f"TODO - The following items need asset IDs before importing to Avvo Account! Missing tags in {len(missing_tags)} items: {missing_tags}"
        )


def swap_private_locations(data):
    for key, value in data.items():
        if "locations" in value:
            locations = value["locations"]
            for i, location in enumerate(locations):
                if location in (
                    PRIVATE_LOCATIONS["dev/qa"]["findlaw"],
                    PRIVATE_LOCATIONS["stage/prod"]["findlaw"],
                ):
                    continue
                if (
                    location in PRIVATE_LOCATIONS["dev/qa"]["tr"].values()
                ):
                    locations[i] = PRIVATE_LOCATIONS["dev/qa"]["findlaw"]
                elif (
                    location in PRIVATE_LOCATIONS["stage/prod"]["tr"].values()
                ):
                    locations[i] = PRIVATE_LOCATIONS["stage/prod"]["findlaw"]
                elif any(cloud in location for cloud in ("aws:", "gcp", "azure:")):
                    continue
                else:
                    print(f"!! Unexpected private location found: {location} in {key}")
    return


def swap_global_variables(data):
    for key, value in data.items():
        if "config" in value:
            config = value["config"]
            if "variables" in config:
                variables = config["variables"]
                for variable in variables:
                    if "name" in variable and "id" in variable:
                        name = variable["name"]
                        id = variable["id"]
                        if name == "FINDLAW_BOT_USERNAME":
                            if (
                                id
                                != GLOBAL_VARIABLE_IDS["FINDLAW_BOT_USERNAME"][
                                    "findlaw"
                                ]
                            ):
                                if id not in set(
                                    GLOBAL_VARIABLE_IDS["FINDLAW_BOT_USERNAME"][
                                        "tr"
                                    ].values()
                                ).union(
                                    {
                                        GLOBAL_VARIABLE_IDS[
                                            "FINDLAW_BOT_USERNAME"
                                        ]["avvo"]
                                    }
                                ):
                                    print(
                                        "unknown ID for FINDLAW_BOT_USERNAME found",
                                        id,
                                    )
                                    continue
                                variable["id"] = GLOBAL_VARIABLE_IDS[
                                    "FINDLAW_BOT_USERNAME"
                                ]["findlaw"]
                        if name == "FINDLAW_BOT_PASSWORD":
                            if (
                                id
                                != GLOBAL_VARIABLE_IDS["FINDLAW_BOT_PASSWORD"][
                                    "findlaw"
                                ]
                            ):
                                if id not in GLOBAL_VARIABLE_IDS["FINDLAW_BOT_PASSWORD"][
                                        "tr"
                                    ]:
                                    print(
                                        "unknown ID for FINDLAW_BOT_PASSWORD found",
                                        id,
                                    )
                                    continue
                                variable["id"] = GLOBAL_VARIABLE_IDS[
                                    "FINDLAW_BOT_PASSWORD"
                                ]["findlaw"]