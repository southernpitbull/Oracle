"""
AI Evaluator module for sentiment analysis and text summarization
"""

from .config import (TRANSFORMERS_AVAILABLE, logger)


class AIEvaluator:
    def __init__(self):
        # Delay loading the pipeline until it's actually needed
        self.sentiment_analyzer = None
        self._initialized = False

    def _ensure_initialized(self):
        """Ensure the evaluator is properly initialized."""
        if self._initialized:
            return
        self._initialized = True

    def analyze_sentiment(self, text):
        if not TRANSFORMERS_AVAILABLE:
            logger.warning("Transformers not available, skipping sentiment analysis")
            return None

        try:
            self._ensure_initialized()
            
            if self.sentiment_analyzer is None:
                try:
                    from transformers.pipelines import pipeline  # type: ignore
                    self.sentiment_analyzer = pipeline("sentiment-analysis")  # type: ignore
                except Exception as e:
                    logger.error(f"Failed to load sentiment analyzer: {e}")
                    self.sentiment_analyzer = None
                    return None
            try:
                return self.sentiment_analyzer(text)  # type: ignore
            except Exception as e:
                logger.error(f"Sentiment analysis failed: {e}")
                return None
        except Exception as e:
            logger.error(f"Sentiment analysis initialization failed: {e}")
            return None

    def summarize_text(self, text, max_length=150, min_length=30):
        if not TRANSFORMERS_AVAILABLE:
            logger.warning("Transformers not available, skipping text summarization")
            return "Summarization not available - transformers package not installed"

        try:
            self._ensure_initialized()
            
            from transformers.pipelines import pipeline
            summarizer = pipeline("summarization")
            summary = summarizer(text, max_length=max_length, min_length=min_length, do_sample=False)
            return summary[0]['summary_text']
        except Exception as e:
            logger.error(f"Summarization failed: {e}")
            return f"Could not summarize: {e}"
