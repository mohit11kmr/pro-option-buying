import re
import json
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from collections import Counter
import random


class SentimentAnalyzer:
    def __init__(self):
        self.bullish_keywords = [
            'bullish', 'buy', 'long', 'up', 'gain', 'profit', 'rise', 'rally', 'surge',
            ' breakout', 'accumulation', 'support', 'calls', 'CE', 'target', 'moon', '🚀',
            'hold', 'breakout', 'moving up', 'positive', 'strong', 'growth', 'upgrade',
            'beat', 'excellent', 'good', 'recovery', 'recover', 'rebound'
        ]
        
        self.bearish_keywords = [
            'bearish', 'sell', 'short', 'down', 'loss', 'drop', 'fall', 'crash', 'decline',
            'breakdown', 'distribution', 'resistance', 'puts', 'PE', 'dump', 'crash', '�rizzly',
            'weak', 'negative', 'downgrade', 'miss', 'poor', 'sell off', 'fear', 'panic'
        ]
        
        self.market_indicators = {
            'fii': 'foreign_institutional',
            'dii': 'domestic_institutional',
            'fpi': 'foreign_portfolio',
            'nri': 'non_resident',
            'hedging': 'hedging_activity',
            'speculative': 'speculation'
        }
        
        self.sentiment_history = []
        
    def analyze_text(self, text: str) -> Dict:
        text_lower = text.lower()
        
        bullish_count = sum(1 for word in self.bullish_keywords if word in text_lower)
        bearish_count = sum(1 for word in self.bearish_keywords if word in text_lower)
        
        total = bullish_count + bearish_count
        
        if total == 0:
            sentiment_score = 0
            sentiment_label = "NEUTRAL"
        else:
            sentiment_score = (bullish_count - bearish_count) / total
            if sentiment_score > 0.3:
                sentiment_label = "STRONG_BULLISH"
            elif sentiment_score > 0.1:
                sentiment_label = "BULLISH"
            elif sentiment_score < -0.3:
                sentiment_label = "STRONG_BEARISH"
            elif sentiment_score < -0.1:
                sentiment_label = "BEARISH"
            else:
                sentiment_label = "NEUTRAL"
        
        intensity = min(abs(sentiment_score) * 100, 100)
        
        return {
            "sentiment_score": round(sentiment_score, 3),
            "sentiment_label": sentiment_label,
            "bullish_count": bullish_count,
            "bearish_count": bearish_count,
            "intensity": round(intensity, 1),
            "analyzed_at": datetime.now().isoformat()
        }
    
    def analyze_news(self, news_items: List[str]) -> Dict:
        if not news_items:
            return {
                "overall_sentiment": "NEUTRAL",
                "sentiment_score": 0,
                "bullish_signals": [],
                "bearish_signals": [],
                "market_mood": "neutral"
            }
        
        results = [self.analyze_text(news) for news in news_items]
        
        bullish_signals = []
        bearish_signals = []
        
        for i, news in enumerate(news_items):
            result = results[i]
            if result['sentiment_label'] in ['BULLISH', 'STRONG_BULLISH']:
                bullish_signals.append({"news": news[:100], "score": result['sentiment_score']})
            elif result['sentiment_label'] in ['BEARISH', 'STRONG_BEARISH']:
                bearish_signals.append({"news": news[:100], "score": result['sentiment_score']})
        
        avg_score = sum(r['sentiment_score'] for r in results) / len(results)
        
        if avg_score > 0.3:
            overall = "STRONG_BULLISH"
            mood = "greed"
        elif avg_score > 0.1:
            overall = "BULLISH"
            mood = "optimistic"
        elif avg_score < -0.3:
            overall = "STRONG_BEARISH"
            mood = "fear"
        elif avg_score < -0.1:
            overall = "BEARISH"
            mood = "pessimistic"
        else:
            overall = "NEUTRAL"
            mood = "neutral"
        
        return {
            "overall_sentiment": overall,
            "sentiment_score": round(avg_score, 3),
            "bullish_signals": bullish_signals[:5],
            "bearish_signals": bearish_signals[:5],
            "market_mood": mood,
            "total_news_analyzed": len(news_items),
            "analyzed_at": datetime.now().isoformat()
        }
    
    def analyze_social_media(self, posts: List[Dict]) -> Dict:
        if not posts:
            return {
                "sentiment": "NEUTRAL",
                "engagement_weighted_score": 0,
                "top_influencers": [],
                "trending_topics": []
            }
        
        weighted_scores = []
        influencers = []
        
        for post in posts:
            text = post.get('text', '')
            likes = post.get('likes', 0)
            shares = post.get('shares', 0)
            comments = post.get('comments', 0)
            author = post.get('author', 'unknown')
            
            sentiment = self.analyze_text(text)
            
            engagement = likes + (shares * 2) + (comments * 3)
            weight = min(engagement / 1000, 5)
            
            weighted_score = sentiment['sentiment_score'] * weight
            weighted_scores.append(weighted_score)
            
            if engagement > 1000:
                influencers.append({
                    "author": author,
                    "sentiment": sentiment['sentiment_label'],
                    "engagement": engagement
                })
        
        if weighted_scores:
            avg_score = sum(weighted_scores) / len(weighted_scores)
        else:
            avg_score = 0
        
        if avg_score > 0.3:
            sentiment = "BULLISH"
        elif avg_score < -0.3:
            sentiment = "BEARISH"
        else:
            sentiment = "NEUTRAL"
        
        influencers.sort(key=lambda x: x['engagement'], reverse=True)
        
        return {
            "sentiment": sentiment,
            "engagement_weighted_score": round(avg_score, 3),
            "top_influencers": influencers[:5],
            "total_posts_analyzed": len(posts),
            "analyzed_at": datetime.now().isoformat()
        }
    
    def analyze_market_sentiment_indicators(self, data: Dict) -> Dict:
        indicators = data.get('indicators', {})
        
        fii_activity = indicators.get('fii_activity', 0)
        dii_activity = indicators.get('dii_activity', 0)
        vix = indicators.get('vix', 15)
        put_call_ratio = indicators.get('put_call_ratio', 1.0)
        market_breadth = indicators.get('market_breadth', 0.5)
        
        sentiment_score = 0
        signals = []
        
        if fii_activity > 5000:
            sentiment_score += 0.3
            signals.append("FII buying detected")
        elif fii_activity < -5000:
            sentiment_score -= 0.3
            signals.append("FII selling detected")
        
        if vix > 25:
            sentiment_score -= 0.2
            signals.append("High volatility (fear)")
        elif vix < 12:
            sentiment_score += 0.2
            signals.append("Low volatility (complacency)")
        
        if put_call_ratio < 0.7:
            sentiment_score += 0.2
            signals.append("Low PCR - bullish signal")
        elif put_call_ratio > 1.3:
            sentiment_score -= 0.2
            signals.append("High PCR - bearish signal")
        
        if market_breadth > 0.6:
            sentiment_score += 0.2
            signals.append("Strong market breadth")
        elif market_breadth < 0.4:
            sentiment_score -= 0.2
            signals.append("Weak market breadth")
        
        if sentiment_score > 0.3:
            overall = "BULLISH"
        elif sentiment_score < -0.3:
            overall = "BEARISH"
        else:
            overall = "NEUTRAL"
        
        return {
            "overall_sentiment": overall,
            "sentiment_score": round(sentiment_score, 3),
            "signals": signals,
            "indicators": {
                "fii_activity": fii_activity,
                "dii_activity": dii_activity,
                "vix": vix,
                "put_call_ratio": put_call_ratio,
                "market_breadth": market_breadth
            },
            "analyzed_at": datetime.now().isoformat()
        }
    
    def generate_sentiment_summary(self, news: List[str], social_posts: List[Dict], market_data: Dict) -> Dict:
        news_sentiment = self.analyze_news(news)
        social_sentiment = self.analyze_social_media(social_posts)
        market_sentiment = self.analyze_market_sentiment_indicators(market_data)
        
        scores = [
            news_sentiment['sentiment_score'],
            social_sentiment['engagement_weighted_score'],
            market_sentiment['sentiment_score']
        ]
        
        avg_score = sum(scores) / len(scores)
        
        if avg_score > 0.25:
            recommendation = "BUY"
        elif avg_score > 0.1:
            recommendation = "ACCUMULATE"
        elif avg_score < -0.25:
            recommendation = "SELL"
        elif avg_score < -0.1:
            recommendation = "REDUCE"
        else:
            recommendation = "HOLD"
        
        return {
            "news_sentiment": news_sentiment,
            "social_sentiment": social_sentiment,
            "market_sentiment": market_sentiment,
            "combined_score": round(avg_score, 3),
            "recommendation": recommendation,
            "timestamp": datetime.now().isoformat()
        }


