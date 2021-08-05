import os
import filecmp
import tempfile
import unittest
from snappy import cmd


class TestCommands(unittest.TestCase):

    def setUp(self) -> None:

        self.test_folder = tempfile.TemporaryDirectory()
        file1 = os.path.join(self.test_folder.name, "file1.txt")
        with open(file1, "w") as f:
            f.write("some text in the file")
    
        self.file1 = file1

    def tearDown(self) -> None:
        self.test_folder.cleanup()
    
    def test_copy_basic(self):

        # ----------------------
        #  basic test for copy
        # ----------------------
        
        file2 = os.path.join(self.test_folder.name, "file2.txt")
        cmd.cp(self.file1, file2)
        self.assertTrue(filecmp.cmp(self.file1, file2))

    def test_copy_with_flags(self):

        # -------------------------
        #  testing copy with flags
        # -------------------------

        file3 = os.path.join(self.test_folder.name, "file3.txt")
        cmd.cp(self.file1, file3, ["-sR"])
        self.assertTrue(os.path.islink(file3))

    def test_move(self):
        
        file4 = os.path.join(self.test_folder.name, "file4.txt")
        new = os.path.join(self.test_folder.name, "new.txt")
        
        cmd.cp(self.file1, new)
        cmd.mv(new, file4)
        self.assertTrue(filecmp.cmp(self.file1, file4))
        self.assertFalse(os.path.exists(new))
