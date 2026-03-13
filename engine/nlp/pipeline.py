"""
JanPulse AI — NLP Pipeline
5-Layer Hybrid Stack: Rules → Lexicon → Transformer → LLM → Human Review Queue

Processes DataPoints through language detection, preprocessing, sentiment classification,
emotion detection, stance detection, NER, topic modelling, sarcasm detection, and bot scoring.
"""

import os
import re
import json
import hashlib
from datetime import datetime
from typing import Optional
from loguru import logger

from engine.models import (
    DataPoint, NLPResults, SentimentResult, StanceResult, EmotionScore,
    EntityDetection, SentimentLabel, EmotionLabel, StanceLabel, LanguageCode
)


# ─── LAYER 1: RULES-BASED ────────────────────────────────────────────────

class RulesEngine:
    """Fast, deterministic classification using regex and keyword matching."""

    def __init__(self, keyword_corpus: dict):
        self.corpus = keyword_corpus
        self._build_patterns()

    def _build_patterns(self):
        """Pre-compile regex patterns from keyword corpus."""
        self.positive_patterns = []
        self.negative_patterns = []
        self.sarcasm_patterns = []

        categories = self.corpus.get("categories", {})

        # Positive rally markers
        pos_markers = categories.get("sentiment_markers", {}).get("positive_rally", {}).get("variants", {})
        for lang, terms in pos_markers.items():
            for term in terms:
                self.positive_patterns.append(re.compile(re.escape(term.lower()), re.IGNORECASE))

        # Negative rally markers
        neg_markers = categories.get("sentiment_markers", {}).get("negative_rally", {}).get("variants", {})
        for lang, terms in neg_markers.items():
            for term in terms:
                self.negative_patterns.append(re.compile(re.escape(term.lower()), re.IGNORECASE))

        # Sarcasm indicators
        sarc_markers = categories.get("sentiment_markers", {}).get("sarcasm_indicators", {}).get("variants", {})
        for lang, terms in sarc_markers.items():
            for term in terms:
                self.sarcasm_patterns.append(re.compile(re.escape(term.lower()), re.IGNORECASE))

    def classify(self, text: str) -> dict:
        """Returns rules-based signals (not final classification)."""
        text_lower = text.lower()
        pos_hits = sum(1 for p in self.positive_patterns if p.search(text_lower))
        neg_hits = sum(1 for p in self.negative_patterns if p.search(text_lower))
        sarc_hits = sum(1 for p in self.sarcasm_patterns if p.search(text_lower))

        return {
            "positive_signal": pos_hits,
            "negative_signal": neg_hits,
            "sarcasm_signal": sarc_hits,
            "has_signal": (pos_hits + neg_hits + sarc_hits) > 0
        }


# ─── LAYER 2: LEXICON-BASED ─────────────────────────────────────────────