class NewsFetcher:
    def __init__(self):
        self.cached_news = []
        self.last_fetch = None
        
    def fetch_market_news(self, symbol: str = "NIFTY", max_items: int = 10) -> List[str]:
        import random
        bearish_news = [
            "FIIs sell ₹2000Cr worth of Indian equities amid global uncertainty",
            "NIFTY breaks below crucial support level amid selling pressure",
            "Global markets tumble on recession fears",
            "RBI signals hawkish stance, markets decline",
            "IT sector drags NIFTY lower amid earnings concerns",
            "Bank NIFTY under pressure from rate hike fears",
            "Crude oil surge weakens market sentiment",
            "Foreign investors pull out ₹5000Cr in past week",
            "US Fed hawkish comments impact emerging markets",
            "Q4 earnings disappoint, IT and finance drag"
        ]
        bullish_news = [
            "FIIs buy ₹2000Cr worth of Indian equities today",
            "NIFTY closes above key support level",
            "Global markets rally on positive cues",
            "RBI keeps rates steady, markets gain",
            "IT and pharma sectors lead the rally today",
            "Bank NIFTY shows strength amid positive earnings",
            "Crude oil prices ease, markets rally",
            "Domestic inflows continue to support markets",
            "US Fed signals dovish stance, markets up",
            "Q4 earnings season kicks off with positive surprises"
        ]
        
        is_bearish = random.random() < 0.5
        sample_news = bearish_news if is_bearish else bullish_news
        
        selected = random.sample(sample_news, min(max_items, len(sample_news)))
        
        self.cached_news = selected
        self.last_fetch = datetime.now()
        
        return selected
    
    def fetch_earnings_news(self, symbols: List[str]) -> Dict:
        news_dict = {}
        
        for symbol in symbols:
            news_dict[symbol] = [
                f"{symbol} reports quarterly results",
                f"{symbol} beats revenue estimates",
                f"Analysts upgrade {symbol} to BUY"
            ]
        
        return news_dict


