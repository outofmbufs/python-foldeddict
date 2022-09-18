# FoldedDict python MutableMapping

A FoldedDict is a MutableMapping (like a dict) where keys with equal
`canonicalkey()` results refer to the same entry in the mapping.
The default `canonicalkey()` method use `str.lower()` to make keys
case-insensitive.

## Example

```
    d = FoldedDict()
    d['Clown'] = 'Bozo'
    d['clown'] = 'Krusty'
    print(d['CLOWN'])           # prints Krusty
    for k in d.keys():
       print(k)                 # prints Clown
```

## Equivalence of Keys and Preserved Keys

If keys `k1, k2, .. kN` form an equivalence set of keys that all
convert to the same canonical key:

```
    canonicalkey(k1) == canonicalkey(k2) == .. == canonicalkey(kN)
```

this code preserves the first key seen for any given equivalence set.
In the Example above, 'Clown' is the preserved key in that code sequence.
Each preserved key has no semantic significance; however it is the key
that will be returned by `.keys()` and other such methods.

The base `canonicalkey()` method case-folds strings together
according to `str.lower()`. For example:

```
   d = FoldedDict()
   d['XYZ'] = object()
   d['Xyz'] == d['xyz'] == d['XYZ']      # True
```

A subclass can, of course, override `canonicalkey()` for other equivalencies.

## Methods
All methods of a MutableMapping are supported.

One additional method, `canonicalkey()` defines the equivalence sets on
keys; it is not normally invoked outside of the class but is implicitly
used to fold entries together. Note that (by default) the canonical key
and the preserved key are not necessarily the same.

```
    d = FoldedDict()
    c = d.canonicalkey(k)
```    

## Initialization
When creating a FoldedDict the same arguments are accepted as by `dict()`:

```
    d = FoldedDict(Clown='Bozo')
    print(d['CLOWN'])              # prints Bozo
```

Overspecified initializations (a single call to FoldedDict() with
arguments that result in one entry being initialized more than once
because of folding) have implementation-specific results.


## LICENSE
MIT. See source code.
