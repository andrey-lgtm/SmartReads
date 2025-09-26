"""
Data Generator for SmartReads Demo
Generates realistic sample data for the recommendation system
"""

import random
import json
from datetime import datetime, timedelta
from typing import List, Tuple
import hashlib
from recommendation_engine import Book, Student, BorrowingRecord

# Sample data pools
FIRST_NAMES = [
    "Emma", "Liam", "Olivia", "Noah", "Ava", "Elijah", "Sophia", "Lucas",
    "Isabella", "Oliver", "Mia", "Ethan", "Charlotte", "James", "Amelia",
    "Benjamin", "Harper", "Mason", "Evelyn", "Logan", "Abigail", "Alexander",
    "Emily", "Sebastian", "Madison", "Jack", "Chloe", "Daniel", "Grace", "Henry"
]

LAST_NAMES = [
    "Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis",
    "Rodriguez", "Martinez", "Hernandez", "Lopez", "Gonzalez", "Wilson", "Anderson"
]

BOOK_TITLES_TEMPLATES = [
    "The {adjective} {noun}",
    "{noun} of {place}",
    "Journey to {place}",
    "The Last {noun}",
    "{adjective} {noun} Adventures",
    "Mystery of the {adjective} {noun}",
    "The {noun}'s Secret",
    "Tales of {place}",
    "The {adjective} Quest",
    "{noun} and the {adjective} {noun}"
]

ADJECTIVES = [
    "Mysterious", "Ancient", "Golden", "Silver", "Lost", "Hidden", "Magical",
    "Enchanted", "Forgotten", "Secret", "Crystal", "Emerald", "Sapphire",
    "Brave", "Clever", "Curious", "Amazing", "Wonderful", "Fantastic"
]

NOUNS = [
    "Dragon", "Knight", "Princess", "Wizard", "Forest", "Castle", "Mountain",
    "Ocean", "Island", "Kingdom", "Adventure", "Journey", "Quest", "Mystery",
    "Treasure", "Phoenix", "Guardian", "Explorer", "Inventor", "Detective"
]

PLACES = [
    "Avalon", "Atlantis", "Eldoria", "Mystwood", "Silverstone", "Goldshire",
    "Dragonfall", "Starhaven", "Moonhallow", "Sunridge", "Windmere", "Shadowvale"
]

GENRES = [
    "Fantasy", "Science Fiction", "Mystery", "Adventure", "Historical Fiction",
    "Contemporary", "Horror", "Romance", "Thriller", "Biography", "Poetry",
    "Graphic Novel", "Humor", "Sports", "Nature", "Technology"
]

SUBJECTS = [
    "Friendship", "Courage", "Family", "Growing Up", "Problem Solving",
    "Teamwork", "Perseverance", "Creativity", "Leadership", "Empathy",
    "Environment", "History", "Science", "Mathematics", "Arts", "Music",
    "Animals", "Space", "Time Travel", "Magic", "Robots", "Dinosaurs"
]

INTERESTS = [
    "Sports", "Music", "Art", "Science", "Technology", "Nature", "Animals",
    "Space", "History", "Cooking", "Gaming", "Photography", "Dancing",
    "Writing", "Reading", "Traveling", "Movies", "Comics", "Puzzles", "Chess"
]

def generate_isbn() -> str:
    """Generate a realistic ISBN-13"""
    prefix = "978"
    group = str(random.randint(0, 9))
    publisher = str(random.randint(10000, 99999))
    title = str(random.randint(100, 999))
    check = str(random.randint(0, 9))
    return f"{prefix}-{group}-{publisher}-{title}-{check}"

def generate_book_id(title: str, author: str) -> str:
    """Generate unique book ID"""
    hash_input = f"{title}{author}".encode()
    return hashlib.md5(hash_input).hexdigest()[:8].upper()