class LexiconEngine:
    """Domain-specific political sentiment lexicon scoring."""

    # Base political lexicon (expandable via config)
    POSITIVE_LEXICON = {
        "en": {"development": 0.6, "growth": 0.5, "historic": 0.7, "amazing": 0.8,
               "massive": 0.5, "support": 0.6, "victory": 0.8, "progress": 0.6,
               "trust": 0.7, "hope": 0.7, "proud": 0.7, "strong": 0.5},
        "hi": {"विकास": 0.6, "शानदार": 0.8, "जबरदस्त": 0.7, "समर्थन": 0.6,
               "जीत": 0.8, "उम्मीद": 0.7, "गर्व": 0.7},
        "romanised": {"vikas": 0.6, "shandar": 0.8, "jabardast": 0.7, "jeet": 0.8,
                      "support": 0.6, "unnayan": 0.6}
    }

    NEGATIVE_LEXICON = {
        "en": {"corruption": -0.7, "scam": -0.8, "failure": -0.7, "empty": -0.5,
               "flop": -0.8, "lie": -0.8, "violence": -0.7, "fraud": -0.8,
               "hate": -0.8, "destroy": -0.7, "worst": -0.8, "fake": -0.7},
        "hi": {"भ्रष्टाचार": -0.7, "घोटाला": -0.8, "झूठ": -0.8, "हिंसा": -0.7,
               "फ्लॉप": -0.8, "जुमला": -0.9, "बर्बाद": -0.7},
        "romanised": {"corruption": -0.7, "jumla": -0.9, "flop": -0.8, "jhooth": -0.8,
                      "tolabaji": -0.7, "bhrashtachar": -0.7}
    }

    def score(self, text: str, language: str = "en") -> dict:
        """Compute lexicon-based sentiment score."""
        words = text.lower().split()
        pos_score = 0.0
        neg_score = 0.0

        for lang_key in [language, "en", "romanised"]:
            pos_lex = self.POSITIVE_LEXICON.get(lang_key, {})
            neg_lex = self.NEGATIVE_LEXICON.get(lang_key, {})
            for word in words:
                if word in pos_lex:
                    pos_score += pos_lex[word]
                if word in neg_lex:
                    neg_score += neg_lex[word]

        total = pos_score + abs(neg_score)
        if total == 0:
            return {"label": "neutral", "score": 0.0, "confidence": 0.3}

        net = pos_score + neg_score  # neg_score is already negative
        if net > 0.2:
            return {"label": "positive", "score": net, "confidence": min(0.7, net / 2)}
        elif net < -0.2:
            return {"label": "negative", "score": net, "confidence": min(0.7, abs(net) / 2)}
        else:
            return {"label": "neutral", "score": net, "confidence": 0.4}


# ─── LAYER 3: TRANSFORMER-BASED ─────────────────────────────────────────

class TransformerEngine:
    """
    Pre-trained multilingual transformer models for sentiment, emotion, NER.
    Uses MuRIL for Indian languages, XLM-RoBERTa for emotion.
    """

    def __init__(self, device: str = "cpu"):
        self.device = device
        self.sentiment_pipeline = None
        self.emotion_pipeline = None
        self.ner_pipeline = None
        self.embeddings_model = None
        self._loaded = False

    def load_models(self):
        """Load all transformer models. Call once at startup."""
        try:
            from transformers import pipeline
            logger.info("Loading transformer models...")

            # Sentiment: multilingual model
            try:
                self.sentiment_pipeline = pipeline(
                    "sentiment-analysis",
                    model="cardiffnlp/twitter-xlm-roberta-base-sentiment-multilingual",
                    device=0 if self.device == "cuda" else -1,
                    max_length=512, truncation=True
                )
                logger.info("Sentiment model loaded: twitter-xlm-roberta-base-sentiment-multilingual")
            except Exception as e:
                logger.warning(f"Could not load sentiment model: {e}")

            # Emotion: multilingual
            try:
                self.emotion_pipeline = pipeline(
                    "text-classification",
                    model="j-hartmann/emotion-english-distilroberta-base",
                    device=0 if self.device == "cuda" else -1,
                    max_length=512, truncation=True, top_k=5
                )
                logger.info("Emotion model loaded")
            except Exception as e:
                logger.warning(f"Could not load emotion model: {e}")

            # NER
            try:
                self.ner_pipeline = pipeline(
                    "ner",
                    model="dslim/bert-base-NER",
                    device=0 if self.device == "cuda" else -1,
                    aggregation_strategy="simple"
                )
                logger.info("NER model loaded")
            except Exception as e:
                logger.warning(f"Could not load NER model: {e}")

            self._loaded = True
            logger.info("All transformer models loaded successfully")

        except ImportError:
            logger.warning("transformers library not installed; transformer layer disabled")

    def classify_sentiment(self, text: str) -> dict:
        if not self.sentiment_pipeline:
            return {"label": "neutral", "confidence": 0.0, "method": "transformer_unavailable"}
        try:
            result = self.sentiment_pipeline(text[:512])[0]
            label_map = {"positive": "positive", "negative": "negative", "neutral": "neutral"}
            label = label_map.get(result["label"].lower(), "neutral")
            return {"label": label, "confidence": result["score"], "method": "transformer"}
        except Exception as e:
            logger.debug(f"Transformer sentiment error: {e}")
            return {"label": "neutral", "confidence": 0.0, "method": "transformer_error"}

    def classify_emotion(self, text: str) -> list[dict]:
        if not self.emotion_pipeline:
            return []
        try:
            results = self.emotion_pipeline(text[:512])
            if isinstance(results[0], list):
                results = results[0]
            emotion_map = {
                "anger": EmotionLabel.ANGER, "disgust": EmotionLabel.DISGUST,
                "fear": EmotionLabel.FEAR, "joy": EmotionLabel.JOY,
                "sadness": EmotionLabel.SADNESS, "surprise": EmotionLabel.EXCITEMENT,
                "neutral": EmotionLabel.TRUST
            }
            return [
                {"label": emotion_map.get(r["label"].lower(), EmotionLabel.TRUST).value,
                 "score": r["score"]}
                for r in results[:5]
            ]
        except Exception as e:
            logger.debug(f"Transformer emotion error: {e}")
            return []

    def extract_entities(self, text: str) -> list[dict]:
        if not self.ner_pipeline:
            return []
        try:
            results = self.ner_pipeline(text[:512])
            entities = []
            for r in results:
                entities.append({
                    "text": r.get("word", ""),
                    "entity_type": r.get("entity_group", "MISC"),
                    "normalised": r.get("word", "").strip("##").strip()
                })
            return entities
        except Exception as e:
            logger.debug(f"Transformer NER error: {e}")
            return []


