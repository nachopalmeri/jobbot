import unittest

from job_bot.search_queries import build_search_queries


class BuildSearchQueriesTests(unittest.TestCase):
    def test_reserves_slots_for_balanced_broad_queries_and_user_terms(self):
        broad = ["part-time dev", "part-time AI", "part-time systems", "AI trainee", "analista funcional", "redes soporte"]
        personal = ["Python junior", "Backend trainee", "QA junior"]

        result = build_search_queries(personal, broad, limit=8)

        self.assertEqual(
            result,
            [
                "part-time dev",
                "part-time AI",
                "part-time systems",
                "AI trainee",
                "analista funcional",
                "redes soporte",
                "Python junior",
                "Backend trainee",
            ],
        )

    def test_deduplicates_case_insensitively_and_can_disable_broad_queries(self):
        result = build_search_queries(
            ["Python junior", "python Junior", "QA trainee"],
            ["AI trainee"],
            limit=5,
            include_broad=False,
        )

        self.assertEqual(result, ["Python junior", "QA trainee"])

    def test_keeps_personal_terms_when_query_budget_is_lower_than_role_taxonomy(self):
        broad = ["part-time dev", "part-time AI", "part-time systems", "AI trainee"]
        personal = ["Python junior", "Backend trainee", "QA junior"]

        result = build_search_queries(personal, broad, limit=5)

        self.assertEqual(
            result,
            ["part-time dev", "part-time AI", "part-time systems", "Python junior", "Backend trainee"],
        )


if __name__ == "__main__":
    unittest.main()
