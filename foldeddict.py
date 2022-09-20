# MIT License
#
# Copyright (c) 2022 Neil Webber
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

from collections.abc import MutableMapping


# A FoldedDict is a MutableMapping (like a dict) where keys with equal
# canonicalkey() results refer to the same entry in the mapping.
#
# If keys k1, k2, .. kN form an equivalence set of keys that all
# convert to the same canonicalkey:
#
#    canonicalkey(k1) == canonicalkey(k2) == .. == canonicalkey(kN)
#
# this code preserves the first key seen for any given equivalence set
# (e.g., 'k1' in the above example) and calls it the 'preservedkey'.
# The preservedkey has no semantic significance; however it is the key
# that will be returned by .keys() and other such methods.
#
# The base canonicalkey() method case-folds strings together
# according to str.lower(). So, for example, d['Xyz'] and d['xyz']
# refer to the same mapping entry. This method can, of course, be
# overridden to allow for other types of key equivalences.
#
# EXAMPLE:
#    d = FoldedDict()
#    d['Clown'] = 'Bozo'
#    d['clown'] = 'Krusty'
#    print(d['CLOWN'])
#
# prints Krusty and
#
#    for k in d.keys():
#       print(k)
#
# prints Clown  ... because 'Clown' is the preservedkey.
#
# The __init__ method accepts all of the same argument forms as dict():
#
#    d = FoldedDict(Clown='Bozo')
#    print(d['CLOWN'])
#
# prints Bozo
#
class FoldedDict(MutableMapping):
    """MutableMapping where 'equivalent' keys refer to the same entry"""

    # Override this to create other types of key equivalence.
    def canonicalkey(self, key):
        """Return the 'canonical' representation for the given key."""
        try:
            return key.lower()
        except AttributeError:      # i.e., it's not a string
            return key

    def __init__(self, *args, **kwargs):
        self.__preserves = {}
        self.__dict = {}

        # To support *every* form of dict() arguments... use dict()!
        #    ... i.e., make a temporary dictionary from the arguments
        #        and then initialize self by iterating those results.
        #
        # NOTE: The semantics of (ill-advised) initializations with
        #       multiple equivalent keys (i.e., that will fold together
        #       in step 2) are 'undefined' ... but work this way:
        for k, v in dict(*args, **kwargs).items():
            self[k] = v

    def __getitem__(self, key):
        return self.__dict[self.__preserves[self.canonicalkey(key)]]

    def __setitem__(self, key, val):
        self.__dict[self._savekey(key)] = val

    def __delitem__(self, key):
        canon = self.canonicalkey(key)
        p = self.__preserves[canon]     # KeyError if key was no good
        del self.__preserves[canon]
        del self.__dict[p]

    def __iter__(self):
        return self.__dict.__iter__()

    def __len__(self):
        return self.__dict.__len__()

    def __eq__(self, other):
        # if comparing two FoldedDicts canonicalize both sets of keys
        # and compare that way. Otherwise ... best of luck with the
        # underlying == method.
        try:
            oc = {other.canonicalkey(k): v for k, v in other.items()}
            return {self.canonicalkey(k): v for k, v in self.items()} == oc
        except AttributeError:
            return self.__dict == other

    def __repr__(self):
        return f"{self.__class__.__name__}({self.__dict})"

    def copy(self):
        """Shallow copy"""
        # MutableMapping doesn't provide this?? huh.
        return self.__class__(self)

    def _savekey(self, key):
        """Return the preservedkey if it exists, or set it (and return it)."""
        canon = self.canonicalkey(key)
        try:
            return self.__preserves[canon]
        except KeyError:
            self.__preserves[canon] = key
        return key


# this subclass uses the canonicalkey() as the preservedkey. This
# is potentially quite useful if the keys need to be used elsewhere
# (e.g., possibly to create other, regular, dict() objects) and it
# would be important for the preservedkey value to be predictable/canonical
# instead of preserving whatever form was first seen for each key.
class CanonFolder(FoldedDict):
    def _savekey(self, key):
        return super()._savekey(self.canonicalkey(key))


