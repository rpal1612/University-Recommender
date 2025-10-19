from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Any, Tuple
import numpy as np
import pandas as pd


@dataclass
class Weights:
    academic: float = 0.45
    profile: float = 0.30
    financial: float = 0.20
    contextual: float = 0.05

    def as_tuple(self) -> Tuple[float, float, float, float]:
        return (self.academic, self.profile, self.financial, self.contextual)


def clamp01(x: np.ndarray | float) -> np.ndarray | float:
    return np.clip(x, 0.0, 1.0)


def normalize(val: pd.Series | float, vmin: float, vmax: float) -> pd.Series | float:
    if vmax == vmin:
        return 0.0
    return (val - vmin) / (vmax - vmin)


def compute_category_weights(user_prefs: Dict[str, Any] | None) -> Weights:
    w = Weights()

    if not user_prefs:
        return w

    target_tier = (user_prefs.get('target_tier') or '').strip().lower()
    focus = (user_prefs.get('focus') or '').strip().lower()
    program_duration = (user_prefs.get('program_duration') or '').strip().lower()

    # Adjust weights dynamically per requirements
    if target_tier == 'elite':
        # +10% academic, -10% financial (relative move across categories)
        w.academic += 0.10
        w.financial = max(0.0, w.financial - 0.10)

    if focus == 'research':
        w.profile += 0.05

    if program_duration in ('1 year', '1-year', '1yr', 'one year', '1'):
        w.contextual += 0.05

    # Normalize weights to sum to 1.0
    total = w.academic + w.profile + w.financial + w.contextual
    w.academic /= total
    w.profile /= total
    w.financial /= total
    w.contextual /= total

    return w


def calculate_weighted_score(user_prefs: Dict[str, Any], uni_row: pd.Series, data_stats: Dict[str, float]) -> Dict[str, float]:
    """
    Compute dynamic, intent-driven weighted score and category breakdown.

    - Academic score = 0.4*CGPA + 0.4*(GRE_V + GRE_Q) + 0.2*IELTS
    - Profile score = 0.5*Projects + 0.3*Research_Papers + 0.2*Experience
    - Financial score = (1 - normalized_tuition/budget)
    - Contextual score = (0.7*Country_Match + 0.3*Duration_Match)
    - Total score = weighted sum of the four category scores using dynamic weights

    Returns dict with: total, academic, profile, financial, contextual
    """

    # Defaults if some fields are missing from dataset or user_prefs
    greV = float(uni_row.get('greV', np.nan))
    greQ = float(uni_row.get('greQ', np.nan))
    cgpa = float(uni_row.get('cgpa', np.nan))
    ielts_min = uni_row.get('ielts_min', np.nan)
    toefl_min = uni_row.get('toefl_min', np.nan)
    tuition = uni_row.get('tuition_usd', np.nan)
    duration_years = uni_row.get('duration_years', np.nan)
    country = str(uni_row.get('country', ''))

    # Normalize inputs to [0,1]
    cgpa_n = clamp01((cgpa - 0.0) / 4.0) if not np.isnan(cgpa) else 0.5
    greV_n = clamp01((greV - 130.0) / 40.0) if not np.isnan(greV) else 0.5
    greQ_n = clamp01((greQ - 130.0) / 40.0) if not np.isnan(greQ) else 0.5
    # Academic language component should reflect USER proficiency, not uni min
    user_ielts = user_prefs.get('ielts')
    user_toefl = user_prefs.get('toefl')
    if user_ielts is not None and not pd.isna(user_ielts):
        ielts_user_n = clamp01(float(user_ielts) / 9.0)
    elif user_toefl is not None and not pd.isna(user_toefl):
        ielts_user_n = clamp01(float(user_toefl) / 120.0)
    else:
        ielts_user_n = 0.5

    # Profile features may not exist in dataset; default neutral if missing
    projects = float(uni_row.get('projects', np.nan))
    research_papers = float(uni_row.get('research_papers', np.nan))
    experience = float(uni_row.get('experience_years', np.nan))
    # Normalize by simple assumed ranges if present
    projects_n = clamp01(projects / 10.0) if not np.isnan(projects) else 0.5
    research_papers_n = clamp01(research_papers / 10.0) if not np.isnan(research_papers) else 0.5
    experience_n = clamp01(experience / 10.0) if not np.isnan(experience) else 0.5

    # Academic score per formula
    academic = 0.4 * cgpa_n + 0.4 * ((greV_n + greQ_n) / 2.0) + 0.2 * ielts_user_n

    # Profile score per formula
    profile = 0.5 * projects_n + 0.3 * research_papers_n + 0.2 * experience_n

    # Financial score: 1 - normalized_tuition/budget
    budget = float(user_prefs.get('budget_usd', 0) or 0)
    if np.isnan(tuition):
        financial = 0.5  # neutral when unknown
    elif budget > 0:
        tuition_n = clamp01(float(tuition) / max(budget, 1.0))
        financial = clamp01(1.0 - tuition_n)
    else:
        # If no budget provided, make it neutral
        financial = 0.5

    # Contextual score: country + duration matches
    preferred_countries = user_prefs.get('preferred_countries') or []
    program_duration = (user_prefs.get('program_duration') or '').strip().lower()

    if preferred_countries:
        country_match = 1.0 if country in preferred_countries else 0.0
    else:
        country_match = 0.5

    if program_duration in ('1 year', '1-year', '1yr', 'one year', '1'):
        duration_match = 1.0 if duration_years == 1 else 0.0
    elif program_duration in ('2 years', '2-year', '2yr', 'two years', '2'):
        duration_match = 1.0 if duration_years == 2 else 0.0
    else:
        duration_match = 0.5

    contextual = 0.7 * country_match + 0.3 * duration_match

    # Dynamic weights
    w = compute_category_weights(user_prefs)

    # Soft preference boosts (capped at 0.10 total)
    preference_boost = 0.0
    if user_prefs.get('research_focused'):
        has_research = False
        if 'research_papers' in uni_row:
            try:
                has_research = float(uni_row.get('research_papers', 0) or 0) > 0
            except Exception:
                has_research = False
        elif 'research_focused' in uni_row:
            has_research = bool(uni_row.get('research_focused')) is True
        if has_research:
            preference_boost += 0.05

    if user_prefs.get('internship_ok'):
        # Prefer countries known for internships; also use dataset indicator if present
        internship_countries = {"USA", "UK", "Canada", "Australia"}
        if (str(country) in internship_countries) or (bool(uni_row.get('internship_opportunities')) is True):
            preference_boost += 0.03

    if user_prefs.get('work_visa'):
        visa_countries = {"Canada", "UK", "Australia", "Germany"}
        if (str(country) in visa_countries) or (bool(uni_row.get('post_study_work_visa')) is True):
            preference_boost += 0.02

    total = (
        w.academic * academic +
        w.profile * profile +
        w.financial * financial +
        w.contextual * contextual
    )
    total += min(preference_boost, 0.10)

    return {
        'total': float(total),
        'academic': float(academic),
        'profile': float(profile),
        'financial': float(financial),
        'contextual': float(contextual),
        'preferences': float(preference_boost),
        'w_academic': w.academic,
        'w_profile': w.profile,
        'w_financial': w.financial,
        'w_contextual': w.contextual,
    }
