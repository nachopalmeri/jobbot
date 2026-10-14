import unittest

from job_bot.search_sources import get_search_source_catalog
from job_bot import config


class SearchSourceCatalogTests(unittest.TestCase):
    def test_catalog_separates_automated_feeds_from_manual_discovery(self):
        sources = {source["id"]: source for source in get_search_source_catalog()}

        self.assertEqual(sources["remotive"]["access"], "automated_api")
        self.assertEqual(sources["startups_argentina"]["access"], "manual")
        self.assertEqual(sources["wellfound"]["access"], "manual")
        self.assertEqual(sources["uade"]["access"], "authenticated_manual")

    def test_catalog_keeps_ai_task_platforms_outside_employment_sources(self):
        sources = {source["id"]: source for source in get_search_source_catalog()}

        for source_id in ("outlier", "alignerr", "dataannotation", "prolific"):
            self.assertEqual(sources[source_id]["group"], "ai_task_work")
            self.assertNotEqual(sources[source_id]["kind"], "employment")

    def test_remote_apis_and_startup_discovery_are_both_in_the_unified_catalog(self):
        sources = get_search_source_catalog()
        source_ids = {source["id"] for source in sources}

        self.assertTrue({"remotive", "arbeitnow", "jobicy", "himalayas"}.issubset(source_ids))
        self.assertTrue({"wellfound", "yc_jobs", "startupjobs", "vibehackers", "cosign"}.issubset(source_ids))

    def test_all_job_and_startup_routes_from_user_bookmarks_are_in_catalog(self):
        sources = {source["id"]: source for source in get_search_source_catalog()}
        expected_job_routes = {
            "startups_argentina", "cosign", "wellfound", "yc_jobs", "startupjobs",
            "firstjob", "empleosit", "indeed", "computrabajo", "getonbrd", "uade",
            "linkedin", "vibe_coding_jobs", "vibehackers", "remotive", "arbeitnow",
            "jobicy", "himalayas", "outlier", "alignerr", "dataannotation", "prolific",
        }

        self.assertTrue(expected_job_routes.issubset(sources))
        self.assertEqual(sources["cosign"]["access"], "manual")
        self.assertIn("appgentina_events", sources)
        self.assertEqual(sources["appgentina_events"]["kind"], "ecosystem")

    def test_catalog_can_filter_group_without_mutating_shared_source_data(self):
        task_sources = get_search_source_catalog(group="ai_task_work")
        self.assertEqual({source["id"] for source in task_sources}, {"outlier", "alignerr", "dataannotation", "prolific"})
        task_sources[0]["name"] = "changed by caller"
        self.assertNotEqual(get_search_source_catalog(group="ai_task_work")[0]["name"], "changed by caller")

    def test_unified_search_taxonomy_covers_user_requested_role_families(self):
        taxonomy = " ".join(config.GENERAL_SEARCH_KEYWORDS).casefold()

        for term in ("qa", "automation", "rpa", "agents", "workflows", "prompt engineering", "trainee", "pasantía", "analista funcional", "redes", "forward deployed", "remote"):
            with self.subTest(term=term):
                self.assertIn(term, taxonomy)


if __name__ == "__main__":
    unittest.main()
