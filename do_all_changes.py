import json
import argparse
import transition_tagging.tagging_changes as tagging_changes

resource_options = ["monitors", "dashboards", "synthetics"]


def main():
    parser = argparse.ArgumentParser(
        description="CLI for performing tagging changes on Datadog Resources."
    )
    parser.add_argument(
        "--names", type=str, nargs="+", help="Name of resource to filter on"
    )
    parser.add_argument("--t", type=str, help="tag to filter on")
    parser.add_argument(
        "--change_retry_to_0",
        action="store_true",
        help="For synthetic tests > setting retry to 0",
    )
    parser.add_argument(
        "--r",
        required=True,
        type=str,
        choices=resource_options,
        help="Resources (json files) work on",
    )

    args = parser.parse_args()

    file_name = "resources/source/xxx.json"

    if args.r == "monitors":
        file_name = file_name.replace("xxx", "monitors")
    elif args.r == "dashboards":
        file_name = file_name.replace("xxx", "dashboards")
    elif args.r == "synthetics":
        file_name = file_name.replace("xxx", "synthetics_tests")
    else:
        print("Invalid resource")
        return

    with open(file_name, "r") as file:
        data = json.load(file)

    # Create a backup of the original file name with _backup
    backup_file_name = file_name.replace(".json", "_backup.json")
    with open(backup_file_name, "w") as file:
        json.dump(data, file, indent=4)

    # Remove items created by terraform
    if args.r != "dashboards":
        tagging_changes.skip_created_by_terraform_resources(data)
    
    # If dashboards, filter by team:findlaw
    if args.r == "dashboards":
        tagging_changes.filter_by_tag(data, "team:findlaw")

    if args.names:
        tagging_changes.filter_by_names(data, args.names)

    if args.t:
        print("arg t", args.t)
        tagging_changes.filter_by_tag(data, args.t)

    if args.change_retry_to_0:
        if args.resource != "synthetics":
            print("retry can only be changed for synthetics")
            return
        tagging_changes.change_retry_to_0(data)

    if args.r != "dashboards":
        tagging_changes.add_tag(data, "business_unit:findlaw")
    tagging_changes.add_tag(data, "team:findlaw")

    if args.r != "dashboards":
        tagging_changes.replace_env_findlaw_x_with_env_x(data)

    tagging_changes.identify_resources_without_asset_ids(
        data
    ) 

    tagging_changes.rename_tr_asset_insight_id_with_findlaw_asset_id(data)

    tagging_changes.drop_a_from_asset_ids(data)

    tagging_changes.remove_business_and_busines_accidental_tags(data)

    tagging_changes.remove_duplicate_managed_by_datadogsync_tag(data)

    tagging_changes.swap_private_locations(data)

    tagging_changes.swap_global_variables(data)

    tagging_changes.change_tick_options_to_weekly(data)

    num_items_to_move = tagging_changes.count_items(data)
    print("num_items_to_move", num_items_to_move)

    # Save changes to original file name
    with open(file_name, "w") as file:
        json.dump(data, file, indent=4)


if __name__ == "__main__":
    main()
