import os
import filecmp
import tempfile
import unittest
import shutil
from snappy import rsync


class TestRsync(unittest.TestCase):

    def setUp(self) -> None:
        self.test_folder = tempfile.TemporaryDirectory()

    def tearDown(self) -> None:
        self.test_folder.cleanup()
    
    def test_rsync_file(self):

        file1 = os.path.join(self.test_folder.name, "file1.txt")
        file2 = os.path.join(self.test_folder.name, "file2.txt")
        with open(file1, "w") as f:
            f.write("some text in the file")

        rsync.rsync(file1, file2)
        self.assertTrue(filecmp.cmp(file1, file2))

    def test_rsync_folder(self):
        
        folder1 = os.path.join(self.test_folder.name, "folder1")
        file1 = os.path.join(folder1, "file1.txt")
        
        folder2 = os.path.join(folder1, "folder2")
        file2 = os.path.join(folder2, "file2.txt")
        
        os.makedirs(folder1)
        os.makedirs(folder2)

        with open(file1, "w") as f:
            f.write("some text")

        with open(file2, "w") as f:
            f.write("some more text")

        dst = os.path.join(self.test_folder.name, "folder_dst")
        output = rsync.rsync(folder1, dst, ["-a"])

        files = ["file1.txt", "file2.txt"]
        files = [os.path.join(fd, fl) for fl, fd in zip(files, [folder1, folder2])]
        match, mismatch, errors = filecmp.cmpfiles(folder1, dst, files)
        self.assertEqual(files, match)
        self.assertEqual(output.returncode, 0)

    def test_rsync_folder_contents(self):
        
        folder1c = os.path.join(self.test_folder.name, "folder1c")
        file1 = os.path.join(folder1c, "file1.txt")
        
        folder2c = os.path.join(folder1c, "folder2c")
        file2 = os.path.join(folder2c, "file2.txt")
        
        os.makedirs(folder1c)
        os.makedirs(folder2c)

        with open(file1, "w") as f:
            f.write("some text")

        with open(file2, "w") as f:
            f.write("some more text")

        dst = os.path.join(self.test_folder.name, "folder_dst")
        os.makedirs(dst)

        output = rsync.rsync(folder1c + os.path.sep, dst + os.path.sep, ["-a"])
        files = [
            os.path.join(folder1c, "file1.txt"),
            os.path.join(folder1c, folder2c, "file2.txt")
        ]

        match, mismatch, errors = filecmp.cmpfiles(folder1c, dst, files)
        self.assertEqual(files, match)
        self.assertEqual(output.returncode, 0)

    def test_rsync_check(self):

        expect = shutil.which("rsync") is not None
        output = rsync.is_rsync_installed()
        self.assertEqual(expect, output)
