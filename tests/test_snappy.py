import os
import stat
import unittest
import tempfile
import filecmp
import unittest.mock
from snappy import snappy as snp


class TestFolders(unittest.TestCase):

    def setUp(self) -> None:
        
        self.folder = tempfile.TemporaryDirectory()
        self.folders = ["a", "b", "c", "e", "g"]
        self.files = ["d", "f"]

        for f in self.folders:
            os.mkdir(os.path.join(self.folder.name, f))

        for f in self.files:
            with open(os.path.join(self.folder.name, f"{f}.txt"), "w") as ff:
                ff.write(f"this the {f.upper()} file")
    
    def tearDown(self) -> None:
        self.folder.cleanup()

    def test_get_backup_folders(self):

        output = snp.get_backup_folders(self.folder.name)
        expect = [os.path.join(self.folder.name, e) for e in self.folders]
        self.assertEqual(expect, output)

    def test_clean_backups_nothing_to_clean_neg_n(self):

        snp.clean_backups(self.folder.name, -1)
        for f in self.folders:
            self.assertTrue(os.path.exists(os.path.join(self.folder.name, f)))

    def test_clean_backups_nothing_to_clean_zero_n(self):

        snp.clean_backups(self.folder.name, 0)
        for f in self.folders:
            self.assertTrue(os.path.exists(os.path.join(self.folder.name, f)))

    def test_clean_backups_nothing_to_clean_large_n(self):

        snp.clean_backups(self.folder.name, 1000)
        for f in self.folders:
            self.assertTrue(os.path.exists(os.path.join(self.folder.name, f)))

    def test_clean_backups_delete_old(self):

        size = 3
        snp.clean_backups(self.folder.name, size)

        fl = sorted(self.folders)
        fl.reverse()

        for f in fl[:size]:
            self.assertTrue(os.path.exists(os.path.join(self.folder.name, f)))

        for f in fl[size]:
            self.assertFalse(os.path.exists(os.path.join(self.folder.name, f)))

    def test_clean_backups_delete_n_is_one(self):

        size = 1
        snp.clean_backups(self.folder.name, size)

        fl = sorted(self.folders)
        fl.reverse()

        for f in fl[:size]:
            self.assertTrue(os.path.exists(os.path.join(self.folder.name, f)))

        for f in fl[size]:
            self.assertFalse(os.path.exists(os.path.join(self.folder.name, f)))

    def test_list_non_readable_empty(self):

        file = "a.txt"
        with tempfile.TemporaryDirectory(dir = ".") as folder:
            file = os.path.join(folder, file)
            with open(file, "w") as f:
                f.write("this is a file")

            lst = snp._list_non_readable_files(folder)

        self.assertEqual(len(lst), 0)
        self.assertEqual(lst, [])

    @unittest.mock.patch("snappy.cmd.find_non_readable")
    def test_non_reabable_error(self, mock):
        file = "error_file.txt"
        mock.side_effect = Exception("NOT RUN")
        with tempfile.TemporaryDirectory(dir = ".") as folder:
            file = os.path.join(folder, file)
            with open(file, "w") as f:
                f.write("this is an error")

            lst = snp._list_non_readable_files(folder)
            self.assertEqual(len(lst), 0)
            self.assertEqual(lst, [])

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

            lst = snp._list_non_readable_files(folder)

            self.assertEqual(len(lst), 2)
            for file in files[:2]:
                file = os.path.join(folder, file)
                file = os.path.abspath(file)
                file = os.path.expanduser(file)
                self.assertIn(file, lst)


class TestCreateSnapshot(unittest.TestCase):

    @staticmethod
    def create_test_folders(folder_name):
        
        path = os.path.join(folder_name, "A")
        os.makedirs(path)
        with open(os.path.join(path, "a.txt"), "w") as f:
            f.write("This is file A")

        path = os.path.join(folder_name, "B")
        os.makedirs(path)
        with open(os.path.join(path, "b.txt"), "w") as f:
            f.write("This is file B")

        path = os.path.join(folder_name, "B", "C")
        os.makedirs(path)
        with open(os.path.join(path, "c.txt"), "w") as f:
            f.write("This is file C")

    def setUp(self) -> None:
        self.folder = tempfile.TemporaryDirectory()
        self.sources = ["A", "B"]
        self.create_test_folders(self.folder.name)

    def tearDown(self) -> None:
        self.folder.cleanup()

    def test_destination_no_trailing_slash(self):

        src = [os.path.join(self.folder.name, s) for s in self.sources]
        files = ["A/a.txt", "B/b.txt", "B/C/c.txt"]

        with tempfile.TemporaryDirectory() as dst:
            snp.create_snapshot(src, dst)
            match, mismatch, errors = filecmp.cmpfiles(self.folder.name, dst, files)

        self.assertEqual(match, files)

    def test_destination_with_trailing_slash(self):

        src = [os.path.join(self.folder.name, s) for s in self.sources]
        files = ["A/a.txt", "B/b.txt", "B/C/c.txt"]

        with tempfile.TemporaryDirectory() as dst:

            ndst = os.path.join(dst, "new")
            os.makedirs(ndst)

            ndst += os.path.sep
            snp.create_snapshot(src, ndst)
            match, mismatch, errors = filecmp.cmpfiles(self.folder.name, ndst, files)

        self.assertEqual(match, files)

    def test_invalid_source(self):

        src = [os.path.join(self.folder.name, s) for s in self.sources]
        src += [os.path.join(self.folder.name, "ThisFolderIsNotThere")]

        with tempfile.TemporaryDirectory() as dst:
            with self.assertRaises(FileNotFoundError):
                snp.create_snapshot(src, dst)
        
    def test_expand_tilde(self):

        files = ["A/a.txt", "B/b.txt", "B/C/c.txt"]
        with tempfile.TemporaryDirectory(dir = os.environ["HOME"]) as src:
            
            self.create_test_folders(src)
            folders = os.listdir(src)
            origin = [os.path.join("~", os.path.basename(src), f) for f in folders]
            with tempfile.TemporaryDirectory() as dst:
                snp.create_snapshot(origin, dst)
                match, mismatch, errors = filecmp.cmpfiles(self.folder.name, dst, files)

        self.assertEqual(match, files)
