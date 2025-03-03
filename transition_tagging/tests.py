import unittest
from transition_tagging.constants import GLOBAL_VARIABLE_IDS
from transition_tagging.tagging_changes import (
    add_tag,
    count_items,
    drop_a_from_asset_ids,
    filter_by_tag,
    getEnv,
    remove_business_and_busines_accidental_tags,
    remove_duplicate_managed_by_datadogsync_tag,
    remove_tag,
    rename_tr_asset_insight_id_with_findlaw_asset_id,
    replace_env_findlaw_x_with_env_x,
    skip_created_by_terraform_resources,
    swap_global_variables,
    swap_private_locations,
    swap_tag_key,
    PRIVATE_LOCATIONS,
)


class TestReplaceEnvFindlawTags(unittest.TestCase):
    def test_dev_and_ci_environments(self):
        data = {
            "dev and ci": {"tags": ["env:findlaw-dev", "env:findlaw-ci"]},
        }
        replace_env_findlaw_x_with_env_x(data)
        self.assertCountEqual(data["dev and ci"]["tags"], ["env:dev"])

    def test_dev_and_ci_environments_backwards(self):
        data = {
            "ci and dev": {"tags": ["env:findlaw-ci", "env:findlaw-dev"]},
        }

        replace_env_findlaw_x_with_env_x(data)

        self.assertCountEqual(data["ci and dev"]["tags"], ["env:dev"])

    def test_ci_gets_renamed_to_dev(self):
        data = {"ci": {"tags": ["env:findlaw-ci", "team:findlaw"]}}
        replace_env_findlaw_x_with_env_x(data)
        self.assertCountEqual(data["ci"]["tags"], ["env:dev", "team:findlaw"])

    def test_one_environment(self):
        data = {
            "dev": {"tags": ["env:findlaw-dev", "team:findlaw"]},
            "qa": {"tags": ["env:findlaw-qa"]},
            "stage": {"tags": ["team:findlaw", "env:findlaw-stage"]},
            "prod": {"tags": ["env:findlaw-prod"]},
        }

        replace_env_findlaw_x_with_env_x(data)
        self.assertCountEqual(data["dev"]["tags"], ["team:findlaw", "env:dev"])
        self.assertCountEqual(data["qa"]["tags"], ["env:qa"])
        self.assertCountEqual(data["stage"]["tags"], ["team:findlaw", "env:stage"])
        self.assertCountEqual(data["prod"]["tags"], ["env:prod"])


class TestFilterByTag(unittest.TestCase):
    def test_filter_by_tag(self):
        data = {
            "dev": {"tags": ["env:findlaw-dev", "team:findlaw"]},
            "qa": {"tags": ["env:findlaw-qa"]},
            "stage": {"tags": ["team:findlaw", "env:findlaw-stage"]},
            "prod": {"tags": ["env:findlaw-prod"]},
        }
        filter_by_tag(data, "env:findlaw-dev")
        self.assertCountEqual(
            data, {"dev": {"tags": ["env:findlaw-dev", "team:findlaw"]}}
        )


class TestAddTags(unittest.TestCase):
    def test_add_tag(self):
        data = {"dev": {"tags": ["team:findlaw"]}}
        add_tag(data, "business_unit:findlaw")
        self.assertCountEqual(
            data["dev"]["tags"], ["business_unit:findlaw", "team:findlaw"]
        )


class TestRemoveItemsCreatedByTerraform(unittest.TestCase):
    def test_remove_items_created_by_terraform(self):
        data = {
            "no terraform": {"tags": ["env:findlaw-dev", "team:findlaw"]},
            "terraform": {"tags": ["env:findlaw-qa", "created_by:terraform"]},
        }
        skip_created_by_terraform_resources(data)
        self.assertCountEqual(
            data, {"no terraform": {"tags": ["env:findlaw-dev", "team:findlaw"]}}
        )


class TestRemoveAFromAssetIds(unittest.TestCase):
    def test_remove_a_from_asset_ids(self):
        data = {"object": {"tags": ["findlaw-asset-id:a12345"]}}
        drop_a_from_asset_ids(data)
        self.assertCountEqual(data["object"]["tags"], ["findlaw-asset-id:12345"])


class TestFindLawEnvTagging(unittest.TestCase):
    def test_replace_env_findlaw_x_with_env_x(self):
        data = {"dev": {"tags": ["env:findlaw-dev", "team:findlaw"]}}
        replace_env_findlaw_x_with_env_x(data)
        self.assertCountEqual(data["dev"]["tags"], ["team:findlaw", "env:dev"])

    def test_capitalized_findlaw_env(self):
        data = {"dev": {"tags": ["env:Findlaw-dev", "team:findlaw"]}}
        replace_env_findlaw_x_with_env_x(data)
        self.assertCountEqual(data["dev"]["tags"], ["team:findlaw", "env:dev"])

    def test_with_spaces(self):
        data = {
            "dev": {"tags": ["env: findlaw-dev", "team:findlaw"]},
            "qa": {"tags": ["env:findlaw-qa "]},
        }
        replace_env_findlaw_x_with_env_x(data)
        self.assertCountEqual(data["dev"]["tags"], ["team:findlaw", "env:dev"])
        self.assertCountEqual(data["qa"]["tags"], ["env:qa"])


