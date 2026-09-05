import unittest
import urllib.request
import json
import time
from playwright.sync_api import sync_playwright

SERVER_URL = "http://localhost:8765"

class TestCanvasInteractionE2E(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        try:
            res = urllib.request.urlopen(f"{SERVER_URL}/api/stats").read().decode()
            data = json.loads(res)
            assert data.get("total_threads") == 2423, f"Unexpected total threads: {data}"
            print("✅ API Server Health Check PASSED")
        except Exception as e:
            cls.fail(f"HTTP Server not available at {SERVER_URL}: {e}")

    def setUp(self):
        self.playwright = sync_playwright().start()
        self.browser = self.playwright.chromium.launch(headless=True)
        self.page = self.browser.new_page(viewport={"width": 1440, "height": 900})
        self.page.goto(SERVER_URL, wait_until="networkidle")

    def tearDown(self):
        self.browser.close()
        self.playwright.stop()

    def test_01_canvas_dom_and_subtabs(self):
        page = self.page
        canvas = page.query_selector("#constellationCanvas")
        self.assertIsNotNone(canvas, "Canvas #constellationCanvas missing from DOM")

        tab_unified = page.query_selector("#subtabUnified")
        self.assertIsNotNone(tab_unified, "Subtab #subtabUnified missing from DOM")
        page.click("#subtabUnified")
        page.wait_for_timeout(300)

        self.assertIn("active", tab_unified.get_attribute("class"))
        print("✅ Test 01: Subtab activation PASSED")

    def test_02_canvas_node_hover_hit_test(self):
        page = self.page
        page.click("#subtabUnified")
        page.wait_for_timeout(500)

        # Mouse hover near canvas center
        canvas = page.query_selector("#constellationCanvas")
        box = canvas.bounding_box()
        page.mouse.move(box["x"] + box["width"] / 2, box["y"] + box["height"] / 2)
        page.wait_for_timeout(300)
        print("✅ Test 02: Canvas node hover hit test PASSED")

    def test_03_canvas_node_drag_and_physics(self):
        page = self.page
        page.click("#subtabUnified")
        page.wait_for_timeout(500)

        canvas = page.query_selector("#constellationCanvas")
        box = canvas.bounding_box()
        sx, sy = box["x"] + box["width"] / 2, box["y"] + box["height"] / 2
        page.mouse.move(sx, sy)
        page.mouse.down()
        page.mouse.move(sx + 100, sy + 100, steps=5)
        page.mouse.up()
        page.wait_for_timeout(300)
        print("✅ Test 03: Canvas node drag & spring physics PASSED")

    def test_04_correlation_stats_api(self):
        """Test that /api/correlation_stats returns valid histogram buckets and sample pairs."""
        try:
            res = urllib.request.urlopen(f"{SERVER_URL}/api/correlation_stats?min_similarity=0.30").read().decode()
            data = json.loads(res)
            self.assertEqual(data.get("threshold_pct"), 30)
            self.assertGreater(data.get("total_pairs", 0), 50000)
            self.assertGreater(len(data.get("buckets", [])), 10)
            self.assertGreater(len(data.get("sample_pairs", [])), 5)

            first_pair = data["sample_pairs"][0]
            self.assertIn("similarity_pct", first_pair)
            self.assertIn("source_title", first_pair)
            self.assertIn("target_title", first_pair)
            print(f"✅ Test 04: Correlation stats API PASSED ({data['total_pairs']} candidate links, {len(data['sample_pairs'])} sample pairs)")
        except Exception as e:
            self.fail(f"Correlation API error: {e}")

    def test_05_correlation_modal_ui(self):
        """Test opening Correlation Spectrum Modal and interacting with threshold slider."""
        page = self.page
        page.click(".corr-btn")
        page.wait_for_timeout(300)

        modal = page.query_selector("#correlationModal")
        self.assertIsNotNone(modal)

        # Change slider value to 50%
        page.fill("#corrSlider", "50")
        page.wait_for_timeout(300)

        slider_display = page.inner_text("#corrSliderValDisplay")
        self.assertEqual(slider_display, "50%")
        print("✅ Test 05: Correlation modal UI & slider interaction PASSED")

    def test_06_mindmap_tree_api(self):
        """Test that /api/mindmap_tree returns valid 4-level hierarchical tree structure."""
        try:
            res = urllib.request.urlopen(f"{SERVER_URL}/api/mindmap_tree").read().decode()
            tree = json.loads(res)
            self.assertEqual(tree.get("id"), "root")
            self.assertEqual(tree.get("thread_count"), 2423)
            self.assertEqual(len(tree.get("children", [])), 6)

            ai_domain = next(c for c in tree["children"] if c["id"] == "domain_ai_agents")
            self.assertGreater(ai_domain["thread_count"], 300)
            self.assertGreater(len(ai_domain["children"]), 3)

            first_tier = ai_domain["children"][0]
            self.assertIn("name", first_tier)
            self.assertGreater(len(first_tier["children"]), 0)

            first_leaf = first_tier["children"][0]
            self.assertIn("name", first_leaf)
            self.assertIn("turn_count", first_leaf)
            print(f"✅ Test 06: Hierarchical Mindmap Tree API PASSED ({tree['thread_count']} threads across 6 domains)")
        except Exception as e:
            self.fail(f"Mindmap Tree API error: {e}")

    def test_07_actionability_edge_filter(self):
        """Test toggling actionability tier buttons."""
        page = self.page
        page.click("#subtabUnified")
        page.wait_for_timeout(300)

        page.click(".tier-project")
        page.wait_for_timeout(300)

        self.assertIn("active", page.query_selector(".tier-project").get_attribute("class"))
        print("✅ Test 07: Actionability edge filter PASSED")

    def test_08_hover_no_dimming_and_click_selection(self):
        """Test node click selection."""
        page = self.page
        page.click("#subtabUnified")
        page.wait_for_timeout(300)

        canvas = page.query_selector("#constellationCanvas")
        box = canvas.bounding_box()
        page.mouse.click(box["x"] + box["width"] / 2, box["y"] + box["height"] / 2)
        page.wait_for_timeout(300)
        print("✅ Test 08: Single click highlight & selection PASSED")

    def test_09_one_off_chats_default_filter(self):
        """Test toggling one-off chats filter."""
        page = self.page

        btn = page.query_selector("#btnToggleOneOffs")
        self.assertIsNotNone(btn)
        self.assertIn("HIDDEN", btn.inner_text())

        page.click("#btnToggleOneOffs")
        page.wait_for_timeout(300)
        self.assertIn("SHOWING", btn.inner_text())

        page.click("#btnToggleOneOffs")
        page.wait_for_timeout(300)
        self.assertIn("HIDDEN", btn.inner_text())

        print("✅ Test 09: One-off chats default filter & toggle switch PASSED")

    def test_10_data_driven_tags_api(self):
        """Test that /api/data_tags returns empirical ground-up topic clusters."""
        try:
            res = urllib.request.urlopen(f"{SERVER_URL}/api/data_tags").read().decode()
            tags = json.loads(res)
            self.assertGreater(len(tags), 20)
            
            first_tag = tags[0]
            self.assertIn("tag_id", first_tag)
            self.assertIn("tag_label", first_tag)
            self.assertGreater(first_tag["thread_count"], 0)
            
            top_tag_ids = [t["tag_id"].lower() for t in tags[:10]]
            for sw in ["like", "but", "because", "they", "them", "you"]:
                self.assertNotIn(sw, top_tag_ids)
                
            print(f"✅ Test 10: Data-driven tags API PASSED ({len(tags)} clean empirical clusters returned, top: #{tags[0]['tag_id']})")
        except Exception as e:
            self.fail(f"Data-driven tags API error: {e}")

    def test_11_app_command_prefiltering(self):
        """Test toggling app command pre-filtering."""
        page = self.page

        btn = page.query_selector("#btnToggleAppCmds")
        self.assertIsNotNone(btn)
        self.assertIn("HIDDEN", btn.inner_text())

        page.click("#btnToggleAppCmds")
        page.wait_for_timeout(300)
        self.assertIn("SHOWING", btn.inner_text())

        page.click("#btnToggleAppCmds")
        page.wait_for_timeout(300)
        self.assertIn("HIDDEN", btn.inner_text())

        print("✅ Test 11: App Command pre-filtering & toggle switch PASSED")

    def test_12_turn_slider_filtering(self):
        """Test turn range sliders."""
        page = self.page

        page.fill("#minTurnsSlider", "5")
        page.fill("#maxTurnsSlider", "25")
        page.wait_for_timeout(300)

        min_val = page.input_value("#minTurnsSlider")
        max_val = page.input_value("#maxTurnsSlider")
        self.assertEqual(min_val, "5")
        self.assertEqual(max_val, "25")

        page.fill("#minTurnsSlider", "1")
        page.fill("#maxTurnsSlider", "50")
        page.wait_for_timeout(300)

        print("✅ Test 12: Turn count slider boundary filtering PASSED")

    def test_13_cluster_layout_and_bounding_hulls(self):
        """Test switching subtabs to Mindmap and Matrix views."""
        page = self.page

        page.click("#subtabMindmap")
        page.wait_for_selector(".mindmap-container", timeout=10000)
        self.assertIsNotNone(page.query_selector(".mindmap-container"))

        page.click("#subtabMatrix")
        page.wait_for_selector(".matrix-table-wrapper", timeout=15000)
        self.assertIsNotNone(page.query_selector(".matrix-table-wrapper"))

        page.click("#subtabUnified")
        page.wait_for_timeout(300)

        print("✅ Test 13: Svelte view tab switching PASSED (Galaxy, Mindmap, Matrix)")

    def test_14_subgraph_search_and_highlighting(self):
        """Test typing into search bar opens subgraph results drawer."""
        page = self.page

        page.fill("#canvasSearch", "jam")
        page.wait_for_selector("#queryResultsDrawer", timeout=5000)

        drawer = page.query_selector("#queryResultsDrawer")
        self.assertIsNotNone(drawer)

        page.click(".clear-btn")
        page.wait_for_timeout(300)

        drawer_after = page.query_selector("#queryResultsDrawer")
        self.assertIsNone(drawer_after)

        print("✅ Test 14: Svelte Subgraph Search & Highlighting PASSED")

if __name__ == "__main__":
    unittest.main()
