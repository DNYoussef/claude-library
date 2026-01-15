"""
Statistical Analyzer - Text analysis using entropy, burstiness, and lexical diversity metrics.

Extracted from: D:\Projects\slop-detector\backend\analyzers\statistical.py
Purpose: Standalone statistical text analysis component with zero external dependencies.

Metrics calculated:
1. Shannon Entropy - Word distribution predictability
2. Burstiness - Sentence length variance (coefficient of variation)
3. Type-Token Ratio (TTR) - Lexical diversity measurement
4. Hapax Legomena - Words appearing only once (uniqueness ratio)
5. Sentence Structure - Diversity of sentence openings

All metrics use stdlib only: re, math, collections, logging
"""

import re
import math
import logging
from collections import Counter
from dataclasses import dataclass
from typing import Dict, List, Any, Optional

# Configure module logger
logger = logging.getLogger(__name__)


@dataclass
class EntropyMetrics:
    """Shannon entropy calculation results."""
    value: float  # Normalized entropy (0-1)
    raw_entropy: float  # Raw Shannon entropy
    points: float  # Score contribution
    assessment: str  # Human-readable assessment


@dataclass
class BurstinessMetrics:
    """Sentence length variance (burstiness) results."""
    value: float  # Coefficient of variation
    mean_length: float  # Average sentence length in words
    std_dev: float  # Standard deviation
    min_length: int  # Shortest sentence
    max_length: int  # Longest sentence
    points: float  # Score contribution
    assessment: str  # Human-readable assessment


@dataclass
class LexicalDiversityMetrics:
    """Type-Token Ratio (TTR) results."""
    value: float  # TTR value (0-1)
    unique_words: int  # Count of unique words
    total_words: int  # Total word count
    points: float  # Score contribution
    assessment: str  # Human-readable assessment


@dataclass
class HapaxMetrics:
    """Hapax Legomena (words appearing once) results."""
    value: float  # Hapax ratio (0-1)
    hapax_count: int  # Count of words appearing once
    unique_words: int  # Total unique words
    points: float  # Score contribution
    assessment: str  # Human-readable assessment


@dataclass
class SentenceStartMetrics:
    """Sentence opening diversity results."""
    value: float  # Diversity ratio (0-1)
    unique_starts: int  # Count of unique openings
    total_sentences: int  # Total sentence count
    most_common: List[Dict[str, Any]]  # Top repeated openings
    points: float  # Score contribution
    assessment: str  # Human-readable assessment


@dataclass
class StatisticalMetrics:
    """Complete statistical analysis results."""
    score: float  # Final score (0-40)
    max_score: float  # Maximum possible score
    word_count: int  # Total words analyzed
    sentence_count: int  # Total sentences analyzed
    entropy: Optional[EntropyMetrics] = None
    burstiness: Optional[BurstinessMetrics] = None
    lexical_diversity: Optional[LexicalDiversityMetrics] = None
    hapax: Optional[HapaxMetrics] = None
    sentence_starts: Optional[SentenceStartMetrics] = None
    summary: str = ""


