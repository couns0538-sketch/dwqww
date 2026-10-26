#!/usr/bin/env python3
"""Pure state/float-word model only; it does not compile or execute Forge."""
import argparse
from dataclasses import dataclass, field
import random
import struct
import unittest


def f32(value):
    return struct.unpack('<f', struct.pack('<f', value))[0]


def words(values):
    return struct.pack('<' + 'f' * len(values), *values)


@dataclass
class Frame:
    values: tuple = ()
    valid: bool = False
    alias: object = None
    dirty: tuple = ()
    score: int = 0
    phase: int = 0


class Stack:
    def __init__(self, alias_on, clear_alias=True, lanes=32):
        self.alias_on = alias_on
        self.clear_alias = clear_alias
        self.lanes = lanes
        self.frames = [Frame() for _ in range(24)]
        self.updates = self.avoided = self.alias_hits = 0
        self.reset()

    def reset(self):
        for item in self.frames:
            item.valid = False
            item.alias = None
        self.frames[0] = Frame(tuple(f32((i - 9) / 4096) for i in range(self.lanes)), True)

    def edge(self, parent, dirty):
        child = self.frames[parent + 1]
        child.dirty = dirty
        child.valid = False
        if self.clear_alias:
            child.alias = None

    def owner(self, index):
        item = self.frames[index]
        return index if item.valid else item.alias if self.alias_on else None

    def evaluate(self, index):
        owner = self.owner(index)
        if owner is not None:
            self.alias_hits += owner != index
            return self.frames[owner]
        start = index - 1
        while start >= 0 and self.owner(start) is None:
            start -= 1
        if start < 0:
            raise AssertionError('model root must remain physically computed')
        owner = self.owner(start)
        for step in range(start + 1, index + 1):
            item, source = self.frames[step], self.frames[owner]
            assert source.valid and owner < step
            if self.alias_on and not item.dirty:
                item.alias = owner
                self.avoided += 1
            else:
                values = source.values
                for delta in item.dirty:
                    values = tuple(f32(value + f32(delta * (lane + 1) / 4096))
                                   for lane, value in enumerate(values))
                item.values = values
                item.score = source.score + sum(item.dirty)
                item.phase = source.phase + len(item.dirty)
                item.valid = True
                item.alias = None
                self.updates += 1
                owner = step
        return self.frames[owner]


class AliasModelTests(unittest.TestCase):
    requested_mode = True

    def same(self, left, right, index):
        a, b = left.evaluate(index), right.evaluate(index)
        self.assertEqual(words(a.values), words(b.values))
        self.assertEqual((a.score, a.phase), (b.score, b.phase))

    def test_zero_dirty_copies_are_actually_elided(self):
        reference, candidate = Stack(False, lanes=512), Stack(self.requested_mode, lanes=512)
        original = words(reference.frames[0].values)
        for depth in range(7):
            reference.edge(depth, ())
            candidate.edge(depth, ())
        self.same(reference, candidate, 7)
        self.assertEqual(candidate.avoided, 7)
        self.assertEqual(candidate.updates, 0)
        self.assertEqual(reference.updates, 7)
        self.assertEqual(words(candidate.frames[0].values), original)
        for depth in range(1, 8):
            self.assertFalse(candidate.frames[depth].valid)
            self.assertEqual(candidate.frames[depth].alias, 0)

    def test_null_then_real_edge_and_repeated_eval(self):
        reference, candidate = Stack(False), Stack(True)
        for depth, dirty in enumerate([(), (), (-9, 7), (), (-2, -3, 6), ()]):
            reference.edge(depth, dirty)
            candidate.edge(depth, dirty)
        self.same(reference, candidate, 6)
        old = (candidate.updates, candidate.avoided)
        self.same(reference, candidate, 6)
        self.assertEqual(old, (candidate.updates, candidate.avoided))
        self.assertEqual(candidate.frames[6].alias, 5)
        self.assertTrue(candidate.frames[5].valid)

    def test_sibling_invalidation_clears_stale_alias(self):
        reference, candidate = Stack(False), Stack(True)
        for model in (reference, candidate):
            model.edge(0, ())
            model.evaluate(1)
            model.edge(0, (-3, 8))
        self.assertIsNone(candidate.frames[1].alias)
        self.same(reference, candidate, 1)

    def test_missing_invalidation_negative_control_is_detected(self):
        reference, broken = Stack(False), Stack(True, clear_alias=False)
        for model in (reference, broken):
            model.edge(0, ())
            model.evaluate(1)
            model.edge(0, (-3, 8))
        a, b = reference.evaluate(1), broken.evaluate(1)
        self.assertNotEqual(words(a.values), words(b.values))

    def test_reset_clears_all_aliases_and_stale_descendants(self):
        model = Stack(True)
        for depth in range(9):
            model.edge(depth, ())
        model.evaluate(9)
        model.reset()
        self.assertTrue(model.frames[0].valid)
        self.assertTrue(all(not f.valid and f.alias is None for f in model.frames[1:]))

    def test_deterministic_depth_first_reuse_matches_copy_baseline(self):
        reference, candidate = Stack(False), Stack(True)
        rng = random.Random(120026)
        depth = 0
        for operation in range(2400):
            if depth and (depth == 20 or rng.randrange(4) == 0):
                depth = rng.randrange(depth)
            else:
                dirty = () if rng.randrange(3) == 0 else tuple(rng.randrange(-15, 16) for _ in range(rng.randrange(2, 5)))
                reference.edge(depth, dirty)
                candidate.edge(depth, dirty)
                depth += 1
            if operation % 3 == 0 or rng.randrange(4) == 0:
                self.same(reference, candidate, depth)
            for index in range(depth + 1):
                owner = candidate.owner(index)
                if owner is not None:
                    self.assertTrue(candidate.frames[owner].valid)
                    self.assertLessEqual(owner, index)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--baseline-copy-control', action='store_true')
    args = parser.parse_args()
    AliasModelTests.requested_mode = not args.baseline_copy_control
    unittest.main(argv=['model'], verbosity=2)
