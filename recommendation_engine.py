"""
SmartReads Recommendation Engine
Core recommendation system combining collaborative filtering, content-based filtering, and LLM enhancement
"""

import json
import numpy as np
import pandas as pd
from typing import List, Dict, Tuple, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import random
from collections import defaultdict
import logging
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.decomposition import TruncatedSVD
import hashlib

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class Book:
    """Represents a book in the library catalog"""
    book_id: str
    title: str
    author: str
    isbn: str
    genre: List[str]
    subject: List[str]
    reading_level: str  # K-2, 3-5, 6-8, 9-12
    description: str
    publication_year: int
    page_count: int
    language: str = "English"
    available_copies: int = 1
    total_copies: int = 1
    popularity_score: float = 0.0
    
    def to_dict(self) -> Dict:
        """Convert book to dictionary"""
        return {
            'book_id': self.book_id,
            'title': self.title,
            'author': self.author,
            'isbn': self.isbn,
            'genre': self.genre,
            'subject': self.subject,
            'reading_level': self.reading_level,
            'description': self.description,
            'publication_year': self.publication_year,
            'page_count': self.page_count,
            'language': self.language,
            'available_copies': self.available_copies,
            'total_copies': self.total_copies,
            'popularity_score': self.popularity_score
        }

@dataclass
class Student:
    """Represents a student user"""
    student_id: str
    grade_level: int
    reading_level: str
    preferred_genres: List[str] = field(default_factory=list)
    interests: List[str] = field(default_factory=list)
    reading_history: List[str] = field(default_factory=list)  # List of book_ids
    
    def to_dict(self) -> Dict:
        """Convert student to dictionary"""
        return {
            'student_id': self.student_id,
            'grade_level': self.grade_level,
            'reading_level': self.reading_level,
            'preferred_genres': self.preferred_genres,
            'interests': self.interests,
            'reading_history': self.reading_history
        }

@dataclass
class BorrowingRecord:
    """Represents a book borrowing transaction"""
    student_id: str
    book_id: str
    borrow_date: datetime
    return_date: Optional[datetime]
    rating: Optional[int] = None  # 1-5 scale
    completed: bool = False

@dataclass
class Recommendation:
    """Represents a book recommendation with explanation"""
    book: Book
    score: float
    reason: str
    strategy: str  # 'collaborative', 'content', 'llm', 'hybrid'
    confidence: float  # 0.0 to 1.0
    
    def to_dict(self) -> Dict:
        """Convert recommendation to dictionary"""
        return {
            'book': self.book.to_dict(),
            'score': self.score,
            'reason': self.reason,
            'strategy': self.strategy,
            'confidence': self.confidence
        }

class CollaborativeFilter:
    """Collaborative filtering recommendation engine"""
    
    def __init__(self):
        self.user_item_matrix = None
        self.user_similarity_matrix = None
        self.item_similarity_matrix = None
        self.svd_model = None
        
    def fit(self, borrowing_records: List[BorrowingRecord]):
        """Train the collaborative filtering model"""
        logger.info("Training collaborative filter...")
        
        # Create user-item matrix
        user_ids = list(set([r.student_id for r in borrowing_records]))
        book_ids = list(set([r.book_id for r in borrowing_records]))
        
        # Initialize matrix
        self.user_item_matrix = pd.DataFrame(
            0, 
            index=user_ids, 
            columns=book_ids
        )
        
        # Fill matrix with ratings (implicit feedback: 1 for borrowed)
        for record in borrowing_records:
            value = 1  # Base value for borrowing
            if record.rating:
                value = record.rating / 5.0  # Normalize rating
            elif record.completed:
                value = 1.2  # Bonus for completed books
            
            self.user_item_matrix.loc[record.student_id, record.book_id] = value
        
        # Calculate user similarity matrix (cosine similarity)
        if len(user_ids) > 1:
            user_vectors = self.user_item_matrix.values
            self.user_similarity_matrix = cosine_similarity(user_vectors)
            self.user_similarity_matrix = pd.DataFrame(
                self.user_similarity_matrix,
                index=user_ids,
                columns=user_ids
            )
        
        # Calculate item similarity matrix
        if len(book_ids) > 1:
            item_vectors = self.user_item_matrix.T.values
            self.item_similarity_matrix = cosine_similarity(item_vectors)
            self.item_similarity_matrix = pd.DataFrame(
                self.item_similarity_matrix,
                index=book_ids,
                columns=book_ids
            )
        
        # Train SVD for matrix factorization (handle cold start better)
        if len(user_ids) > 2 and len(book_ids) > 2:
            self.svd_model = TruncatedSVD(n_components=min(10, len(user_ids)-1, len(book_ids)-1))
            self.svd_model.fit(self.user_item_matrix.values)
            
        logger.info(f"Collaborative filter trained with {len(user_ids)} users and {len(book_ids)} books")
    
    def recommend(self, student_id: str, n_recommendations: int = 10) -> List[Tuple[str, float]]:
        """Generate recommendations using collaborative filtering"""
        if self.user_item_matrix is None:
            return []
        
        if student_id not in self.user_item_matrix.index:
            # Cold start - return popular items
            popularity = self.user_item_matrix.sum(axis=0)
            return list(zip(popularity.nlargest(n_recommendations).index, 
                          popularity.nlargest(n_recommendations).values))
        
        # Get similar users
        if self.user_similarity_matrix is not None:
            similar_users = self.user_similarity_matrix[student_id].nlargest(6).index[1:]  # Top 5 similar users
            
            # Aggregate preferences of similar users
            recommendations = defaultdict(float)
            for user in similar_users:
                similarity_score = self.user_similarity_matrix.loc[student_id, user]
                user_books = self.user_item_matrix.loc[user]
                for book_id, rating in user_books[user_books > 0].items():
                    if self.user_item_matrix.loc[student_id, book_id] == 0:  # Not already read
                        recommendations[book_id] += rating * similarity_score
            
            # Sort and return top N
            sorted_recs = sorted(recommendations.items(), key=lambda x: x[1], reverse=True)
            return sorted_recs[:n_recommendations]
        
        return []

