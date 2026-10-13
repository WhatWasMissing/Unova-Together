import tempfile,unittest
from pathlib import Path
from launcher_ui.game_routes import research_command

class RouteTests(unittest.TestCase):
    def fixture(self,path):
        (path/'tools').mkdir();(path/'profiles').mkdir()
        for name in ('start_joinable_session.ps1','start_lan_coop.ps1'):(path/'tools'/name).write_text('fixture')
        (path/'profiles/pokemon-x-base.research.json').write_text('{}')
    def test_selected_modes_route_only_to_known_local_scripts(self):
        with tempfile.TemporaryDirectory(prefix='Pokemon Together ') as folder:
            root=Path(folder);self.fixture(root)
            _,local=research_command(root,'local');self.assertEqual(local[-1],'-GeneralTrainers')
            _,host=research_command(root,'host');self.assertEqual(host[-2:],['-Address','0.0.0.0'])
            _,guest=research_command(root,'guest','192.168.0.63');self.assertEqual(guest[-2:],['-Address','192.168.0.63'])
            self.assertEqual(local[5],str(root/'tools/start_joinable_session.ps1'))
    def test_bad_modes_addresses_and_missing_setup_reject_before_launch(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)
            with self.assertRaises(ValueError):research_command(root,'local')
            self.fixture(root)
            for mode,address in (('other','127.0.0.1'),('guest','bad; command'),('guest','::1'),('guest','0.0.0.0')):
                with self.assertRaises(ValueError):research_command(root,mode,address)