class TestHelpers(unittest.TestCase):
    def test_get_env(self):
        data = {
            "dev": {"tags": ["env:findlaw-dev", "team:findlaw"]},
            "qa": {"tags": ["env:qa"]},
            "stage": {"tags": ["team:findlaw", "env:findlaw-stage"]},
            "prod": {"tags": ["env:prod"]},
        }
        self.assertEqual(getEnv(data["dev"]), "dev")
        self.assertEqual(getEnv(data["qa"]), "qa")
        self.assertEqual(getEnv(data["stage"]), "stage")
        self.assertEqual(getEnv(data["prod"]), "prod")

    def test_swap_tag_key(self):
        data = {"object": {"tags": ["tr_application-asset-insight-id:12345"]}}
        swap_tag_key(data, "tr_application-asset-insight-id", "findlaw-asset-id")
        self.assertCountEqual(data["object"]["tags"], ["findlaw-asset-id:12345"])

    def test_add_tag(self):
        data = {"object": {"tags": []}}
        add_tag(data, "business_unit:findlaw")
        self.assertCountEqual(data["object"]["tags"], ["business_unit:findlaw"])

    def test_remove_tag(self):
        data = {
            "object": {"tags": ["business", "business_unit:findlaw", "team:findlaw"]}
        }
        remove_tag(data, "business")
        self.assertCountEqual(
            data["object"]["tags"], ["business_unit:findlaw", "team:findlaw"]
        )


class TestReplaceAssetInsightIdTag(unittest.TestCase):
    def test_replace_tr_asset_id_with_findlaw_asset_id(self):
        data = {"object": {"tags": ["tr_application-asset-insight-id:12345"]}}
        rename_tr_asset_insight_id_with_findlaw_asset_id(data)
        self.assertCountEqual(data["object"]["tags"], ["findlaw-asset-id:12345"])


class TestRemoveAccidentalTags(unittest.TestCase):
    def test_remove_business_and_busines_accidental_tags(self):
        data = {
            "object": {
                "tags": [
                    "business",
                    "busines",
                    "business_unit:findlaw",
                    "team:findlaw",
                    "env:stage",
                ]
            }
        }
        remove_business_and_busines_accidental_tags(data)
        self.assertCountEqual(
            data["object"]["tags"],
            ["business_unit:findlaw", "team:findlaw", "env:stage"],
        )

    def test_remove_duplicate_managed_by_datadogsync_tag(self):
        data = {
            "object": {
                "tags": [
                    "managed_by:datadog-sync",
                    "managed_by:datadog-sync",
                    "team:findlaw",
                    "env:stage",
                ]
            }
        }
        remove_duplicate_managed_by_datadogsync_tag(data)
        self.assertCountEqual(
            data["object"]["tags"],
            ["team:findlaw", "env:stage", "managed_by:datadog-sync"],
        )


class TestCountItems(unittest.TestCase):
    def test_count_items(self):
        data = {
            "dev": {"tags": ["env:findlaw-dev", "team:findlaw"]},
            "qa": {"tags": ["env:findlaw-qa"]},
            "stage": {"tags": ["team:findlaw", "env:findlaw-stage"]},
            "prod": {"tags": ["env:findlaw-prod"]},
        }
        self.assertEqual(count_items(data), 4)


class TestChangingPrivateLocations(unittest.TestCase):
    def test_changing_private_locations(self):
        data = {
            "stage/prod": {
                "locations": [PRIVATE_LOCATIONS["stage/prod"]["tr"]["findlaw"]]
            },
            "dev/qa": {"locations": [PRIVATE_LOCATIONS["dev/qa"]["tr"]["findlaw"]]},
        }
        swap_private_locations(data)
        self.assertCountEqual(
            data["stage/prod"]["locations"],
            [PRIVATE_LOCATIONS["stage/prod"]["findlaw"]],
        )
        self.assertCountEqual(
            data["dev/qa"]["locations"],
            [PRIVATE_LOCATIONS["dev/qa"]["findlaw"]],
        )
        self.assertCountEqual(
            data["stage/prod"]["locations"],
            [PRIVATE_LOCATIONS["stage/prod"]["findlaw"]],
        )
        self.assertEqual(
            data["dev/qa"]["locations"],
            [PRIVATE_LOCATIONS["dev/qa"]["findlaw"]],
        )


class TestChangingGlobalVariables(unittest.TestCase):
    def test_changing_global_variables(self):
        data = {
            "findlaw-tr": {
                "config": {
                    "variables": [
                        {
                            "type": "global",
                            "name": "FINDLAW_BOT_USERNAME",
                            "id": GLOBAL_VARIABLE_IDS["FINDLAW_BOT_USERNAME"][
                                "tr"
                            ]["findlaw"],
                        },
                        {
                            "type": "global",
                            "name": "FINDLAW_BOT_PASSWORD",
                            "id": GLOBAL_VARIABLE_IDS["FINDLAW_BOT_PASSWORD"][
                                "tr"
                            ]["findlaw"],
                        },
                    ]
                }
            }
        }
        swap_global_variables(data)
        answer = {
            "findlaw-tr": {
                "config": {
                    "variables": [
                        {
                            "type": "global",
                            "name": "FINDLAW_BOT_USERNAME",
                            "id": GLOBAL_VARIABLE_IDS["FINDLAW_BOT_USERNAME"][
                                "findlaw"
                            ],
                        },
                        {
                            "type": "global",
                            "name": "FINDLAW_BOT_PASSWORD",
                            "id": GLOBAL_VARIABLE_IDS["FINDLAW_BOT_PASSWORD"][
                                "findlaw"
                            ],
                        },
                    ]
                }
            }
        }
        self.assertCountEqual(
            data["findlaw-tr"]["config"]["variables"],
            answer["findlaw-tr"]["config"]["variables"],
        )
        self.assertEqual(data, answer)  # deep comparison


if __name__ == "__main__":
    unittest.main(buffer=False)
