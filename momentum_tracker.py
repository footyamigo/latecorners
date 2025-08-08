#!/usr/bin/env python3
from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from typing import Deque, Dict, Optional, Tuple


@dataclass
class TeamSnapshot:
    minute: int
    shots_on_target: int
    shots_off_target: int
    dangerous_attacks: int
    possession: int  # percentage 0-100


class MomentumTracker:
    """
    Tracks rolling 10-minute attacking momentum per fixture using live, cumulative stats.

    Momentum formula (per team, last 10 minutes):
      +12 points per shot on target
      + 8 points per shot off target
      + 2 points per dangerous attack
      + 1 point per 5% average possession
    """

    def __init__(self, window_minutes: int = 10):
        self.window_minutes = window_minutes
        # fixture_id -> { 'home': deque[TeamSnapshot], 'away': deque[TeamSnapshot] }
        self._history: Dict[int, Dict[str, Deque[TeamSnapshot]]] = {}

    def _get_fixture_deques(self, fixture_id: int) -> Tuple[Deque[TeamSnapshot], Deque[TeamSnapshot]]:
        buckets = self._history.setdefault(
            fixture_id,
            {
                'home': deque(),
                'away': deque(),
            },
        )
        return buckets['home'], buckets['away']

    def add_snapshot(self, fixture_id: int, minute: int, home: Dict[str, int], away: Dict[str, int]) -> None:
        """
        Add a snapshot for both teams. Ignores duplicate minutes, clears on minute regression.
        Required keys in team dicts: shots_on_target, shots_off_target, dangerous_attacks, possession.
        """
        home_q, away_q = self._get_fixture_deques(fixture_id)

        def _append(queue: Deque[TeamSnapshot], stats: Dict[str, int]) -> None:
            # Handle minute regression (HT resets, etc.) by clearing
            if queue and minute < queue[-1].minute:
                queue.clear()
            # Ignore duplicate minute
            if queue and minute == queue[-1].minute:
                return
            queue.append(
                TeamSnapshot(
                    minute=minute,
                    shots_on_target=int(stats.get('shots_on_target', 0) or 0),
                    shots_off_target=int(stats.get('shots_off_target', 0) or 0),
                    dangerous_attacks=int(stats.get('dangerous_attacks', 0) or 0),
                    possession=int(stats.get('possession', 0) or 0),
                )
            )

        _append(home_q, home)
        _append(away_q, away)

        self._prune(home_q, minute)
        self._prune(away_q, minute)

    def _prune(self, queue: Deque[TeamSnapshot], now_minute: int) -> None:
        cutoff = max(0, now_minute - self.window_minutes)
        while queue and queue[0].minute < cutoff:
            queue.popleft()

    def _compute_team(self, queue: Deque[TeamSnapshot]) -> Dict[str, int]:
        if not queue:
            return {
                'total': 0,
                'on_target_points': 0,
                'off_target_points': 0,
                'dangerous_points': 0,
                'possession_points': 0,
                'window_covered': 0,
            }

        first = queue[0]
        last = queue[-1]
        window_covered = last.minute - first.minute

        # Time-decayed diffs of cumulative stats across last 10 minutes
        # Recent minutes count more: weights for last 4 minutes = 4,3,2,1; older minutes = 1
        weights = {0: 4, 1: 3, 2: 2, 3: 1}

        def diff(a: int, b: int) -> int:
            return max(0, a - b)

        sot = diff(last.shots_on_target, first.shots_on_target)
        soff = diff(last.shots_off_target, first.shots_off_target)
        dang = diff(last.dangerous_attacks, first.dangerous_attacks)

        # If enough snapshots exist, apply extra weight to most recent minutes by estimating
        # per-minute increments from the deque and re-weighting their sum.
        if len(queue) >= 2:
            # Build minute-indexed map from snapshots
            by_minute = {s.minute: s for s in queue}
            recent_sot = recent_soff = recent_dang = 0
            used_weight = 0
            for i in range(4):
                m = last.minute - i
                prev = by_minute.get(m - 1)
                cur = by_minute.get(m)
                if prev and cur:
                    w = weights.get(i, 1)
                    recent_sot += w * diff(cur.shots_on_target, prev.shots_on_target)
                    recent_soff += w * diff(cur.shots_off_target, prev.shots_off_target)
                    recent_dang += w * diff(cur.dangerous_attacks, prev.dangerous_attacks)
                    used_weight += w
            # Blend: combine weighted recent increments with remaining older increments (weight 1)
            # Older part = total diff minus the unweighted recent increments
            unweighted_recent_sot = 0
            unweighted_recent_soff = 0
            unweighted_recent_dang = 0
            for i in range(4):
                m = last.minute - i
                prev = by_minute.get(m - 1)
                cur = by_minute.get(m)
                if prev and cur:
                    unweighted_recent_sot += diff(cur.shots_on_target, prev.shots_on_target)
                    unweighted_recent_soff += diff(cur.shots_off_target, prev.shots_off_target)
                    unweighted_recent_dang += diff(cur.dangerous_attacks, prev.dangerous_attacks)

            older_sot = max(0, sot - unweighted_recent_sot)
            older_soff = max(0, soff - unweighted_recent_soff)
            older_dang = max(0, dang - unweighted_recent_dang)

            # Recompose: weighted recent + older (weight 1)
            sot = recent_sot + older_sot
            soff = recent_soff + older_soff
            dang = recent_dang + older_dang

        # Average possession across snapshots
        if len(queue) == 1:
            avg_pos = last.possession
        else:
            avg_pos = sum(s.possession for s in queue) // len(queue)

        # Points: decay-adjusted counts; possession only for excess over 50%
        on_target_points = 12 * sot
        off_target_points = 8 * soff
        dangerous_points = 2 * dang
        excess_pos = max(0, avg_pos - 50)
        possession_points = (excess_pos // 5)

        total = on_target_points + off_target_points + dangerous_points + possession_points

        return {
            'total': total,
            'on_target_points': on_target_points,
            'off_target_points': off_target_points,
            'dangerous_points': dangerous_points,
            'possession_points': possession_points,
            'window_covered': window_covered,
        }

    def compute_scores(self, fixture_id: int) -> Dict[str, Dict[str, int]]:
        home_q, away_q = self._get_fixture_deques(fixture_id)
        return {
            'home': self._compute_team(home_q),
            'away': self._compute_team(away_q),
        }