class OptionsSentimentAnalyzer:
    def __init__(self):
        self.analyzer = SentimentAnalyzer()
        
    def analyze_options_data(self, options_chain: Dict) -> Dict:
        calls_oi = options_chain.get('calls_oi', 0)
        puts_oi = options_chain.get('puts_oi', 0)
        calls_change_oi = options_chain.get('calls_change_oi', 0)
        puts_change_oi = options_chain.get('puts_change_oi', 0)
        
        if calls_oi + puts_oi == 0:
            pcr = 1.0
        else:
            pcr = puts_oi / calls_oi
        
        if pcr < 0.7:
            sentiment = "STRONG_BULLISH"
            signal = "Low PCR indicates bullish sentiment"
        elif pcr < 1.0:
            sentiment = "BULLISH"
            signal = "Slightly low PCR"
        elif pcr > 1.5:
            sentiment = "STRONG_BEARISH"
            signal = "High PCR indicates bearish sentiment"
        elif pcr > 1.0:
            sentiment = "BEARISH"
            signal = "Slightly high PCR"
        else:
            sentiment = "NEUTRAL"
            signal = "Balanced PCR"
        
        max_pain = options_chain.get('max_pain', 0)
        support_levels = options_chain.get('support_levels', [])
        resistance_levels = options_chain.get('resistance_levels', [])
        
        return {
            "sentiment": sentiment,
            "signal": signal,
            "put_call_ratio": round(pcr, 2),
            "calls_oi": calls_oi,
            "puts_oi": puts_oi,
            "calls_change_oi": calls_change_oi,
            "puts_change_oi": puts_change_oi,
            "max_pain": max_pain,
            "support_levels": support_levels,
            "resistance_levels": resistance_levels,
            "interpretation": self._interpret_options_sentiment(pcr, calls_change_oi, puts_change_oi),
            "timestamp": datetime.now().isoformat()
        }
    
    def _interpret_options_sentiment(self, pcr: float, calls_change: float, puts_change: float) -> str:
        interpretations = []
        
        if pcr < 0.8:
            interpretations.append("Bearish bias among options writers")
        elif pcr > 1.2:
            interpretations.append("Hedging activity from institutional players")
        
        if calls_change > puts_change * 1.5:
            interpretations.append("Fresh call writing indicates resistance building")
        elif puts_change > calls_change * 1.5:
            interpretations.append("Put buying indicates support being built")
        
        if not interpretations:
            return "No clear directional bias in options market"
        
        return " | ".join(interpretations)


if __name__ == "__main__":
    analyzer = SentimentAnalyzer()
    
    news = [
        "NIFTY breaks out above 25000 resistance with strong volume",
        "FIIs buy 2000Cr in Indian markets today",
        "IT stocks lead the rally amid positive earnings",
        "Global markets cautious ahead of Fed meeting",
        "Bank NIFTY shows weakness on interest rate fears"
    ]
    
    result = analyzer.analyze_news(news)
    print(json.dumps(result, indent=2))