class ContentBasedFilter:
    """Content-based filtering recommendation engine"""
    
    def __init__(self):
        self.tfidf_vectorizer = TfidfVectorizer(max_features=1000, stop_words='english')
        self.book_features = None
        self.book_ids = []
        
    def fit(self, books: List[Book]):
        """Train the content-based filter"""
        logger.info("Training content-based filter...")
        
        # Create feature text for each book
        feature_texts = []
        self.book_ids = []
        
        for book in books:
            feature_text = f"{book.title} {book.author} {' '.join(book.genre)} {' '.join(book.subject)} {book.description}"
            feature_texts.append(feature_text)
            self.book_ids.append(book.book_id)
        
        # Create TF-IDF matrix
        if feature_texts:
            self.book_features = self.tfidf_vectorizer.fit_transform(feature_texts)
            logger.info(f"Content-based filter trained with {len(books)} books")
        
    def recommend(self, student: Student, books_dict: Dict[str, Book], n_recommendations: int = 10) -> List[Tuple[str, float]]:
        """Generate recommendations using content-based filtering"""
        if self.book_features is None or not student.reading_history:
            return []
        
        # Get indices of books in reading history
        history_indices = []
        for book_id in student.reading_history[-10:]:  # Use last 10 books
            if book_id in self.book_ids:
                history_indices.append(self.book_ids.index(book_id))
        
        if not history_indices:
            return []
        
        # Calculate average feature vector of reading history
        history_vectors = self.book_features[history_indices]
        avg_profile = np.asarray(history_vectors.mean(axis=0)).reshape(1, -1)
        
        # Calculate similarity with all books
        similarities = cosine_similarity(avg_profile, self.book_features).flatten()
        
        # Filter out already read books and sort
        recommendations = []
        for idx, score in enumerate(similarities):
            book_id = self.book_ids[idx]
            if book_id not in student.reading_history:
                recommendations.append((book_id, float(score)))
        
        recommendations.sort(key=lambda x: x[1], reverse=True)
        return recommendations[:n_recommendations]