def generate_student_id(name: str, grade: int) -> str:
    """Generate unique student ID"""
    hash_input = f"{name}{grade}{random.randint(1000, 9999)}".encode()
    return f"S{hashlib.md5(hash_input).hexdigest()[:6].upper()}"

def generate_books(n: int = 100) -> List[Book]:
    """Generate sample books"""
    books = []
    used_titles = set()
    
    for _ in range(n):
        # Generate unique title
        attempts = 0
        while attempts < 10:
            template = random.choice(BOOK_TITLES_TEMPLATES)
            title = template.format(
                adjective=random.choice(ADJECTIVES),
                noun=random.choice(NOUNS),
                place=random.choice(PLACES)
            )
            if title not in used_titles:
                used_titles.add(title)
                break
            attempts += 1
        
        # Generate author name
        author = f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}"
        
        # Select genres and subjects
        num_genres = random.randint(1, 3)
        genres = random.sample(GENRES, num_genres)
        num_subjects = random.randint(2, 4)
        subjects = random.sample(SUBJECTS, num_subjects)
        
        # Determine reading level
        reading_levels = ["K-2", "3-5", "6-8", "9-12"]
        reading_level = random.choice(reading_levels)
        
        # Generate description
        description = f"An engaging {genres[0].lower()} story about {subjects[0].lower()}. "
        description += f"This book explores themes of {', '.join(subjects[1:]).lower()} "
        description += f"through {random.choice(['exciting', 'thoughtful', 'imaginative', 'compelling'])} storytelling."
        
        # Calculate page count based on reading level
        page_ranges = {
            "K-2": (20, 80),
            "3-5": (80, 200),
            "6-8": (150, 350),
            "9-12": (200, 500)
        }
        min_pages, max_pages = page_ranges[reading_level]
        page_count = random.randint(min_pages, max_pages)
        
        book = Book(
            book_id=generate_book_id(title, author),
            title=title,
            author=author,
            isbn=generate_isbn(),
            genre=genres,
            subject=subjects,
            reading_level=reading_level,
            description=description,
            publication_year=random.randint(2010, 2024),
            page_count=page_count,
            available_copies=random.randint(1, 5),
            total_copies=random.randint(2, 8)
        )
        books.append(book)
    
    return books

def generate_students(n: int = 50) -> List[Student]:
    """Generate sample students"""
    students = []
    
    for _ in range(n):
        # Generate student name
        first_name = random.choice(FIRST_NAMES)
        last_name = random.choice(LAST_NAMES)
        full_name = f"{first_name} {last_name}"
        
        # Generate grade level (K-12)
        grade_level = random.randint(0, 12)
        
        # Determine reading level based on grade
        if grade_level <= 2:
            reading_level = "K-2"
        elif grade_level <= 5:
            reading_level = "3-5"
        elif grade_level <= 8:
            reading_level = "6-8"
        else:
            reading_level = "9-12"
        
        # Generate preferences
        num_genres = random.randint(1, 4)
        preferred_genres = random.sample(GENRES, num_genres)
        
        num_interests = random.randint(2, 5)
        interests = random.sample(INTERESTS, num_interests)
        
        student = Student(
            student_id=generate_student_id(full_name, grade_level),
            grade_level=grade_level,
            reading_level=reading_level,
            preferred_genres=preferred_genres,
            interests=interests,
            reading_history=[]
        )
        students.append(student)
    
    return students

