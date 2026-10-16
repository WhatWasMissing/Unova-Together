"""Progress display for the install-cleanup worker, without opening a window."""
import time
import unittest
from types import SimpleNamespace

from launcher_ui.app import Launcher

class Variable:
    def __init__(self):self.value=''
    def set(self,value):self.value=value

class ProgressBar:
    def __init__(self):self.options={};self.stopped=False
    def stop(self):self.stopped=True
    def configure(self,**options):self.options.update(options)

class TextLog:
    def __init__(self):self.value=''
    def configure(self,**_):pass
    def insert(self,_where,value):self.value+=value
    def see(self,_where):pass

class CleanupProgressTests(unittest.TestCase):
    def setUp(self):
        self.app=SimpleNamespace(cleanup_eta=Variable(),cleanup_bar=ProgressBar(),cleanup_log=TextLog(),
                                 cleanup_started=time.monotonic(),cleanup_total=0,cleanup_done=0)

    def test_deleted_file_updates_eta_bar_and_full_path_log(self):
        Launcher._storage_progress(self.app,{'phase':'delete','stage':'start','total':4,'completed':0})
        self.app.cleanup_started-=3
        path=r'C:\Users\player\AppData\Roaming\UnovaTogether\.updates\versions\1.0.1\Unova-Together\builds\current\melonDS.exe'
        Launcher._storage_progress(self.app,{'phase':'delete','stage':'deleted','total':4,'completed':1,'path':path})
        self.assertEqual(self.app.cleanup_bar.options['maximum'],4)
        self.assertEqual(self.app.cleanup_bar.options['value'],1)
        self.assertIn('ETA',self.app.cleanup_eta.value)
        self.assertIn('Processed 1 of 4',self.app.cleanup_eta.value)
        self.assertIn('Deleted: '+path,self.app.cleanup_log.value)

    def test_removed_empty_directory_is_listed(self):
        path=r'C:\Users\player\AppData\Roaming\UnovaTogether\.updates\versions\1.0.1\Unova-Together\launcher\assets'
        Launcher._storage_progress(self.app,{'phase':'delete','stage':'directory','total':0,'completed':0,'path':path})
        self.assertIn('Removed empty folder: '+path,self.app.cleanup_log.value)

if __name__=='__main__':unittest.main()
