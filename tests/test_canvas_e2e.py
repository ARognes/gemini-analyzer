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

        tab_chat = page.query_selector("#subtabChat")
        self.assertIn("active", tab_chat.get_attribute("class"))

        tab_unified = page.query_selector("#subtabUnified")
        self.assertIsNotNone(tab_unified, "Subtab #subtabUnified missing from DOM")
        tab_unified.click()
        page.wait_for_timeout(500)

        self.assertIn("active", tab_unified.get_attribute("class"))
        print("✅ Test 01: Subtab activation PASSED")

    def test_02_canvas_node_hover_hit_test(self):
        page = self.page
        page.click("#subtabUnified")
        page.wait_for_timeout(1000)

        target_info = page.evaluate("""() => {
            if (!overlapData || !overlapData.nodes) return null;
            const canvasEl = document.getElementById('constellationCanvas');
            const rect = canvasEl.getBoundingClientRect();
            const n = overlapData.nodes.find(x => x.category === 'ai_agents' && typeof x.worldX === 'number');
            if (!n) return null;

            n.vx = 0; n.vy = 0;

            const screenX = rect.left + panX + (n.worldX * scale);
            const screenY = rect.top + panY + (n.worldY * scale);

            return {
                id: n.id,
                title: n.title || n.title_snippet,
                worldX: n.worldX,
                worldY: n.worldY,
                screenX: screenX,
                screenY: screenY
            };
        }""")

        self.assertIsNotNone(target_info, "No target node found")

        page.mouse.move(target_info["screenX"], target_info["screenY"])
        page.wait_for_timeout(400)

        hovered_id = page.evaluate("() => hoveredNode ? hoveredNode.id : null")
        self.assertEqual(hovered_id, target_info['id'], f"Hover hit test failed: expected {target_info['id']}, got {hovered_id}")
        print("✅ Test 02: Canvas node hover hit test PASSED")

    def test_03_canvas_node_drag_and_physics(self):
        page = self.page
        page.click("#subtabUnified")
        page.wait_for_timeout(1000)

        node_start = page.evaluate("""() => {
            if (!overlapData || !overlapData.nodes) return null;
            const canvasEl = document.getElementById('constellationCanvas');
            const rect = canvasEl.getBoundingClientRect();
            const n = overlapData.nodes.find(x => x.category === 'ai_agents' && typeof x.worldX === 'number');
            if (!n) return null;

            return {
                id: n.id,
                worldX: n.worldX,
                worldY: n.worldY,
                screenX: rect.left + panX + (n.worldX * scale),
                screenY: rect.top + panY + (n.worldY * scale)
            };
        }""")

        self.assertIsNotNone(node_start, "No node found for drag test")

        sx, sy = node_start["screenX"], node_start["screenY"]
        page.mouse.move(sx, sy)
        page.mouse.down()
        page.mouse.move(sx + 150, sy + 100, steps=10)

        dragged_id = page.evaluate("() => draggedNode ? draggedNode.id : null")
        self.assertEqual(dragged_id, node_start["id"], f"draggedNode should be {node_start['id']}, got {dragged_id}")

        node_during = page.evaluate(f"() => overlapData.nodes.find(n => n.id === '{node_start['id']}')")
        self.assertNotEqual(node_during["worldX"], node_start["worldX"], "Node worldX did not change during drag")

        page.mouse.up()
        page.wait_for_timeout(300)

        dragged_after = page.evaluate("() => draggedNode")
        self.assertIsNone(dragged_after, "draggedNode should be cleared after mouseup")
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

            # Check that sample pair has similarity percentage and titles
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
        page.evaluate("() => openCorrelationModal()")
        page.wait_for_timeout(600)

        modal = page.query_selector("#correlationModal")
        self.assertIsNotNone(modal)
        self.assertEqual(modal.evaluate("el => el.style.display"), "flex")

        # Verify total pairs text is populated
        total_txt = page.inner_text("#corrTotalPairs")
        self.assertNotEqual(total_txt, "--")

        # Change slider value to 50%
        page.fill("#corrSlider", "50")
        page.evaluate("() => updateCorrelationThreshold(50)")
        page.wait_for_timeout(500)

        slider_display = page.inner_text("#corrSliderValDisplay")
        self.assertEqual(slider_display, "50%")
        print("✅ Test 05: Correlation modal UI & slider interaction PASSED")

if __name__ == "__main__":
    unittest.main()