def generate_borrowing_history(
    students: List[Student], 
    books: List[Book], 
    n_records: int = 500
) -> List[BorrowingRecord]:
    """Generate borrowing history records"""
    records = []
    start_date = datetime.now() - timedelta(days=365)
    
    # Ensure each student has some history
    for student in students:
        # Number of books this student has borrowed
        num_borrows = random.randint(2, 15)
        
        for _ in range(num_borrows):
            # Select a book (prefer books matching student's reading level)
            suitable_books = [b for b in books if b.reading_level == student.reading_level]
            if not suitable_books:
                suitable_books = books
            
            # 70% chance to pick from suitable books, 30% to explore
            if random.random() < 0.7:
                book = random.choice(suitable_books)
            else:
                book = random.choice(books)
            
            # Generate borrowing date
            borrow_date = start_date + timedelta(days=random.randint(0, 365))
            
            # 80% of books are returned
            return_date = None
            completed = False
            rating = None
            
            if random.random() < 0.8:
                return_date = borrow_date + timedelta(days=random.randint(7, 30))
                completed = random.random() < 0.7  # 70% completion rate
                if completed:
                    # Rate completed books
                    rating = random.choices([3, 4, 5], weights=[0.2, 0.4, 0.4])[0]
            
            record = BorrowingRecord(
                student_id=student.student_id,
                book_id=book.book_id,
                borrow_date=borrow_date,
                return_date=return_date,
                rating=rating,
                completed=completed
            )
            records.append(record)
            
            # Add to student's reading history
            if book.book_id not in student.reading_history:
                student.reading_history.append(book.book_id)
    
    # Add more random records to reach target number
    while len(records) < n_records:
        student = random.choice(students)
        book = random.choice(books)
        
        borrow_date = start_date + timedelta(days=random.randint(0, 365))
        return_date = None
        completed = False
        rating = None
        
        if random.random() < 0.8:
            return_date = borrow_date + timedelta(days=random.randint(7, 30))
            completed = random.random() < 0.7
            if completed:
                rating = random.choices([3, 4, 5], weights=[0.2, 0.4, 0.4])[0]
        
        record = BorrowingRecord(
            student_id=student.student_id,
            book_id=book.book_id,
            borrow_date=borrow_date,
            return_date=return_date,
            rating=rating,
            completed=completed
        )
        records.append(record)
        
        if book.book_id not in student.reading_history:
            student.reading_history.append(book.book_id)
    
    return records

def generate_sample_data() -> Tuple[List[Book], List[Student], List[BorrowingRecord]]:
    """Generate complete sample dataset"""
    books = generate_books(150)
    students = generate_students(75)
    records = generate_borrowing_history(students, books, 1000)
    return books, students, records

def save_sample_data():
    """Generate and save sample data to JSON files"""
    books, students, records = generate_sample_data()
    
    # Convert to JSON-serializable format
    books_data = [book.to_dict() for book in books]
    students_data = [student.to_dict() for student in students]
    records_data = [
        {
            'student_id': r.student_id,
            'book_id': r.book_id,
            'borrow_date': r.borrow_date.isoformat(),
            'return_date': r.return_date.isoformat() if r.return_date else None,
            'rating': r.rating,
            'completed': r.completed
        }
        for r in records
    ]
    
    # Save to files
    with open('data/books.json', 'w') as f:
        json.dump(books_data, f, indent=2)
    
    with open('data/students.json', 'w') as f:
        json.dump(students_data, f, indent=2)
    
    with open('data/borrowing_history.json', 'w') as f:
        json.dump(records_data, f, indent=2)
    
    print(f"Generated and saved:")
    print(f"  - {len(books)} books to data/books.json")
    print(f"  - {len(students)} students to data/students.json")
    print(f"  - {len(records)} borrowing records to data/borrowing_history.json")
    
    # Generate some statistics
    print("\nDataset Statistics:")
    print(f"  - Average books per student: {len(records) / len(students):.1f}")
    print(f"  - Unique books borrowed: {len(set(r.book_id for r in records))}")
    print(f"  - Completion rate: {sum(1 for r in records if r.completed) / len(records):.1%}")
    print(f"  - Books with ratings: {sum(1 for r in records if r.rating) / len(records):.1%}")

if __name__ == "__main__":
    import os
    
    # Create data directory if it doesn't exist
    os.makedirs('data', exist_ok=True)
    
    # Generate and save sample data
    save_sample_data()