# In this variant, the most recent key used to SET an element is preserved.
class DKFoldedDict(FoldedDict):
    def _savekey(self, key):
        if key in self:
            del self[key]     # so the set will preserve THIS key
        return super()._savekey(key)


# This is probably not useful but shows an example alternate canonicalkey()
class StrippedWhitespaceDict(FoldedDict):
    # Dictionary indexed by strings with spaces removed.
    # Thus ['xy'] and b['x y'] would map to the same thing.
    # Note that this one is case-sensitive but obviously could
    # be modified to include a lower() mapping as well.
    def canonicalkey(self, key):
        try:
            return ''.join(key.split())
        except TypeError:
            return key


# another questionably not-useful example, just as an example
class SortedKeyDict(FoldedDict):
    # Dictionary where the keys are expected to be sortable iterables and
    # are sorted ... thus d[(1,2,3)] and d[(3,2,1)] are the same item.
    # CAUTION: STRING KEYS ARE ITERABLES AND GET SORTED so, for example:
    #     d['abc'] and d['bac'] would be the same item here.
    def canonicalkey(self, key):
        try:
            return tuple(sorted(key))
        except TypeError:
            return key


if __name__ == "__main__":
    import unittest

    class TestMethods(unittest.TestCase):
        def test_basic1(self):
            """basic test of key equivalence."""

            # NOTE: test taken from the comment example at top of file
            d = FoldedDict()
            d['Clown'] = 'Bozo'
            d['clown'] = 'Krusty'
            self.assertEqual(d['CLOWN'], 'Krusty')

        def test_basic2(self):
            """basic test of preservedkey functionality."""
            # NOTE: test taken from the coment example at top of file
            d = FoldedDict()
            d['Clown'] = 'Bozo'      # 'Clown' is the preservedkey
            d['clown'] = 'Krusty'    # this shouldn't change that
            self.assertEqual(list(d.keys()), ['Clown'])

        def test_cf1(self):
            """Like test_basic1 but with CanonFolder."""
            d = CanonFolder()
            d['Clown'] = 'Bozo'
            d['clown'] = 'Krusty'
            self.assertEqual(d['CLOWN'], 'Krusty')

        def test_cf2(self):
            """Adapted from test_basic2 but with CanonFolder."""
            d = CanonFolder()
            d['Clown'] = 'Bozo'      # the canonical/preserved will be 'clown'
            d['CLOWN'] = 'Krusty'    # this shouldn't change that
            self.assertEqual(d['clown'], 'Krusty')
            self.assertEqual(d['cLOwn'], 'Krusty')
            self.assertEqual(d['cLoWn'], 'Krusty')
            self.assertEqual(list(d.keys()), ['clown'])

        def test_keyerror(self):
            d = FoldedDict()
            with self.assertRaises(KeyError):
                x = d['banana']

            # Now make sure the preservedkey wasn't polluted
            d['baNANA'] = 42    # 'baNANA' should be the preservedkey
            self.assertEqual(list(d.keys()), ['baNANA'])

        def test_del(self):
            """test del"""
            d = FoldedDict(foo='bar')
            del d['foo']
            with self.assertRaises(KeyError):
                _ = d['foo']

        def test_deltwice(self):
            """more del test; a failed del should not pollute preservedkey."""
            d = FoldedDict(banana='gram')
            del d['BANANA']
            with self.assertRaises(KeyError):
                del d['Banana']

            # the first, naive, version of del would result in 'Foo'
            # being left behind as a preservedkey even though the second
            # del failed... check for that by establishing what should
            # be a new preservedkey and making sure it is right.
            d['baNANA'] = 42
            self.assertEqual(list(d.keys()), ['baNANA'])

        def test_equals(self):
            d1 = FoldedDict(banana='gram', clown='Bozo')
            d2 = FoldedDict(Banana='gram', CLOWN='Bozo')
            self.assertTrue(d1 == d2)

        def test_equalsother(self):
            d1 = FoldedDict(banana='gram', clown='Bozo')
            d2 = dict(banana='gram', clown='Bozo')
            self.assertTrue(d1 == d2)

        def test_notequals(self):
            d1 = FoldedDict(banana='gram', clown='Bozo')
            d2 = FoldedDict(Banana='GRAM', CLOWN='bozo')
            self.assertTrue(d1 != d2)

        def test_init(self):
            """test proper folding in __init__ kwargs"""
            # make sure keys that are equivalent get folded
            # even if they are specified this way:
            d = FoldedDict(banana=1, Banana=2)
            self.assertEqual(len(d), 1)
            self.assertEqual(d['BANANA'], 2)
            self.assertEqual(list(d.keys()), ['banana'])

        def test_init2(self):
            """More tests of init in all its forms."""
            # NOTE: Test taken from the dict() python documentation
            a = FoldedDict(one=1, two=2, three=3)
            b = {'one': 1, 'two': 2, 'three': 3}
            c = FoldedDict(zip(['one', 'two', 'three'], [1, 2, 3]))
            d = FoldedDict([('two', 2), ('one', 1), ('three', 3)])
            e = FoldedDict({'three': 3, 'one': 1, 'two': 2})
            f = FoldedDict({'one': 1, 'three': 3}, two=2)
            self.assertTrue(a == b == c == d == e == f)

            # and some variations just for grins
            xa = FoldedDict(onE=1, Two=2, thRee=3)
            # note that the {} test case isn't valid so no xb
            xc = FoldedDict(zip(['ONE', 'two', 'three'], [1, 2, 3]))
            xd = FoldedDict([('tWO', 2), ('oNE', 1), ('THReE', 3)])
            xe = FoldedDict({'tHRee': 3, 'onE': 1, 'TwO': 2})
            xf = FoldedDict({'one': 1, 'three': 3}, TWO=2)
            self.assertTrue(xa == xc == xd == xe == xf == a)

        def test_canonfolder(self):
            # the test-variations from init2 but now because of CanonFolder
            # semantics the xb test will also work.
            xa = CanonFolder(onE=1, Two=2, thRee=3)
            xb = {'one': 1, 'two': 2, 'three': 3}
            xc = CanonFolder(zip(['ONE', 'two', 'three'], [1, 2, 3]))
            xd = CanonFolder([('tWO', 2), ('oNE', 1), ('THReE', 3)])
            xe = CanonFolder({'tHRee': 3, 'onE': 1, 'TwO': 2})
            xf = CanonFolder({'one': 1, 'three': 3}, TWO=2)
            self.assertTrue(xa == xb == xc == xd == xe == xf)

        def test_notstrings(self):
            """test keys that are not strings"""
            d = FoldedDict()
            d[1] = 1
            d[None] = None
            d[(1, 2)] = (1, 2)
            self.assertEqual(len(d), 3)
            for k, v in d.items():
                self.assertEqual(k, v)

        def test_SWD(self):
            d = StrippedWhitespaceDict(theclown='Bozo')
            self.assertEqual(d['   the      clown  '], 'Bozo')

        def test_SKD(self):
            d = SortedKeyDict()
            d[(1, 2, 3)] = 'foo'
            d[(3, 2, 1)] = 'bar'
            self.assertEqual(len(d), 1)
            self.assertEqual(d[(2, 3, 1)], 'bar')

        def test_DK1(self):
            # test the dynamic key where the preserved key is always
            # whatever key was used last to SET a value.
            d = DKFoldedDict()
            d['cloWN'] = 'boZO'
            self.assertEqual(d['clown'], 'boZO')
            self.assertEqual(list(d.keys()), ['cloWN'])

            d['CLOwn'] = 'BOzo'
            self.assertEqual(d['clown'], 'BOzo')
            self.assertEqual(list(d.keys()), ['CLOwn'])

    unittest.main()