class LLMRecommender:
    """LLM-based recommendation enhancement"""
    
    def __init__(self, use_mock: bool = True):
        self.use_mock = use_mock
        
    def enhance_recommendation(self, student: Student, book: Book, base_score: float) -> Tuple[float, str]:
        """
        Enhance recommendation with LLM reasoning
        Returns enhanced score and explanation
        """
        if self.use_mock:
            return self._mock_llm_enhancement(student, book, base_score)
        else:
            # In production, this would call actual LLM API
            return self._real_llm_enhancement(student, book, base_score)
    
    def _mock_llm_enhancement(self, student: Student, book: Book, base_score: float) -> Tuple[float, str]:
        """Mock LLM enhancement for demo purposes"""
        reasons = []
        score_boost = 0.0
        
        # Check genre match
        matched_genres = [g for g in book.genre if g in student.preferred_genres]
        if matched_genres:
            score_boost += 0.1
            reasons.append(f"matches your preferred genre of {matched_genres[0]}")
        
        # Check reading level appropriateness
        if book.reading_level == student.reading_level:
            score_boost += 0.05
            reasons.append("is at your reading level")
        
        # Check interests alignment
        interest_keywords = set(word.lower() for interest in student.interests for word in interest.split())
        description_words = set(book.description.lower().split())
        if interest_keywords & description_words:
            score_boost += 0.15
            matched = list(interest_keywords & description_words)[0]
            reasons.append(f"relates to your interest in {matched}")
        
        # Generate explanation
        if reasons:
            explanation = f"This book is recommended because it {' and '.join(reasons)}."
        else:
            explanation = "This book offers a new reading experience to expand your horizons."
        
        enhanced_score = min(1.0, base_score + score_boost)
        return enhanced_score, explanation
    
    def _real_llm_enhancement(self, student: Student, book: Book, base_score: float) -> Tuple[float, str]:
        """
        Actual LLM API call (placeholder for real implementation)
        In production, this would call OpenAI/Claude API
        """
        # This would construct a prompt and call the LLM API
        prompt = f"""
        Analyze this book recommendation:
        Student Profile:
        - Grade Level: {student.grade_level}
        - Reading Level: {student.reading_level}
        - Interests: {', '.join(student.interests)}
        - Preferred Genres: {', '.join(student.preferred_genres)}
        
        Book:
        - Title: {book.title}
        - Author: {book.author}
        - Genre: {', '.join(book.genre)}
        - Description: {book.description}
        
        Provide:
        1. A score adjustment (-0.2 to +0.2)
        2. A brief, student-friendly explanation of why this book is recommended
        """
        
        # Simulated API response
        return base_score + 0.1, "This book matches your interests and reading level perfectly!"

