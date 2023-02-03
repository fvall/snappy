import os
import stat
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

    def test_non_readable_empty(self):

        file = "a.txt"
        with tempfile.TemporaryDirectory(dir = ".") as folder:
            file = os.path.join(folder, file)
            with open(file, "w") as f:
                f.write("this is a file")

            out = cmd.find_non_readable(folder)
            stderr = out.stderr.decode("utf-8")
            stdout = out.stdout.decode("utf-8")

        self.assertEqual(out.returncode, 0)
        self.assertEqual(stderr, "")
        self.assertEqual(stdout, "")

    def test_non_readable_not_empty(self):

        files = ["f1.txt", "f2.txt", "f3.txt"]
        with tempfile.TemporaryDirectory(dir = ".") as folder:
            for idx, file in enumerate(files):
                file = os.path.join(folder, file)
                with open(file, "w") as f:
                    f.write(f"this is file {idx}")

                if idx < 2:
                    os.chmod(file, stat.S_IWUSR | stat.S_IWGRP | stat.S_IWOTH)
                else:
                    os.chmod(file, stat.S_IRWXU | stat.S_IRWXG | stat.S_IRWXO)

            out = cmd.find_non_readable(folder)
            stderr = out.stderr.decode("utf-8")
            stdout = out.stdout.decode("utf-8")

            self.assertEqual(out.returncode, 0)
            self.assertEqual(stderr, "")
            self.assertNotEqual(stdout, "")

            bad = stdout.split("\n")
            bad = [b.strip() for b in bad]
            bad = [b for b in bad if b != ""]
            self.assertEqual(len(bad), 2)

            files = (os.path.join(folder, f) for f in files[:2])
            files = {os.path.abspath(f) for f in files}
            self.assertFalse(set(bad).symmetric_difference(files))
