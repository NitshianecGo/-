import sys, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import fetch_news as f

class FeedTests(unittest.TestCase):
    def test_classify_rumor_before_update(self):
        self.assertEqual(f.classify('Possible WoW leak reveals patch', '', 'Google News', 'https://news.example/test', ''), 'rumor')
    def test_classify_video(self):
        self.assertEqual(f.classify('WoW news', '', 'YouTube · WoW', 'https://youtube.com/watch?v=x', 'https://youtube.com/watch?v=x'), 'video')
    def test_classify_event(self):
        self.assertEqual(f.classify('WoW tournament schedule announced', '', 'Google News', 'https://news.example/test', ''), 'event')
    def test_fuzzy_dedup(self):
        self.assertTrue(f.similar('World of Warcraft announces new patch notes', 'World of Warcraft announces new patch notes!'))
    def test_mode_detection(self):
        modes = f.get_modes('Classic Hardcore server update', '')
        self.assertIn('classic', modes); self.assertIn('hardcore', modes)
    def test_heat_is_bounded(self):
        item={'title':'New patch update','summary':'','published':f.NOW.isoformat(),'category':'update','credibility':'reported'}
        self.assertGreaterEqual(f.heat_score(item,1),1); self.assertLessEqual(f.heat_score(item,1),100)
    def test_no_invented_event_date(self): self.assertIsNone(f.extract_event_date('A big event is coming soon'))
    def test_url_canonicalization(self): self.assertNotIn('utm_source', f.canonical_url('https://example.com/story?utm_source=test&id=2'))
    def test_blizzard_only_is_official_category(self):
        self.assertEqual(f.classify('News', '', 'Blizzard WoW', 'https://worldofwarcraft.blizzard.com/news/a', ''), 'official')
        self.assertEqual(f.classify('News', '', 'Wowhead', 'https://www.wowhead.com/news/a', ''), 'community')

if __name__ == '__main__': unittest.main()
