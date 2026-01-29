#!/usr/bin/env python3
import random
from datetime import datetime


def main():
    print("Generating medium database (social media) data...")

    # Generate 500 users
    with open("02_data.sql", "w") as f:
        f.write("-- Medium DB Data\n")
        f.write(
            "INSERT INTO users (username, email, password_hash, display_name, created_at, is_verified) VALUES\n"
        )
        users = []
        for i in range(500):
            username = f"user{i:04d}"
            email = f"{username}@example.com"
            display = f"User {i}"
            created = datetime(2024, random.randint(1, 12), random.randint(1, 28))
            verified = i < 100  # First 100 verified
            users.append(f"('{username}', '{email}', 'hash', '{display}', '{created}', {verified})")
        f.write(",\n".join(users) + ";\n\n")

        # Generate 2000 posts
        f.write("INSERT INTO posts (user_id, content, content_type, created_at) VALUES\n")
        posts = []
        for i in range(2000):
            user = random.randint(1, 500)
            content = f"Post content {i}"
            ctype = random.choice(["text", "image", "video"])
            created = datetime(2025, random.randint(1, 12), random.randint(1, 28))
            posts.append(f"({user}, '{content}', '{ctype}', '{created}')")
        f.write(",\n".join(posts) + ";\n")

    print("✓ Medium database data generated")


if __name__ == "__main__":
    main()
