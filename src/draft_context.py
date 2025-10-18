"""Shared draft context helper used by materialization and runtime RAG code.

This centralizes the small but important logic that describes draft tiers
based on a player's fantasy rank, FPPM and position. The function supports
an optional league_size parameter; when provided the output becomes
league-size-aware (used by the RAG runtime). When omitted, a fixed-bucket
behavior is used (compatible with the existing materialize script).

Keep this file small and dependency-free so it can be imported by scripts
that run in lightweight environments (Streamlit Cloud materialization).
"""
from typing import Optional


def build_draft_context(rank: int, fppm: float, position: str = "", league_size: Optional[int] = None) -> str:
    """Return a short, human readable draft-context string for a player.

    Args:
        rank: overall fantasy rank (lower is better). Use 999 for unknown/late.
        fppm: fantasy points per minute (efficiency)
        position: player position string (e.g., 'PG', 'C')
        league_size: optional league size (teams). When provided the result
            will be league-size-aware (round calculations) otherwise a fixed
            bucket logic is used.
    """
    # Fallback rank sentinel
    if rank is None:
        rank = 999
    try:
        rank = int(rank)
    except Exception:
        rank = 999

    # If league_size provided prefer league-aware rules (RAG runtime)
    if league_size:
        if rank == 999:
            return "Late round sleeper or waiver wire option."

        draft_round = 1 if rank <= league_size else ((rank - 1) // league_size) + 1

        if rank <= league_size:
            tier = "ELITE FIRST ROUND PICK"
            desc = f"Top {rank} fantasy player. Round 1, pick #{rank}. Premium first round selection."
            if rank <= 3:
                desc += " Consensus top 3 pick. Absolute elite tier."
            elif rank <= max(6, league_size // 3):
                desc += " Core first round target."
        elif rank <= league_size * 2:
            tier = "SECOND ROUND VALUE"
            pick_in_round = rank - league_size
            desc = f"Ranked #{rank}. Round 2, pick #{pick_in_round}. Excellent second round value. Solid fantasy starter."
            if position and position.upper() in ['C', 'PF']:
                desc += f" Strong {position} option for positional scarcity."
        elif rank <= league_size * 3:
            tier = "THIRD ROUND PICK"
            pick_in_round = rank - (league_size * 2)
            desc = f"Ranked #{rank}. Round 3, pick #{pick_in_round}. Great third round target. Quality starter material."
        elif rank <= league_size * 5:
            tier = "EARLY MID-ROUND"
            desc = f"Ranked #{rank}. Round {draft_round} value. Quality depth piece or flex starter."
        elif rank <= league_size * 8:
            tier = "MID-ROUND PICK"
            desc = f"Ranked #{rank}. Round {draft_round}. Solid bench depth, streaming upside, or late sleeper value."
        elif rank <= league_size * 12:
            tier = "LATE ROUND SLEEPER"
            desc = f"Ranked #{rank}. Round {draft_round}. Late round sleeper or waiver wire candidate. Deep league value."
        else:
            tier = "DEEP SLEEPER"
            desc = f"Ranked #{rank}. Waiver wire target. Speculative streaming add or injury replacement."
    else:
        # Fixed buckets (compatible with materialize script)
        if rank == 999:
            return "Late round sleeper or waiver wire option."
        if rank <= 10:
            tier = "ELITE FIRST ROUND PICK"
            desc = f"Top {rank} fantasy player. Should go in picks 1-10 of any draft. Premium first round selection."
            if rank <= 3:
                desc += " Consensus top 3 pick. Absolute elite tier."
            elif rank <= 6:
                desc += " Core first round target."
        elif rank <= 30:
            tier = "FIRST ROUND VALUE"
            desc = f"Ranked #{rank}. Excellent first round pick around picks {max(1, rank-5)} to {rank+5}. Solid fantasy starter."
            if position and position.upper() in ['C', 'PF']:
                desc += f" Strong {position} option for positional scarcity."
        elif rank <= 50:
            tier = "EARLY MID-ROUND"
            desc = f"Ranked #{rank}. Great 2nd/3rd round value around picks {max(1, rank-5)} to {rank+5}. Quality starter material."
        elif rank <= 100:
            tier = "MID-ROUND PICK"
            desc = f"Ranked #{rank}. Solid middle round option around picks {max(1, rank-10)} to {rank+10}. Good bench depth or flex starter."
        elif rank <= 200:
            tier = "LATE ROUND VALUE"
            desc = f"Ranked #{rank}. Late round pick around {max(1, rank-15)} to {rank+15}. Deep league option or streaming candidate."
        else:
            tier = "DEEP SLEEPER"
            desc = f"Ranked #{rank}. Very late pick or waiver wire target. Speculative add."

    # Add FPPM context for understanding efficiency
    if fppm is None:
        fppm = 0
    try:
        fppm_val = float(fppm)
    except Exception:
        fppm_val = 0.0

    if fppm_val >= 1.0:
        efficiency = "Elite efficiency (1+ FPPM)."
    elif fppm_val >= 0.85:
        efficiency = "Excellent efficiency (0.85+ FPPM)."
    elif fppm_val >= 0.70:
        efficiency = "Good efficiency (0.70+ FPPM)."
    else:
        efficiency = "Lower efficiency for the rank."

    return f"{tier}: {desc} {efficiency}"