class SmartReadsRecommendationEngine:
    """Main recommendation engine combining all strategies"""
    
    def __init__(self):
        self.collaborative_filter = CollaborativeFilter()
        self.content_filter = ContentBasedFilter()
        self.llm_recommender = LLMRecommender(use_mock=True)
        self.books_catalog: Dict[str, Book] = {}
        self.students: Dict[str, Student] = {}
        self.borrowing_records: List[BorrowingRecord] = []
        
    def load_catalog(self, books: List[Book]):
        """Load books into the catalog"""
        for book in books:
            self.books_catalog[book.book_id] = book
        self.content_filter.fit(books)
        logger.info(f"Loaded {len(books)} books into catalog")
        
    def load_students(self, students: List[Student]):
        """Load student profiles"""
        for student in students:
            self.students[student.student_id] = student
        logger.info(f"Loaded {len(students)} student profiles")
        
    def load_borrowing_history(self, records: List[BorrowingRecord]):
        """Load borrowing history"""
        self.borrowing_records = records
        self.collaborative_filter.fit(records)
        
        # Update popularity scores
        borrow_counts = defaultdict(int)
        for record in records:
            borrow_counts[record.book_id] += 1
        
        max_count = max(borrow_counts.values()) if borrow_counts else 1
        for book_id, count in borrow_counts.items():
            if book_id in self.books_catalog:
                self.books_catalog[book_id].popularity_score = count / max_count
        
        logger.info(f"Loaded {len(records)} borrowing records")
    
    def recommend(self, student_id: str, n_recommendations: int = 10) -> List[Recommendation]:
        """
        Generate personalized book recommendations
        Combines collaborative, content-based, and LLM strategies
        """
        if student_id not in self.students:
            logger.warning(f"Student {student_id} not found")
            return self._get_popular_books(n_recommendations)
        
        student = self.students[student_id]
        recommendations = []
        
        # Strategy 1: Collaborative Filtering
        collab_recs = self.collaborative_filter.recommend(student_id, n_recommendations * 2)
        for book_id, score in collab_recs[:n_recommendations//2]:
            if book_id in self.books_catalog:
                book = self.books_catalog[book_id]
                enhanced_score, explanation = self.llm_recommender.enhance_recommendation(student, book, score)
                recommendations.append(Recommendation(
                    book=book,
                    score=enhanced_score,
                    reason=explanation,
                    strategy='collaborative',
                    confidence=min(1.0, len(student.reading_history) / 10)  # Higher confidence with more history
                ))
        
        # Strategy 2: Content-Based Filtering
        content_recs = self.content_filter.recommend(student, self.books_catalog, n_recommendations * 2)
        for book_id, score in content_recs[:n_recommendations//2]:
            if book_id in self.books_catalog:
                book = self.books_catalog[book_id]
                # Avoid duplicates
                if not any(r.book.book_id == book_id for r in recommendations):
                    enhanced_score, explanation = self.llm_recommender.enhance_recommendation(student, book, score)
                    recommendations.append(Recommendation(
                        book=book,
                        score=enhanced_score,
                        reason=explanation,
                        strategy='content',
                        confidence=min(1.0, len(student.reading_history) / 5)
                    ))
        
        # Strategy 3: Diversity Enhancement - Add books from unexplored genres
        if len(recommendations) < n_recommendations:
            explored_genres = set()
            for book_id in student.reading_history:
                if book_id in self.books_catalog:
                    explored_genres.update(self.books_catalog[book_id].genre)
            
            for book in self.books_catalog.values():
                if book.book_id not in student.reading_history:
                    new_genres = set(book.genre) - explored_genres
                    if new_genres and book.reading_level == student.reading_level:
                        recommendations.append(Recommendation(
                            book=book,
                            score=0.7 + book.popularity_score * 0.3,
                            reason=f"Explore a new genre: {list(new_genres)[0]}. This highly-rated book will broaden your reading horizons.",
                            strategy='diversity',
                            confidence=0.6
                        ))
                        if len(recommendations) >= n_recommendations:
                            break
        
        # Sort by score and return top N
        recommendations.sort(key=lambda x: x.score, reverse=True)
        return recommendations[:n_recommendations]
    
    def _get_popular_books(self, n: int) -> List[Recommendation]:
        """Fallback to popular books for cold start"""
        popular_books = sorted(
            self.books_catalog.values(), 
            key=lambda x: x.popularity_score, 
            reverse=True
        )[:n]
        
        return [
            Recommendation(
                book=book,
                score=book.popularity_score,
                reason="This is one of our most popular books that many students have enjoyed!",
                strategy='popularity',
                confidence=0.5
            )
            for book in popular_books
        ]
    
    def explain_recommendation(self, recommendation: Recommendation) -> str:
        """Generate detailed explanation for a recommendation"""
        explanation = f"📚 {recommendation.book.title} by {recommendation.book.author}\n\n"
        explanation += f"Why this book?\n{recommendation.reason}\n\n"
        explanation += f"Details:\n"
        explanation += f"- Genres: {', '.join(recommendation.book.genre)}\n"
        explanation += f"- Reading Level: {recommendation.book.reading_level}\n"
        explanation += f"- Pages: {recommendation.book.page_count}\n"
        explanation += f"- Recommendation Confidence: {recommendation.confidence:.0%}\n"
        explanation += f"- Strategy Used: {recommendation.strategy.title()}-based recommendation\n"
        return explanation
    
    def get_analytics(self) -> Dict[str, Any]:
        """Generate analytics about the recommendation system"""
        total_students = len(self.students)
        total_books = len(self.books_catalog)
        total_borrows = len(self.borrowing_records)
        
        # Calculate reading diversity
        genre_distribution = defaultdict(int)
        for record in self.borrowing_records:
            if record.book_id in self.books_catalog:
                for genre in self.books_catalog[record.book_id].genre:
                    genre_distribution[genre] += 1
        
        # Most active readers
        student_activity = defaultdict(int)
        for record in self.borrowing_records:
            student_activity[record.student_id] += 1
        
        most_active = sorted(student_activity.items(), key=lambda x: x[1], reverse=True)[:5]
        
        return {
            'total_students': total_students,
            'total_books': total_books,
            'total_borrowing_records': total_borrows,
            'average_books_per_student': total_borrows / total_students if total_students > 0 else 0,
            'genre_distribution': dict(genre_distribution),
            'most_active_readers': most_active,
            'catalog_coverage': len(set(r.book_id for r in self.borrowing_records)) / total_books if total_books > 0 else 0
        }

# Example usage and testing
if __name__ == "__main__":
    # Initialize the recommendation engine
    engine = SmartReadsRecommendationEngine()
    
    # Create sample data for demonstration
    from data_generator import generate_sample_data
    books, students, records = generate_sample_data()
    
    # Load data into the engine
    engine.load_catalog(books)
    engine.load_students(students)
    engine.load_borrowing_history(records)
    
    # Generate recommendations for a sample student
    sample_student_id = students[0].student_id
    recommendations = engine.recommend(sample_student_id, n_recommendations=5)
    
    print(f"\n{'='*60}")
    print(f"Recommendations for Student {sample_student_id}")
    print(f"{'='*60}\n")
    
    for i, rec in enumerate(recommendations, 1):
        print(f"{i}. {rec.book.title}")
        print(f"   Author: {rec.book.author}")
        print(f"   Score: {rec.score:.2f}")
        print(f"   Strategy: {rec.strategy}")
        print(f"   Reason: {rec.reason}")
        print()
    
    # Show analytics
    print(f"\n{'='*60}")
    print("System Analytics")
    print(f"{'='*60}\n")
    analytics = engine.get_analytics()
    for key, value in analytics.items():
        if isinstance(value, float):
            print(f"{key}: {value:.2f}")
        else:
            print(f"{key}: {value}")