class StatisticalAnalyzer:
    """
    Analyzes statistical properties of text for pattern detection.

    Detects patterns that distinguish AI-generated text from human writing
    based on entropy, burstiness, lexical diversity, and structural analysis.

    Usage:
        analyzer = StatisticalAnalyzer()
        result = analyzer.analyze("Your text here...")
        print(f"Score: {result.score}/{result.max_score}")
        print(f"Entropy: {result.entropy.value}")

        # With debug output:
        result = analyzer.analyze("Your text here...", debug=True)
    """

    MAX_SCORE = 40.0
    MIN_WORDS_REQUIRED = 20
    MIN_SENTENCES_FOR_BURSTINESS = 3
    MIN_SENTENCES_FOR_STARTS = 5
    MSTTR_SEGMENT_SIZE = 100
    MSTTR_MIN_SEGMENT_SIZE = 2  # Minimum segment size to prevent division by zero
    SENTENCE_START_NGRAM_SIZE = 2  # Number of words to use for sentence start analysis

    # Word extraction pattern - use consistent pattern across all methods
    WORD_PATTERN = re.compile(r'[a-zA-Z]+')

    # Configurable thresholds for entropy scoring
    ENTROPY_THRESHOLDS = {
        'very_low': {'max': 0.55, 'points': 10.0, 'assessment': 'Very low entropy - highly predictable'},
        'low': {'max': 0.65, 'points': 7.0, 'assessment': 'Low entropy - somewhat predictable'},
        'moderate': {'max': 0.75, 'points': 4.0, 'assessment': 'Moderate entropy'},
        'good': {'max': 0.85, 'points': 1.0, 'assessment': 'Good entropy - natural variation'},
        'high': {'max': 1.0, 'points': 0.0, 'assessment': 'High entropy - varied word choice'},
    }

    # Configurable thresholds for burstiness scoring
    BURSTINESS_THRESHOLDS = {
        'very_uniform': {'max': 0.2, 'points': 10.0, 'assessment': 'Very uniform sentence lengths - AI pattern'},
        'low_variation': {'max': 0.3, 'points': 7.0, 'assessment': 'Low variation in sentence length'},
        'moderate': {'max': 0.4, 'points': 4.0, 'assessment': 'Moderate sentence length variation'},
        'good': {'max': 0.5, 'points': 1.0, 'assessment': 'Good sentence length variation'},
        'natural': {'max': float('inf'), 'points': 0.0, 'assessment': 'Natural sentence length variation'},
    }

    def analyze(self, text: str, debug: bool = False) -> StatisticalMetrics:
        """
        Analyze text for statistical properties.

        Args:
            text: Input text to analyze
            debug: If True, emit debug logging for all metric calculations

        Returns:
            StatisticalMetrics dataclass with all calculated metrics
        """
        # Use consistent word pattern (WORD_PATTERN = [a-zA-Z]+)
        words = self.WORD_PATTERN.findall(text.lower())
        sentences = self._split_sentences(text)

        if debug:
            logger.debug(f"Analyzing text: {len(words)} words, {len(sentences)} sentences")

        if len(words) < self.MIN_WORDS_REQUIRED:
            if debug:
                logger.debug(f"Text too short: {len(words)} words < {self.MIN_WORDS_REQUIRED} required")
            return StatisticalMetrics(
                score=0,
                max_score=self.MAX_SCORE,
                word_count=len(words),
                sentence_count=len(sentences),
                summary='Text too short for meaningful statistical analysis.'
            )

        total_points = 0.0

        # 1. Shannon Entropy (word-level)
        entropy_result = self._calculate_entropy(words)
        total_points += entropy_result.points
        if debug:
            logger.debug(f"Entropy: value={entropy_result.value}, points={entropy_result.points}")

        # 2. Burstiness (sentence length variance)
        burstiness_result = self._calculate_burstiness(sentences)
        total_points += burstiness_result.points
        if debug:
            logger.debug(f"Burstiness: value={burstiness_result.value}, points={burstiness_result.points}")

        # 3. Type-Token Ratio (lexical diversity)
        ttr_result = self._calculate_ttr(words)
        total_points += ttr_result.points
        if debug:
            logger.debug(f"TTR: value={ttr_result.value}, points={ttr_result.points}")

        # 4. Hapax Legomena (words appearing only once)
        hapax_result = self._calculate_hapax(words)
        total_points += hapax_result.points
        if debug:
            logger.debug(f"Hapax: value={hapax_result.value}, points={hapax_result.points}")

        # 5. Sentence start diversity
        start_result = self._analyze_sentence_starts(sentences)
        total_points += start_result.points
        if debug:
            logger.debug(f"Sentence starts: value={start_result.value}, points={start_result.points}")

        final_score = min(total_points, self.MAX_SCORE)

        if debug:
            logger.debug(f"Final score: {final_score}/{self.MAX_SCORE}")

        return StatisticalMetrics(
            score=round(final_score, 1),
            max_score=self.MAX_SCORE,
            word_count=len(words),
            sentence_count=len(sentences),
            entropy=entropy_result,
            burstiness=burstiness_result,
            lexical_diversity=ttr_result,
            hapax=hapax_result,
            sentence_starts=start_result,
            summary=self._generate_summary(
                entropy_result, burstiness_result, ttr_result,
                hapax_result, start_result, final_score
            )
        )

    def analyze_dict(self, text: str) -> Dict[str, Any]:
        """
        Analyze text and return results as dictionary (legacy compatibility).

        Args:
            text: Input text to analyze

        Returns:
            Dictionary with score, metrics, and summary
        """
        result = self.analyze(text)

        metrics = {}
        if result.entropy:
            metrics['entropy'] = {
                'value': result.entropy.value,
                'raw_entropy': result.entropy.raw_entropy,
                'points': result.entropy.points,
                'assessment': result.entropy.assessment
            }
        if result.burstiness:
            metrics['burstiness'] = {
                'value': result.burstiness.value,
                'mean_length': result.burstiness.mean_length,
                'std_dev': result.burstiness.std_dev,
                'min_length': result.burstiness.min_length,
                'max_length': result.burstiness.max_length,
                'points': result.burstiness.points,
                'assessment': result.burstiness.assessment
            }
        if result.lexical_diversity:
            metrics['lexical_diversity'] = {
                'value': result.lexical_diversity.value,
                'unique_words': result.lexical_diversity.unique_words,
                'total_words': result.lexical_diversity.total_words,
                'points': result.lexical_diversity.points,
                'assessment': result.lexical_diversity.assessment
            }
        if result.hapax:
            metrics['hapax'] = {
                'value': result.hapax.value,
                'hapax_count': result.hapax.hapax_count,
                'unique_words': result.hapax.unique_words,
                'points': result.hapax.points,
                'assessment': result.hapax.assessment
            }
        if result.sentence_starts:
            metrics['sentence_starts'] = {
                'value': result.sentence_starts.value,
                'unique_starts': result.sentence_starts.unique_starts,
                'total_sentences': result.sentence_starts.total_sentences,
                'most_common': result.sentence_starts.most_common,
                'points': result.sentence_starts.points,
                'assessment': result.sentence_starts.assessment
            }

        return {
            'score': result.score,
            'max_score': result.max_score,
            'metrics': metrics,
            'word_count': result.word_count,
            'sentence_count': result.sentence_count,
            'summary': result.summary
        }

    def _split_sentences(self, text: str) -> List[str]:
        """Split text into sentences."""
        sentences = re.split(r'[.!?]+', text)
        return [s.strip() for s in sentences if s.strip() and len(s.strip()) > 5]

    def _calculate_entropy(self, words: List[str]) -> EntropyMetrics:
        """
        Calculate Shannon entropy of word distribution.

        Low entropy = predictable = AI-like pattern
        Human text typically has normalized entropy 0.7-0.9
        AI text tends toward 0.5-0.7 (more predictable)
        """
        if not words:
            return EntropyMetrics(
                value=0, raw_entropy=0, points=0, assessment='No data'
            )

        word_counts = Counter(words)
        total = len(words)

        entropy = 0
        for count in word_counts.values():
            p = count / total
            if p > 0:
                entropy -= p * math.log2(p)

        # Normalize by log2 of vocabulary size for fair comparison
        vocab_size = len(word_counts)
        max_entropy = math.log2(vocab_size) if vocab_size > 1 else 1
        normalized_entropy = entropy / max_entropy if max_entropy > 0 else 0

        # Use class-level configurable thresholds
        points = 0.0
        assessment = ''
        for level_name, thresholds in self.ENTROPY_THRESHOLDS.items():
            if normalized_entropy < thresholds['max']:
                points = thresholds['points']
                assessment = thresholds['assessment']
                break

        return EntropyMetrics(
            value=round(normalized_entropy, 3),
            raw_entropy=round(entropy, 3),
            points=points,
            assessment=assessment
        )

    def _calculate_burstiness(self, sentences: List[str]) -> BurstinessMetrics:
        """
        Calculate burstiness - variance in sentence lengths.

        Low variance = uniform = AI-like pattern
        Human writing typically has CV > 0.4 (varied sentence lengths)
        AI tends toward CV 0.15-0.3 (uniform)
        """
        if len(sentences) < self.MIN_SENTENCES_FOR_BURSTINESS:
            return BurstinessMetrics(
                value=0, mean_length=0, std_dev=0,
                min_length=0, max_length=0,
                points=0, assessment='Too few sentences'
            )

        # Use consistent WORD_PATTERN ([a-zA-Z]+) for word counting
        lengths = [len(self.WORD_PATTERN.findall(s)) for s in sentences]
        lengths = [l for l in lengths if l > 0]

        if not lengths:
            return BurstinessMetrics(
                value=0, mean_length=0, std_dev=0,
                min_length=0, max_length=0,
                points=0, assessment='No valid sentences'
            )

        mean = sum(lengths) / len(lengths)
        if mean == 0:
            return BurstinessMetrics(
                value=0, mean_length=0, std_dev=0,
                min_length=0, max_length=0,
                points=0, assessment='Invalid data'
            )

        variance = sum((l - mean) ** 2 for l in lengths) / len(lengths)
        std_dev = variance ** 0.5
        cv = std_dev / mean  # Coefficient of variation

        # Use class-level configurable thresholds
        points = 0.0
        assessment = ''
        for level_name, thresholds in self.BURSTINESS_THRESHOLDS.items():
            if cv < thresholds['max']:
                points = thresholds['points']
                assessment = thresholds['assessment']
                break

        return BurstinessMetrics(
            value=round(cv, 3),
            mean_length=round(mean, 1),
            std_dev=round(std_dev, 1),
            min_length=min(lengths),
            max_length=max(lengths),
            points=points,
            assessment=assessment
        )

    def _calculate_ttr(self, words: List[str]) -> LexicalDiversityMetrics:
        """
        Calculate Type-Token Ratio (lexical diversity).

        Low TTR = repetitive vocabulary = potentially AI
        Human text typically has TTR 0.4-0.7
        Very high TTR (>0.8) in long text is suspicious (thesaurus syndrome)
        """
        if not words:
            return LexicalDiversityMetrics(
                value=0, unique_words=0, total_words=0,
                points=0, assessment='No data'
            )

        # Use MSTTR (Mean Segmental TTR) for longer texts
        segment_size = self.MSTTR_SEGMENT_SIZE
        # Validate segment_size to prevent division by zero (minimum of MSTTR_MIN_SEGMENT_SIZE)
        min_segment_for_inclusion = max(segment_size // 2, self.MSTTR_MIN_SEGMENT_SIZE)

        if len(words) > segment_size:
            segments = [
                words[i:i+segment_size]
                for i in range(0, len(words), segment_size)
            ]
            ttrs = [
                len(set(seg)) / len(seg)
                for seg in segments
                if len(seg) >= min_segment_for_inclusion
            ]
            ttr = sum(ttrs) / len(ttrs) if ttrs else len(set(words)) / len(words)
        else:
            ttr = len(set(words)) / len(words)

        unique_words = len(set(words))

        if ttr < 0.3:
            points = 8.0
            assessment = 'Very low lexical diversity - repetitive'
        elif ttr < 0.4:
            points = 4.0
            assessment = 'Limited vocabulary variation'
        elif ttr > 0.8 and len(words) > 200:
            points = 6.0
            assessment = 'Suspiciously high diversity - thesaurus pattern'
        elif ttr > 0.7 and len(words) > 500:
            points = 3.0
            assessment = 'Unusually varied vocabulary'
        else:
            points = 0
            assessment = 'Natural vocabulary diversity'

        return LexicalDiversityMetrics(
            value=round(ttr, 3),
            unique_words=unique_words,
            total_words=len(words),
            points=points,
            assessment=assessment
        )

    def _calculate_hapax(self, words: List[str]) -> HapaxMetrics:
        """
        Calculate Hapax Legomena ratio (words appearing only once).

        Human text typically has 40-60% hapax in short samples.
        AI tends to be either too low (repetitive) or artificially varied.
        """
        if not words:
            return HapaxMetrics(
                value=0, hapax_count=0, unique_words=0,
                points=0, assessment='No data'
            )

        word_counts = Counter(words)
        hapax = sum(1 for count in word_counts.values() if count == 1)
        hapax_ratio = hapax / len(word_counts) if word_counts else 0

        if hapax_ratio < 0.3:
            points = 6.0
            assessment = 'Low hapax ratio - repetitive vocabulary'
        elif hapax_ratio < 0.4:
            points = 3.0
            assessment = 'Below average word uniqueness'
        elif hapax_ratio > 0.75:
            points = 4.0
            assessment = 'Unusually high uniqueness - may be artificial'
        else:
            points = 0
            assessment = 'Natural word uniqueness pattern'

        return HapaxMetrics(
            value=round(hapax_ratio, 3),
            hapax_count=hapax,
            unique_words=len(word_counts),
            points=points,
            assessment=assessment
        )

    def _analyze_sentence_starts(self, sentences: List[str]) -> SentenceStartMetrics:
        """
        Analyze diversity of sentence openings.

        AI often starts many sentences the same way.
        """
        if len(sentences) < self.MIN_SENTENCES_FOR_STARTS:
            return SentenceStartMetrics(
                value=0, unique_starts=0, total_sentences=len(sentences),
                most_common=[], points=0, assessment='Too few sentences'
            )

        # Get first word/phrase of each sentence using configurable n-gram size
        starts = []
        ngram_size = self.SENTENCE_START_NGRAM_SIZE
        for s in sentences:
            words = s.split()
            if not words:
                continue
            # Get first N words (configurable via SENTENCE_START_NGRAM_SIZE)
            start_words = words[:ngram_size]
            start = ' '.join(w.lower() for w in start_words)
            starts.append(start)

        if not starts:
            return SentenceStartMetrics(
                value=0, unique_starts=0, total_sentences=0,
                most_common=[], points=0, assessment='No data'
            )

        # Calculate diversity of starts
        unique_starts = len(set(starts))
        diversity = unique_starts / len(starts)

        # Check for repeated patterns
        start_counts = Counter(starts)
        max_repeat = max(start_counts.values())
        repeat_ratio = max_repeat / len(starts)

        if diversity < 0.5 or repeat_ratio > 0.3:
            points = 6.0
            assessment = 'Repetitive sentence openings'
        elif diversity < 0.7:
            points = 3.0
            assessment = 'Limited variety in sentence starts'
        else:
            points = 0
            assessment = 'Good variety in sentence openings'

        most_common = [
            {'start': s, 'count': c}
            for s, c in start_counts.most_common(3)
        ]

        return SentenceStartMetrics(
            value=round(diversity, 3),
            unique_starts=unique_starts,
            total_sentences=len(starts),
            most_common=most_common,
            points=points,
            assessment=assessment
        )

    def _generate_summary(
        self,
        entropy: EntropyMetrics,
        burstiness: BurstinessMetrics,
        ttr: LexicalDiversityMetrics,
        hapax: HapaxMetrics,
        starts: SentenceStartMetrics,
        score: float
    ) -> str:
        """Generate human-readable summary of statistical analysis."""
        if score < 10:
            return "Statistical patterns appear natural and human-like."

        issues = []

        if entropy.points >= 7:
            issues.append('predictable word choice')

        if burstiness.points >= 7:
            issues.append('uniform sentence lengths')

        if ttr.points >= 4:
            issues.append('vocabulary patterns')

        if starts.points >= 3:
            issues.append('repetitive sentence openings')

        if issues:
            return f"Statistical analysis flagged: {', '.join(issues)}."

        return "Some statistical patterns deviate from typical human writing."


# Standalone utility functions for individual metric calculations

def calculate_shannon_entropy(words: List[str]) -> float:
    """
    Calculate normalized Shannon entropy for a list of words.

    Args:
        words: List of lowercase words

    Returns:
        Normalized entropy value (0-1)
    """
    if not words:
        return 0.0

    word_counts = Counter(words)
    total = len(words)

    entropy = 0
    for count in word_counts.values():
        p = count / total
        if p > 0:
            entropy -= p * math.log2(p)

    vocab_size = len(word_counts)
    max_entropy = math.log2(vocab_size) if vocab_size > 1 else 1
    return entropy / max_entropy if max_entropy > 0 else 0


def calculate_coefficient_of_variation(values: List[float]) -> float:
    """
    Calculate coefficient of variation (CV) for a list of values.

    Args:
        values: List of numeric values

    Returns:
        Coefficient of variation (std_dev / mean)
    """
    if not values or len(values) < 2:
        return 0.0

    mean = sum(values) / len(values)
    if mean == 0:
        return 0.0

    variance = sum((v - mean) ** 2 for v in values) / len(values)
    return (variance ** 0.5) / mean


def calculate_type_token_ratio(words: List[str], segment_size: int = 100, min_segment_size: int = 2) -> float:
    """
    Calculate Type-Token Ratio (TTR) with optional MSTTR for long texts.

    Args:
        words: List of words
        segment_size: Segment size for MSTTR calculation
        min_segment_size: Minimum segment size to prevent division by zero (default: 2)

    Returns:
        TTR value (0-1)
    """
    if not words:
        return 0.0

    # Validate segment_size to prevent division by zero
    min_segment_for_inclusion = max(segment_size // 2, min_segment_size)

    if len(words) > segment_size:
        segments = [
            words[i:i+segment_size]
            for i in range(0, len(words), segment_size)
        ]
        ttrs = [
            len(set(seg)) / len(seg)
            for seg in segments
            if len(seg) >= min_segment_for_inclusion
        ]
        return sum(ttrs) / len(ttrs) if ttrs else len(set(words)) / len(words)

    return len(set(words)) / len(words)


def calculate_hapax_ratio(words: List[str]) -> float:
    """
    Calculate Hapax Legomena ratio (words appearing exactly once).

    Args:
        words: List of words

    Returns:
        Hapax ratio (0-1)
    """
    if not words:
        return 0.0

    word_counts = Counter(words)
    hapax = sum(1 for count in word_counts.values() if count == 1)
    return hapax / len(word_counts) if word_counts else 0