# ─── LAYER 4: LLM-BASED INTERPRETATION ──────────────────────────────────

class LLMEngine:
    """
    Large Language Model layer for nuanced analysis.
    Uses Anthropic Claude (primary) or OpenAI GPT-4o (fallback).
    """

    SENTIMENT_PROMPT = """You are an expert political discourse analyst specialising in Indian elections, particularly West Bengal politics. Analyse social media text in Bengali, Hindi, English, Hinglish, and Romanised Bengali. You understand political sarcasm, code-mixing, regional slang, and cultural context.

Analyse the following text and return ONLY valid JSON (no markdown, no backticks):

Text: "{text}"
Language: {language}
Platform: {platform}
Context: Monitoring rally by {leader} ({party}) in {city}

Return JSON:
{{"sentiment": {{"label": "positive|negative|neutral|mixed", "confidence": 0.0}}, "is_sarcastic": false, "sarcasm_confidence": 0.0, "true_sentiment_if_sarcastic": null, "emotions": [{{"label": "emotion_name", "score": 0.0}}], "stance_toward_leader": "support|oppose|neutral", "stance_toward_party": "support|oppose|neutral", "stance_toward_rally": "positive|negative|neutral", "key_topics": [], "reasoning": "brief explanation"}}"""

    def __init__(self):
        self.anthropic_key = os.getenv("ANTHROPIC_API_KEY", "")
        self.openai_key = os.getenv("OPENAI_API_KEY", "")
        self.primary = os.getenv("LLM_PRIMARY_PROVIDER", "anthropic")
        self.primary_model = os.getenv("LLM_PRIMARY_MODEL", "claude-sonnet-4-20250514")
        self.fallback_model = os.getenv("LLM_FALLBACK_MODEL", "gpt-4o-mini")

    def analyse(self, text: str, language: str = "en", platform: str = "twitter",
                leader: str = "Narendra Modi", party: str = "BJP",
                city: str = "Kolkata") -> Optional[dict]:
        """Run LLM analysis on a single text. Returns parsed JSON or None."""
        prompt = self.SENTIMENT_PROMPT.format(
            text=text[:1000], language=language, platform=platform,
            leader=leader, party=party, city=city
        )

        # Try primary provider
        result = None
        if self.primary == "anthropic" and self.anthropic_key:
            result = self._call_anthropic(prompt)
        elif self.openai_key:
            result = self._call_openai(prompt)

        # Try fallback
        if result is None:
            if self.openai_key and self.primary == "anthropic":
                result = self._call_openai(prompt)
            elif self.anthropic_key:
                result = self._call_anthropic(prompt)

        return result

    def _call_anthropic(self, prompt: str) -> Optional[dict]:
        try:
            import anthropic
            client = anthropic.Anthropic(api_key=self.anthropic_key)
            response = client.messages.create(
                model=self.primary_model,
                max_tokens=800,
                messages=[{"role": "user", "content": prompt}]
            )
            text = response.content[0].text.strip()
            # Clean potential markdown wrapping
            if text.startswith("```"):
                text = text.split("```")[1]
                if text.startswith("json"):
                    text = text[4:]
            return json.loads(text)
        except Exception as e:
            logger.debug(f"Anthropic API error: {e}")
            return None

    def _call_openai(self, prompt: str) -> Optional[dict]:
        try:
            import openai
            client = openai.OpenAI(api_key=self.openai_key)
            response = client.chat.completions.create(
                model=self.fallback_model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=800, temperature=0.1,
                response_format={"type": "json_object"}
            )
            text = response.choices[0].message.content.strip()
            return json.loads(text)
        except Exception as e:
            logger.debug(f"OpenAI API error: {e}")
            return None

    def summarise_narratives(self, classified_docs: list[dict], phase: str = "pre_rally") -> Optional[dict]:
        """Generate narrative summary from batch of classified documents."""
        prompt = f"""You are a political intelligence analyst. Summarise the dominant narratives from these {len(classified_docs)} classified social media posts about a political rally in West Bengal ({phase} phase).

Data sample (first 20 items):
{json.dumps(classified_docs[:20], indent=2, default=str)[:3000]}

Return ONLY valid JSON:
{{"dominant_narratives": [{{"narrative_title": "string", "sentiment_direction": "positive|negative|mixed", "strength": 0.0, "platforms": [], "estimated_reach": "high|medium|low"}}], "counter_narratives": [], "emerging_risks": [], "narrative_shift_description": "string"}}"""

        if self.anthropic_key:
            return self._call_anthropic(prompt)
        elif self.openai_key:
            return self._call_openai(prompt)
        return None


