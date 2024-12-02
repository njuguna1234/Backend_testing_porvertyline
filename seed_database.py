from app import app, db
from models import User, Post, Comment, Appointment
from datetime import datetime, timedelta
import random

def seed_database():
    with app.app_context():
        # Clear existing data
        db.drop_all()
        db.create_all()

        # Create users (including therapists)
        users = [
            User(username="john_doe", email="john@example.com", is_therapist=False),
            User(username="jane_smith", email="jane@example.com", is_therapist=False),
            User(username="dr_thompson", email="thompson@therapy.com", is_therapist=True),
            User(username="dr_wilson", email="wilson@therapy.com", is_therapist=True),
        ]

        for user in users:
            user.set_password("password123")
            db.session.add(user)

        db.session.commit()

        # Create posts
        posts = [
            Post(therapist_id=3, title="Coping with Anxiety", content="Anxiety is a common issue that many people face...", media_type="text"),
            Post(therapist_id=3, title="The Importance of Sleep", content="Getting enough quality sleep is crucial for mental health...", media_type="text"),
            Post(therapist_id=4, title="Mindfulness Techniques", content="Mindfulness can be a powerful tool for managing stress...", media_type="text"),
            Post(therapist_id=4, title="Building Healthy Relationships", content="Healthy relationships are fundamental to our well-being...", media_type="text"),
        ]

        for post in posts:
            db.session.add(post)

        db.session.commit()

        # Create comments
        comments = [
            Comment(user_id=1, post_id=1, content="This article really helped me understand my anxiety better."),
            Comment(user_id=2, post_id=1, content="I've been using these techniques and they work great!"),
            Comment(user_id=1, post_id=2, content="I never realized how important sleep was. Thanks for the info!"),
            Comment(user_id=2, post_id=3, content="Mindfulness has changed my life. Great article!"),
        ]

        for comment in comments:
            db.session.add(comment)

        db.session.commit()

        # Create appointments
        start_date = datetime.now() + timedelta(days=1)
        for _ in range(10):
            appointment = Appointment(
                user_id=random.choice([1, 2]),
                therapist_id=random.choice([3, 4]),
                date=start_date + timedelta(days=random.randint(0, 30), hours=random.randint(9, 17)),
                duration=60,
                status=random.choice(['pending', 'confirmed', 'cancelled']),
                notes="Initial consultation"
            )
            db.session.add(appointment)
            
        db.session.commit()

        print("Database seeded successfully!")

if __name__ == "__main__":
    seed_database()

