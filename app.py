"""
SmartReads Web Application
FastAPI-based proof-of-concept for the book recommendation system
"""

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Optional, Any
from contextlib import asynccontextmanager
import json
import os
from datetime import datetime
import uvicorn

from recommendation_engine import (
    SmartReadsRecommendationEngine,
    Book, Student, BorrowingRecord, Recommendation
)
from data_generator import generate_sample_data

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    initialize_engine()
    yield
    # Shutdown (if needed)

# Initialize FastAPI app
app = FastAPI(
    title="SmartReads Book Recommendation System",
    description="AI-powered book recommendations for school districts",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global recommendation engine instance
recommendation_engine = None

# Pydantic models for API
class BookResponse(BaseModel):
    book_id: str
    title: str
    author: str
    isbn: str
    genre: List[str]
    subject: List[str]
    reading_level: str
    description: str
    publication_year: int
    page_count: int
    popularity_score: float
    average_rating: float = 0.0
    rating_count: int = 0

class StudentResponse(BaseModel):
    student_id: str
    grade_level: int
    reading_level: str
    preferred_genres: List[str]
    interests: List[str]
    reading_history: List[str]
    books_read_count: int

class RecommendationResponse(BaseModel):
    book: BookResponse
    score: float
    reason: str
    strategy: str
    confidence: float

class AnalyticsResponse(BaseModel):
    total_students: int
    total_books: int
    total_borrowing_records: int
    average_books_per_student: float
    catalog_coverage: float
    genre_distribution: Dict[str, int]

def initialize_engine():
    """Initialize the recommendation engine with sample data"""
    global recommendation_engine
    
    print("Initializing recommendation engine...")
    recommendation_engine = SmartReadsRecommendationEngine()
    
    # Check if data files exist
    data_dir = "data"
    if not os.path.exists(data_dir):
        os.makedirs(data_dir, exist_ok=True)
    
    books_file = os.path.join(data_dir, "books.json")
    students_file = os.path.join(data_dir, "students.json")
    history_file = os.path.join(data_dir, "borrowing_history.json")
    
    # Generate or load data
    if not all(os.path.exists(f) for f in [books_file, students_file, history_file]):
        print("Generating sample data...")
        books, students, records = generate_sample_data()
        
        # Save to files for persistence
        with open(books_file, 'w') as f:
            json.dump([b.to_dict() for b in books], f)
        with open(students_file, 'w') as f:
            json.dump([s.to_dict() for s in students], f)
        with open(history_file, 'w') as f:
            records_data = [{
                'student_id': r.student_id,
                'book_id': r.book_id,
                'borrow_date': r.borrow_date.isoformat(),
                'return_date': r.return_date.isoformat() if r.return_date else None,
                'rating': r.rating,
                'completed': r.completed
            } for r in records]
            json.dump(records_data, f)
    else:
        print("Loading existing data...")
        # Load from files
        with open(books_file, 'r') as f:
            books_data = json.load(f)
            books = [Book(**b) for b in books_data]
        
        with open(students_file, 'r') as f:
            students_data = json.load(f)
            students = [Student(**s) for s in students_data]
        
        with open(history_file, 'r') as f:
            records_data = json.load(f)
            records = [BorrowingRecord(
                student_id=r['student_id'],
                book_id=r['book_id'],
                borrow_date=datetime.fromisoformat(r['borrow_date']),
                return_date=datetime.fromisoformat(r['return_date']) if r['return_date'] else None,
                rating=r['rating'],
                completed=r['completed']
            ) for r in records_data]
    
    # Load data into engine
    recommendation_engine.load_catalog(books)
    recommendation_engine.load_students(students)
    recommendation_engine.load_borrowing_history(records)
    
    print(f"Engine initialized with {len(books)} books, {len(students)} students, and {len(records)} borrowing records")

@app.get("/", response_class=HTMLResponse)
async def home():
    """Serve the main HTML interface"""
    return HTML_CONTENT

@app.get("/api/students", response_model=List[StudentResponse])
async def get_students():
    """Get all students"""
    if not recommendation_engine:
        raise HTTPException(status_code=500, detail="Engine not initialized")
    
    students = []
    for student_id, student in recommendation_engine.students.items():
        students.append(StudentResponse(
            student_id=student.student_id,
            grade_level=student.grade_level,
            reading_level=student.reading_level,
            preferred_genres=student.preferred_genres,
            interests=student.interests,
            reading_history=student.reading_history,
            books_read_count=len(student.reading_history)
        ))
    
    # Sort by student ID
    students.sort(key=lambda x: x.student_id)
    return students

@app.get("/api/students/{student_id}", response_model=StudentResponse)
async def get_student(student_id: str):
    """Get a specific student"""
    if not recommendation_engine:
        raise HTTPException(status_code=500, detail="Engine not initialized")
    
    if student_id not in recommendation_engine.students:
        raise HTTPException(status_code=404, detail="Student not found")
    
    student = recommendation_engine.students[student_id]
    return StudentResponse(
        student_id=student.student_id,
        grade_level=student.grade_level,
        reading_level=student.reading_level,
        preferred_genres=student.preferred_genres,
        interests=student.interests,
        reading_history=student.reading_history,
        books_read_count=len(student.reading_history)
    )

@app.get("/api/books", response_model=List[BookResponse])
async def get_books(limit: int = 50):
    """Get all books"""
    if not recommendation_engine:
        raise HTTPException(status_code=500, detail="Engine not initialized")
    
    books = []
    for book_id, book in list(recommendation_engine.books_catalog.items())[:limit]:
        books.append(BookResponse(
            book_id=book.book_id,
            title=book.title,
            author=book.author,
            isbn=book.isbn,
            genre=book.genre,
            subject=book.subject,
            reading_level=book.reading_level,
            description=book.description,
            publication_year=book.publication_year,
            page_count=book.page_count,
            popularity_score=book.popularity_score,
            average_rating=book.average_rating,
            rating_count=book.rating_count
        ))
    
    return books

@app.get("/api/recommendations/{student_id}", response_model=List[RecommendationResponse])
async def get_recommendations(student_id: str, n: int = 10):
    """Get book recommendations for a student"""
    if not recommendation_engine:
        raise HTTPException(status_code=500, detail="Engine not initialized")
    
    try:
        recommendations = recommendation_engine.recommend(student_id, n)
        
        responses = []
        for rec in recommendations:
            responses.append(RecommendationResponse(
                book=BookResponse(
                    book_id=rec.book.book_id,
                    title=rec.book.title,
                    author=rec.book.author,
                    isbn=rec.book.isbn,
                    genre=rec.book.genre,
                    subject=rec.book.subject,
                    reading_level=rec.book.reading_level,
                    description=rec.book.description,
                    publication_year=rec.book.publication_year,
                    page_count=rec.book.page_count,
                    popularity_score=rec.book.popularity_score,
                    average_rating=rec.book.average_rating,
                    rating_count=rec.book.rating_count
                ),
                score=rec.score,
                reason=rec.reason,
                strategy=rec.strategy,
                confidence=rec.confidence
            ))
        
        return responses
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/analytics", response_model=AnalyticsResponse)
async def get_analytics():
    """Get system analytics"""
    if not recommendation_engine:
        raise HTTPException(status_code=500, detail="Engine not initialized")
    
    analytics = recommendation_engine.get_analytics()
    
    return AnalyticsResponse(
        total_students=analytics['total_students'],
        total_books=analytics['total_books'],
        total_borrowing_records=analytics['total_borrowing_records'],
        average_books_per_student=analytics['average_books_per_student'],
        catalog_coverage=analytics['catalog_coverage'],
        genre_distribution=analytics['genre_distribution']
    )

@app.post("/api/regenerate-data")
async def regenerate_data():
    """Regenerate sample data and reinitialize the engine"""
    try:
        # Delete existing data files
        data_files = ["data/books.json", "data/students.json", "data/borrowing_history.json"]
        for file in data_files:
            if os.path.exists(file):
                os.remove(file)
        
        # Reinitialize engine with new data
        initialize_engine()
        
        return {"message": "Data regenerated successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# HTML content for the web interface
HTML_CONTENT = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SmartReads - Book Recommendation System</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        
        .container {
            max-width: 1200px;
            margin: 0 auto;
        }
        
        header {
            text-align: center;
            color: white;
            margin-bottom: 40px;
        }
        
        h1 {
            font-size: 3em;
            margin-bottom: 10px;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.2);
        }
        
        .subtitle {
            font-size: 1.2em;
            opacity: 0.9;
        }
        
        .main-content {
            background: white;
            border-radius: 20px;
            padding: 30px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
        }
        
        .section {
            margin-bottom: 30px;
        }
        
        .section-title {
            font-size: 1.5em;
            color: #333;
            margin-bottom: 15px;
            padding-bottom: 10px;
            border-bottom: 2px solid #667eea;
        }
        
        .controls {
            display: flex;
            gap: 15px;
            margin-bottom: 20px;
            flex-wrap: wrap;
        }
        
        select, button {
            padding: 10px 20px;
            font-size: 1em;
            border-radius: 8px;
            border: 2px solid #667eea;
            background: white;
            color: #333;
            cursor: pointer;
            transition: all 0.3s ease;
        }
        
        button {
            background: #667eea;
            color: white;
            font-weight: bold;
        }
        
        button:hover {
            background: #764ba2;
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(0,0,0,0.2);
        }
        
        select:focus {
            outline: none;
            border-color: #764ba2;
        }
        
        .student-info {
            background: #f8f9fa;
            padding: 20px;
            border-radius: 10px;
            margin-bottom: 20px;
        }
        
        .student-info h3 {
            color: #667eea;
            margin-bottom: 10px;
        }
        
        .info-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin-top: 10px;
        }
        
        .info-item {
            display: flex;
            flex-direction: column;
        }
        
        .info-label {
            font-weight: bold;
            color: #666;
            font-size: 0.9em;
            margin-bottom: 5px;
        }
        
        .info-value {
            color: #333;
        }
        
        .tag {
            display: inline-block;
            background: #667eea;
            color: white;
            padding: 3px 8px;
            border-radius: 4px;
            margin: 2px;
            font-size: 0.9em;
        }
        
        .tag-subject {
            display: inline-block;
            background: #e0e0e0;
            color: #555;
            padding: 3px 8px;
            border-radius: 4px;
            margin: 2px;
            font-size: 0.85em;
            cursor: help;
        }
        
        .tag-highlight {
            display: inline-block;
            background: #ffd700;
            color: #333;
            padding: 3px 8px;
            border-radius: 4px;
            margin: 2px;
            font-size: 0.85em;
            font-weight: bold;
            box-shadow: 0 0 8px rgba(255, 215, 0, 0.5);
            animation: pulse 2s ease-in-out infinite;
            cursor: help;
        }
        
        @keyframes pulse {
            0%, 100% { box-shadow: 0 0 8px rgba(255, 215, 0, 0.5); }
            50% { box-shadow: 0 0 15px rgba(255, 215, 0, 0.8); }
        }
        
        .book-subjects {
            margin-bottom: 10px;
            font-size: 0.9em;
            color: #555;
        }
        
        .book-subjects strong {
            color: #333;
            margin-right: 5px;
        }
        
        .recommendations {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
            gap: 20px;
        }
        
        .recommendation-card {
            background: white;
            border: 2px solid #e0e0e0;
            border-radius: 10px;
            padding: 20px;
            transition: all 0.3s ease;
        }
        
        .recommendation-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 10px 30px rgba(0,0,0,0.1);
            border-color: #667eea;
        }
        
        .book-title {
            font-size: 1.2em;
            font-weight: bold;
            color: #333;
            margin-bottom: 5px;
        }
        
        .book-author {
            color: #666;
            margin-bottom: 10px;
        }
        
        .book-details {
            font-size: 0.9em;
            color: #666;
            margin-bottom: 10px;
        }
        
        .book-genres {
            margin-bottom: 10px;
        }
        
        .recommendation-reason {
            background: #f0f4ff;
            padding: 10px;
            border-radius: 8px;
            margin: 10px 0;
            font-style: italic;
            color: #555;
        }
        
        .score-bar {
            display: flex;
            align-items: center;
            gap: 10px;
            margin-top: 10px;
        }
        
        .score-label {
            font-weight: bold;
            color: #667eea;
            min-width: 80px;
        }
        
        .score-progress {
            flex: 1;
            height: 10px;
            background: #e0e0e0;
            border-radius: 5px;
            overflow: hidden;
        }
        
        .score-fill {
            height: 100%;
            background: linear-gradient(90deg, #667eea, #764ba2);
            transition: width 0.5s ease;
        }
        
        .strategy-badge {
            display: inline-block;
            background: #28a745;
            color: white;
            padding: 3px 8px;
            border-radius: 4px;
            font-size: 0.8em;
            font-weight: bold;
            text-transform: uppercase;
            margin-top: 10px;
        }
        
        .analytics {
            background: #f8f9fa;
            padding: 20px;
            border-radius: 10px;
            margin-top: 20px;
        }
        
        .stat-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 20px;
            margin-top: 15px;
        }
        
        .stat-card {
            text-align: center;
            padding: 15px;
            background: white;
            border-radius: 8px;
            border: 1px solid #e0e0e0;
        }
        
        .stat-value {
            font-size: 2em;
            font-weight: bold;
            color: #667eea;
        }
        
        .stat-label {
            color: #666;
            font-size: 0.9em;
            margin-top: 5px;
        }
        
        .loading {
            text-align: center;
            padding: 40px;
            color: #666;
        }
        
        .loading::after {
            content: '...';
            animation: dots 1.5s infinite;
        }
        
        @keyframes dots {
            0%, 20% { content: '.'; }
            40% { content: '..'; }
            60%, 100% { content: '...'; }
        }
        
        .error {
            background: #fee;
            color: #c00;
            padding: 15px;
            border-radius: 8px;
            margin: 20px 0;
        }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>📚 SmartReads</h1>
            <p class="subtitle">AI-Powered Book Recommendation System for School Districts</p>
        </header>
        
        <div class="main-content">
            <div class="section">
                <h2 class="section-title">Select a Student</h2>
                <div class="controls">
                    <select id="studentSelect">
                        <option value="">Loading students...</option>
                    </select>
                    <button onclick="getRecommendations()">Get Recommendations</button>
                    <button onclick="showAnalytics()">Show Analytics</button>
                    <button onclick="regenerateData()">Generate New Data</button>
                </div>
            </div>
            
            <div id="studentInfo" class="section" style="display: none;">
                <h2 class="section-title">Student Profile</h2>
                <div class="student-info">
                    <div id="studentDetails"></div>
                </div>
            </div>
            
            <div id="recommendationsSection" class="section" style="display: none;">
                <h2 class="section-title">Personalized Recommendations</h2>
                <div id="recommendations" class="recommendations"></div>
            </div>
            
            <div id="analyticsSection" class="section" style="display: none;">
                <h2 class="section-title">System Analytics</h2>
                <div id="analytics" class="analytics"></div>
            </div>
        </div>
    </div>
    
    <script>
        let students = [];
        let currentStudent = null;
        
        async function loadStudents() {
            try {
                const response = await fetch('/api/students');
                students = await response.json();
                
                const select = document.getElementById('studentSelect');
                select.innerHTML = '<option value="">Choose a student...</option>';
                
                students.forEach(student => {
                    const option = document.createElement('option');
                    option.value = student.student_id;
                    option.textContent = `${student.student_id} - Grade ${student.grade_level} (${student.reading_level})`;
                    select.appendChild(option);
                });
            } catch (error) {
                console.error('Error loading students:', error);
            }
        }
        
        async function getRecommendations() {
            const studentId = document.getElementById('studentSelect').value;
            if (!studentId) {
                alert('Please select a student first');
                return;
            }
            
            // Hide analytics, show loading
            document.getElementById('analyticsSection').style.display = 'none';
            document.getElementById('recommendationsSection').style.display = 'block';
            document.getElementById('recommendations').innerHTML = '<div class="loading">Generating recommendations</div>';
            
            try {
                // Get student details
                const studentResponse = await fetch(`/api/students/${studentId}`);
                currentStudent = await studentResponse.json();
                displayStudentInfo(currentStudent);
                
                // Get recommendations
                const recResponse = await fetch(`/api/recommendations/${studentId}?n=10`);
                const recommendations = await recResponse.json();
                displayRecommendations(recommendations);
            } catch (error) {
                console.error('Error getting recommendations:', error);
                document.getElementById('recommendations').innerHTML = 
                    '<div class="error">Error loading recommendations. Please try again.</div>';
            }
        }
        
        function displayStudentInfo(student) {
            document.getElementById('studentInfo').style.display = 'block';
            
            const html = `
                <h3>Student ID: ${student.student_id}</h3>
                <div class="info-grid">
                    <div class="info-item">
                        <span class="info-label">Grade Level</span>
                        <span class="info-value">${student.grade_level}</span>
                    </div>
                    <div class="info-item">
                        <span class="info-label">Reading Level</span>
                        <span class="info-value">${student.reading_level}</span>
                    </div>
                    <div class="info-item">
                        <span class="info-label">Books Read</span>
                        <span class="info-value">${student.books_read_count}</span>
                    </div>
                    <div class="info-item">
                        <span class="info-label">Preferred Genres</span>
                        <span class="info-value">
                            ${student.preferred_genres.map(g => `<span class="tag">${g}</span>`).join('')}
                        </span>
                    </div>
                    <div class="info-item">
                        <span class="info-label">Interests</span>
                        <span class="info-value">
                            ${student.interests.map(i => `<span class="tag">${i}</span>`).join('')}
                        </span>
                    </div>
                </div>
            `;
            
            document.getElementById('studentDetails').innerHTML = html;
        }
        
        function displayRecommendations(recommendations) {
            const container = document.getElementById('recommendations');
            
            if (recommendations.length === 0) {
                container.innerHTML = '<p>No recommendations available.</p>';
                return;
            }
            
            const html = recommendations.map((rec, index) => {
                // Get student interests for highlighting matches
                const studentInterests = currentStudent ? currentStudent.interests.map(i => i.toLowerCase()) : [];
                
                // Highlight matching subjects/themes
                const subjectTags = rec.book.subject.map(subject => {
                    const isMatch = studentInterests.some(interest => 
                        subject.toLowerCase().includes(interest) || 
                        interest.includes(subject.toLowerCase())
                    );
                    const highlightClass = isMatch ? 'tag-highlight' : 'tag-subject';
                    return `<span class="${highlightClass}" title="${isMatch ? '✓ Matches your interests' : 'Theme'}">${subject}</span>`;
                }).join('');
                
                // Generate star rating display
                const rating = rec.book.average_rating;
                const ratingCount = rec.book.rating_count;
                let ratingDisplay = '';
                
                if (rating > 0 && ratingCount > 0) {
                    const fullStars = Math.floor(rating);
                    const hasHalfStar = rating % 1 >= 0.5;
                    const emptyStars = 5 - fullStars - (hasHalfStar ? 1 : 0);
                    
                    ratingDisplay = `
                        <div class="book-rating" style="margin: 8px 0; color: #ffa500;">
                            ${'⭐'.repeat(fullStars)}${hasHalfStar ? '⭐' : ''}${'☆'.repeat(emptyStars)}
                            <span style="color: #555; font-size: 0.9em; margin-left: 4px;">
                                ${rating.toFixed(1)} (${ratingCount} ${ratingCount === 1 ? 'rating' : 'ratings'})
                            </span>
                        </div>
                    `;
                }
                
                return `
                    <div class="recommendation-card">
                        <div class="book-title">${index + 1}. ${rec.book.title}</div>
                        <div class="book-author">by ${rec.book.author}</div>
                        <div class="book-details">
                            📖 ${rec.book.page_count} pages | 📚 ${rec.book.reading_level}
                        </div>
                        ${ratingDisplay}
                        <div class="book-genres">
                            ${rec.book.genre.map(g => `<span class="tag">${g}</span>`).join('')}
                        </div>
                        <div class="book-subjects">
                            <strong>Key Themes:</strong> ${subjectTags}
                        </div>
                        <div class="recommendation-reason">
                            💡 ${rec.reason}
                        </div>
                        <div class="score-bar">
                            <span class="score-label">Match: ${(rec.score * 100).toFixed(0)}%</span>
                            <div class="score-progress">
                                <div class="score-fill" style="width: ${rec.score * 100}%"></div>
                            </div>
                        </div>
                        <div>
                            <span class="strategy-badge">${rec.strategy}</span>
                            <span style="float: right; color: #888; font-size: 0.9em;">
                                Confidence: ${(rec.confidence * 100).toFixed(0)}%
                            </span>
                        </div>
                    </div>
                `;
            }).join('');
            
            container.innerHTML = html;
        }
        
        async function showAnalytics() {
            document.getElementById('studentInfo').style.display = 'none';
            document.getElementById('recommendationsSection').style.display = 'none';
            document.getElementById('analyticsSection').style.display = 'block';
            
            const analyticsDiv = document.getElementById('analytics');
            analyticsDiv.innerHTML = '<div class="loading">Loading analytics</div>';
            
            try {
                const response = await fetch('/api/analytics');
                const analytics = await response.json();
                
                const genreChart = Object.entries(analytics.genre_distribution)
                    .sort((a, b) => b[1] - a[1])
                    .slice(0, 5)
                    .map(([genre, count]) => `
                        <div style="margin: 5px 0;">
                            <span style="display: inline-block; width: 120px;">${genre}:</span>
                            <span style="font-weight: bold;">${count}</span>
                        </div>
                    `).join('');
                
                const html = `
                    <div class="stat-grid">
                        <div class="stat-card">
                            <div class="stat-value">${analytics.total_students}</div>
                            <div class="stat-label">Total Students</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-value">${analytics.total_books}</div>
                            <div class="stat-label">Books in Catalog</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-value">${analytics.total_borrowing_records}</div>
                            <div class="stat-label">Total Borrows</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-value">${analytics.average_books_per_student.toFixed(1)}</div>
                            <div class="stat-label">Avg Books/Student</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-value">${(analytics.catalog_coverage * 100).toFixed(0)}%</div>
                            <div class="stat-label">Catalog Coverage</div>
                        </div>
                    </div>
                    <div style="margin-top: 30px;">
                        <h3 style="margin-bottom: 15px; color: #667eea;">Top Genres</h3>
                        ${genreChart}
                    </div>
                `;
                
                analyticsDiv.innerHTML = html;
            } catch (error) {
                console.error('Error loading analytics:', error);
                analyticsDiv.innerHTML = '<div class="error">Error loading analytics.</div>';
            }
        }
        
        async function regenerateData() {
            if (!confirm('This will regenerate all sample data. Continue?')) {
                return;
            }
            
            const button = event.target;
            button.disabled = true;
            button.textContent = 'Regenerating...';
            
            try {
                await fetch('/api/regenerate-data', { method: 'POST' });
                alert('Data regenerated successfully!');
                await loadStudents();
                
                // Clear any displayed content
                document.getElementById('studentInfo').style.display = 'none';
                document.getElementById('recommendationsSection').style.display = 'none';
                document.getElementById('analyticsSection').style.display = 'none';
            } catch (error) {
                console.error('Error regenerating data:', error);
                alert('Error regenerating data');
            } finally {
                button.disabled = false;
                button.textContent = 'Generate New Data';
            }
        }
        
        // Load students on page load
        window.addEventListener('load', loadStudents);
    </script>
</body>
</html>
"""

if __name__ == "__main__":
    # Run the FastAPI application
    print("\n" + "="*60)
    print("🚀 Starting SmartReads Recommendation System")
    print("="*60)
    print("\n📌 Access the application at: http://localhost:8000")
    print("📌 API documentation at: http://localhost:8000/docs")
    print("\nPress Ctrl+C to stop the server\n")
    
    uvicorn.run(app, host="0.0.0.0", port=8000)