# ─── LAYER 5: BOT DETECTION ─────────────────────────────────────────────

class BotDetector:
    """Heuristic-based bot suspicion scoring."""

    def score(self, author: dict, text: str, engagement: dict) -> float:
        score = 0.0

        # Account age
        age = author.get("account_age_days", 365)
        if age < 30:
            score += 0.25
        elif age < 90:
            score += 0.10

        # Follower ratio
        followers = author.get("follower_count", 0)
        if followers < 5:
            score += 0.15
        elif followers < 20:
            score += 0.05

        # Text patterns
        if text == text.upper() and len(text) > 20:
            score += 0.10  # All caps
        if len(set(text.split())) / max(len(text.split()), 1) < 0.3:
            score += 0.15  # Very repetitive words
        if text.count("#") > 5:
            score += 0.10  # Hashtag stuffing
        if len(text) < 15:
            score += 0.05  # Very short

        # Engagement anomaly
        likes = engagement.get("likes", 0)
        if followers > 0 and likes > followers * 2:
            score += 0.10  # Suspicious engagement

        return min(1.0, score)


# ─── TEXT PREPROCESSOR ───────────────────────────────────────────────────

class TextPreprocessor:
    """Clean and normalise text for NLP processing."""

    URL_PATTERN = re.compile(r'https?://\S+')
    MENTION_PATTERN = re.compile(r'@\w+')
    EXTRA_SPACES = re.compile(r'\s+')

    @staticmethod
    def clean(text: str) -> str:
        cleaned = TextPreprocessor.URL_PATTERN.sub('', text)
        cleaned = TextPreprocessor.MENTION_PATTERN.sub('', cleaned)
        cleaned = TextPreprocessor.EXTRA_SPACES.sub(' ', cleaned)
        cleaned = cleaned.strip()
        return cleaned

    @staticmethod
    def detect_language(text: str) -> tuple[str, str]:
        """Returns (language_code, script_type)."""
        try:
            from langdetect import detect
            lang = detect(text)
            lang_map = {"en": ("en", "latin"), "hi": ("hi", "devanagari"),
                        "bn": ("bn", "bengali"), "mr": ("hi", "devanagari")}
            result = lang_map.get(lang, ("unknown", "unknown"))

            # Check for code-mixing
            has_devanagari = bool(re.search(r'[\u0900-\u097F]', text))
            has_bengali = bool(re.search(r'[\u0980-\u09FF]', text))
            has_latin = bool(re.search(r'[a-zA-Z]', text))

            if has_latin and has_devanagari:
                return ("hi-en", "mixed")
            if has_latin and has_bengali:
                return ("bn-en", "mixed")
            return result
        except Exception:
            return ("unknown", "unknown")


