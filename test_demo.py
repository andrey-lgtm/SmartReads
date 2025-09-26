#!/usr/bin/env python3
"""
SmartReads Demo Test Script
Quick test to verify the recommendation engine works
"""

import sys
import os

def test_imports():
    """Test if all required modules can be imported"""
    print("Testing imports...")
    try:
        import numpy
        print("✓ NumPy installed")
    except ImportError:
        print("✗ NumPy not installed - run: pip3 install numpy")
        return False
    
    try:
        import pandas
        print("✓ Pandas installed")
    except ImportError:
        print("✗ Pandas not installed - run: pip3 install pandas")
        return False
    
    try:
        import sklearn
        print("✓ Scikit-learn installed")
    except ImportError:
        print("✗ Scikit-learn not installed - run: pip3 install scikit-learn")
        return False
    
    try:
        import fastapi
        print("✓ FastAPI installed")
    except ImportError:
        print("✗ FastAPI not installed - run: pip3 install fastapi")
        return False
    
    try:
        import uvicorn
        print("✓ Uvicorn installed")
    except ImportError:
        print("✗ Uvicorn not installed - run: pip3 install uvicorn")
        return False
    
    print("✓ All required packages installed!\n")
    return True

def test_recommendation_engine():
    """Test the core recommendation engine"""
    print("Testing recommendation engine...")
    
    try:
        from recommendation_engine import (
            SmartReadsRecommendationEngine,
            Book, Student, BorrowingRecord
        )
        from data_generator import generate_sample_data
        from datetime import datetime
        
        print("✓ Modules imported successfully")
        
        # Initialize engine
        engine = SmartReadsRecommendationEngine()
        print("✓ Engine initialized")
        
        # Generate sample data
        print("\nGenerating sample data...")
        books, students, records = generate_sample_data()
        print(f"✓ Generated {len(books)} books, {len(students)} students, {len(records)} records")
        
        # Load data
        engine.load_catalog(books)
        engine.load_students(students)
        engine.load_borrowing_history(records)
        print("✓ Data loaded into engine")
        
        # Test recommendation for first student
        test_student = students[0]
        print(f"\n{'='*60}")
        print(f"Testing recommendations for Student: {test_student.student_id}")
        print(f"Grade Level: {test_student.grade_level}")
        print(f"Reading Level: {test_student.reading_level}")
        print(f"Interests: {', '.join(test_student.interests)}")
        print(f"Preferred Genres: {', '.join(test_student.preferred_genres)}")
        print(f"Books Read: {len(test_student.reading_history)}")
        print(f"{'='*60}\n")
        
        # Get recommendations
        recommendations = engine.recommend(test_student.student_id, n_recommendations=5)
        
        if recommendations:
            print("✓ Recommendations generated successfully!\n")
            print("Top 5 Recommendations:")
            print("-" * 60)
            
            for i, rec in enumerate(recommendations, 1):
                print(f"\n{i}. {rec.book.title}")
                print(f"   Author: {rec.book.author}")
                print(f"   Genres: {', '.join(rec.book.genre)}")
                print(f"   Reading Level: {rec.book.reading_level}")
                print(f"   Score: {rec.score:.2%}")
                print(f"   Strategy: {rec.strategy.title()}")
                print(f"   Confidence: {rec.confidence:.2%}")
                print(f"   📚 Why: {rec.reason}")
        else:
            print("✗ No recommendations generated")
            return False
        
        # Test analytics
        print(f"\n{'='*60}")
        print("System Analytics")
        print("="*60)
        analytics = engine.get_analytics()
        print(f"Total Students: {analytics['total_students']}")
        print(f"Total Books: {analytics['total_books']}")
        print(f"Total Borrowing Records: {analytics['total_borrowing_records']}")
        print(f"Average Books per Student: {analytics['average_books_per_student']:.1f}")
        print(f"Catalog Coverage: {analytics['catalog_coverage']:.1%}")
        
        print("\n✓ All tests passed successfully!")
        return True
        
    except Exception as e:
        print(f"\n✗ Error during testing: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main test function"""
    print("="*60)
    print("SmartReads Recommendation System - Test Suite")
    print("="*60)
    print()
    
    # Test imports first
    if not test_imports():
        print("\n⚠️  Please install missing dependencies:")
        print("pip3 install -r requirements.txt")
        sys.exit(1)
    
    # Test recommendation engine
    if not test_recommendation_engine():
        print("\n⚠️  Recommendation engine test failed")
        sys.exit(1)
    
    print("\n" + "="*60)
    print("🎉 All tests passed! The system is ready to run.")
    print("="*60)
    print("\nTo start the web application, run:")
    print("  python3 app.py")
    print("\nThen open your browser to:")
    print("  http://localhost:8000")
    print()

if __name__ == "__main__":
    main()
