import unittest
import random
from snappy import rotate as rt


class TestRotateFwd(unittest.TestCase):

    def test_rotate_fwd_infinite_list(self):

        size = random.randint(1, 100)

        ll = list(map(str, range(0, size)))
        x = "aaaa"
        
        output = rt.rotate_fwd(x, ll, 0)
        expect = [x] + ll
        self.assertEqual(output, expect)

    def test_rotate_fwd_neg_max(self):

        size = random.randint(1, 100)

        ll = list(map(str, range(0, size)))
        x = "aaaa"
        
        output = rt.rotate_fwd(x, ll, -size)
        expect = [x] + ll
        self.assertEqual(output, expect)

    def test_rotate_fwd_fixed_size(self):

        ll = ["a", "b", "c", "d", "e"]
        x = "aaaa"
        size = random.randint(1, len(ll) - 1)
        
        output = rt.rotate_fwd(x, ll, size)
        expect = [x] + ll[:size]
        expect[-1] += rt.tmp_suffix()

        self.assertEqual(output, expect)

    def test_rotate_fwd_fits_all(self):

        ll = ["a", "b", "c"]
        x = "aaaa"
        size = len(ll) + random.randint(1, 10)

        output = rt.rotate_fwd(x, ll, size)
        expect = [x] + ll
        self.assertEqual(expect, output)


class TestRotateBkd(unittest.TestCase):

    def test_rotate_bkd_empty(self):

        ll = []
        output = rt.rotate_bkd(ll)
        expect = []
        self.assertEqual(expect, output)
    
    def test_rotate_bkd_not_full(self):

        # -------------------------------------
        # if list last element does not
        # has the temp suffix, it is not full
        # -------------------------------------

        ll = ["a", "b", "c", "d"]
        output = rt.rotate_bkd(ll)
        expect = ll
        self.assertEqual(expect, output)

        ll[-1] += rt.tmp_suffix()
        output = rt.rotate_bkd(ll)
        self.assertNotEqual(ll, output)

    def test_rotate_bkd_is_full(self):

        # ----------------------------------
        # if list is full, the last element
        # must have the suffix
        # ----------------------------------

        ll = ["a", "b", "c", "d", "e"]
        ll[-1] += rt.tmp_suffix()
        output = rt.rotate_bkd(ll)
        expect = ll
        expect[-1] = expect[-1].replace(rt.tmp_suffix(), "")
        
        self.assertEqual(expect, output)