# ─── MAIN PIPELINE ──────────────────────────────────────────────────────

class NLPPipeline:
    """
    Orchestrates the full 5-layer NLP pipeline.
    Processes DataPoints and populates their nlp_results field.
    """

    def __init__(self, keyword_corpus: dict = None, use_gpu: bool = False,
                 use_llm: bool = True, campaign_config: dict = None):
        self.preprocessor = TextPreprocessor()
        self.rules_engine = RulesEngine(keyword_corpus or {"categories": {}})
        self.lexicon_engine = LexiconEngine()
        self.transformer_engine = TransformerEngine(device="cuda" if use_gpu else "cpu")
        self.llm_engine = LLMEngine() if use_llm else None
        self.bot_detector = BotDetector()
        self.campaign_config = campaign_config or {}
        self._llm_call_count = 0
        self._llm_budget = int(os.getenv("LLM_DAILY_BUDGET_CALLS", "500"))

    def load_models(self):
        """Load all transformer models. Call once at startup."""
        self.transformer_engine.load_models()
        logger.info("NLP Pipeline models loaded")

    def process(self, datapoint: DataPoint) -> DataPoint:
        """Run full NLP pipeline on a single DataPoint."""
        text = datapoint.raw_text
        if not text or len(text.strip()) < 3:
            return datapoint

        # ── Stage 1: Preprocessing
        normalised = self.preprocessor.clean(text)
        datapoint.normalised_text = normalised

        # ── Stage 2: Language Detection
        lang_code, script = self.preprocessor.detect_language(text)
        datapoint.language_detected = LanguageCode(lang_code) if lang_code in [e.value for e in LanguageCode] else LanguageCode.UNKNOWN
        datapoint.language_script = script

        # ── Stage 3: Rules-based signals
        rules_result = self.rules_engine.classify(normalised)

        # ── Stage 4: Lexicon scoring
        lexicon_result = self.lexicon_engine.score(normalised, lang_code)

        # ── Stage 5: Transformer classification
        transformer_sentiment = self.transformer_engine.classify_sentiment(normalised)
        transformer_emotions = self.transformer_engine.classify_emotion(normalised)
        entities = self.transformer_engine.extract_entities(normalised)

        # ── Stage 6: Determine if LLM needed (ambiguous cases, sarcasm signals)
        needs_llm = (
            rules_result.get("sarcasm_signal", 0) > 0 or
            transformer_sentiment.get("confidence", 0) < 0.6 or
            (lexicon_result.get("label") != transformer_sentiment.get("label") and
             lexicon_result.get("label") != "neutral")
        )

        llm_result = None
        if needs_llm and self.llm_engine and self._llm_call_count < self._llm_budget:
            llm_result = self.llm_engine.analyse(
                text=text, language=lang_code,
                platform=datapoint.source_platform.value,
                leader=self.campaign_config.get("primary_leader", "Narendra Modi"),
                party=self.campaign_config.get("primary_party", "BJP"),
                city=self.campaign_config.get("rally_location", {}).get("city", "Kolkata"),
            )
            self._llm_call_count += 1

        # ── Stage 7: Fuse results (priority: LLM > Transformer > Lexicon > Rules)
        final_sentiment = self._fuse_sentiment(rules_result, lexicon_result, transformer_sentiment, llm_result)
        final_emotions = self._fuse_emotions(transformer_emotions, llm_result)
        final_stance = self._extract_stance(llm_result)
        sarcasm_flag, sarcasm_conf = self._detect_sarcasm(rules_result, llm_result)

        # If sarcastic, invert sentiment
        if sarcasm_flag and final_sentiment.label == SentimentLabel.POSITIVE:
            final_sentiment = SentimentResult(
                label=SentimentLabel.SARCASTIC_POS,
                confidence=sarcasm_conf,
                method="sarcasm_inversion"
            )

        # ── Stage 8: Bot scoring
        author_dict = datapoint.author.model_dump() if datapoint.author else {}
        engagement_dict = datapoint.engagement.model_dump() if datapoint.engagement else {}
        bot_score = self.bot_detector.score(author_dict, text, engagement_dict)

        # ── Stage 9: Assemble NLP results
        datapoint.nlp_results = NLPResults(
            sentiment=final_sentiment,
            emotions=[EmotionScore(label=EmotionLabel(e["label"]), score=e["score"]) for e in final_emotions[:5]],
            stance=final_stance,
            entities=[EntityDetection(**e) for e in entities[:10]],
            topics=self._extract_topics(llm_result),
            sarcasm_flag=sarcasm_flag,
            sarcasm_confidence=sarcasm_conf,
            bot_suspicion_score=bot_score,
        )

        return datapoint

    def process_batch(self, datapoints: list[DataPoint]) -> list[DataPoint]:
        """Process a batch of DataPoints."""
        results = []
        for dp in datapoints:
            try:
                results.append(self.process(dp))
            except Exception as e:
                logger.error(f"NLP error for doc {dp.doc_id}: {e}")
                results.append(dp)
        logger.info(f"NLP Pipeline: processed batch of {len(results)} documents. LLM calls: {self._llm_call_count}")
        return results

    def _fuse_sentiment(self, rules, lexicon, transformer, llm) -> SentimentResult:
        """Fuse signals from all layers. LLM > Transformer > Lexicon."""
        if llm and "sentiment" in llm:
            s = llm["sentiment"]
            return SentimentResult(
                label=SentimentLabel(s.get("label", "neutral")),
                confidence=float(s.get("confidence", 0.8)),
                method="llm"
            )
        if transformer.get("confidence", 0) > 0.5:
            return SentimentResult(
                label=SentimentLabel(transformer.get("label", "neutral")),
                confidence=float(transformer.get("confidence", 0.0)),
                method="transformer"
            )
        return SentimentResult(
            label=SentimentLabel(lexicon.get("label", "neutral")),
            confidence=float(lexicon.get("confidence", 0.3)),
            method="lexicon"
        )

    def _fuse_emotions(self, transformer_emotions, llm) -> list[dict]:
        if llm and "emotions" in llm:
            return llm["emotions"]
        return transformer_emotions

    def _extract_stance(self, llm) -> StanceResult:
        if not llm:
            return StanceResult()
        # Map LLM response values to StanceLabel enum values
        # LLM may return "positive"/"negative" but StanceLabel uses "support"/"oppose"
        stance_map = {
            "support": "support", "oppose": "oppose", "neutral": "neutral",
            "positive": "support", "negative": "oppose",
            "pro": "support", "anti": "oppose", "against": "oppose",
        }
        def _map_stance(raw: str) -> str:
            return stance_map.get(raw.lower().strip(), "undetermined") if raw else "undetermined"

        return StanceResult(
            toward_leader=StanceLabel(_map_stance(llm.get("stance_toward_leader", "undetermined"))),
            toward_party=StanceLabel(_map_stance(llm.get("stance_toward_party", "undetermined"))),
            toward_rally=StanceLabel(_map_stance(llm.get("stance_toward_rally", "undetermined"))),
            confidence=0.75
        )

    def _detect_sarcasm(self, rules, llm) -> tuple[bool, float]:
        if llm and llm.get("is_sarcastic"):
            return True, float(llm.get("sarcasm_confidence", 0.7))
        if rules.get("sarcasm_signal", 0) > 0:
            return True, 0.5
        return False, 0.0

    def _extract_topics(self, llm) -> list[str]:
        if llm and "key_topics" in llm:
            return llm["key_topics"][:5]
        return []
