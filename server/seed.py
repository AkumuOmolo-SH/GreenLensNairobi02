from app import create_app, db
from app.models import Area, Polygon, DevelopmentPlan, User, Report
from datetime import datetime, timedelta
import random

app = create_app()

with app.app_context():
    # Clear tables in safe order
    Report.query.delete()
    User.query.delete()
    DevelopmentPlan.query.delete()
    Polygon.query.delete()
    Area.query.delete()
    db.session.commit()

    # --- Seed Areas FIRST (no polygon_id needed initially) ---
    area1 = Area(name="Lang'ata")
    area2 = Area(name="Karen")
    area3 = Area(name="Lavington-Kilimani Zone")
    area4 = Area(name="DandoraNjiru Zone")
    db.session.add_all([area1, area2, area3, area4])
    db.session.commit()

    # --- Seed Polygons (referencing areas) ---
    polygon1 = Polygon(
        name="Langata Zone 01 Polygon",
        coordinates="POLYGON((36.785 -1.334, 36.795 -1.334, 36.795 -1.324, 36.785 -1.324, 36.785 -1.334))",
        area=area1.id  # This links to the Area
    )
    polygon2 = Polygon(
        name="Karen Polygon",
        coordinates="POLYGON((36.710 -1.315, 36.725 -1.315, 36.725 -1.300, 36.710 -1.300, 36.710 -1.315))",
        area=area2.id
    )
    polygon3 = Polygon(
        name="Lavington-Kilimani Zone",
        coordinates="POLYGON((36.7600 -1.3150, 36.7900 -1.3150, 36.7900 -1.2950, 36.7750 -1.2850, 36.7550 -1.2900, 36.7600 -1.3150))",
        area=area3.id
    )
    polygon4 = Polygon(
        name="DandoraNjiru Zone",
        coordinates="POLYGON((36.8850 -1.2700, 36.9050 -1.2700, 36.9100 -1.2500, 36.8950 -1.2350, 36.8750 -1.2450, 36.8850 -1.2700))",
        area=area4.id
    )
    db.session.add_all([polygon1, polygon2, polygon3, polygon4])
    db.session.commit()

    # Update Areas with polygon_id
    area1.polygon_id = polygon1.id
    area2.polygon_id = polygon2.id
    area3.polygon_id = polygon3.id
    area4.polygon_id = polygon4.id
    db.session.commit()

    # --- Seed Development Plan ---
    plan1 = DevelopmentPlan(
        title="Road Expansion",
        description="Expand the main road",
        type="Infrastructure",
        area_size=2.5,
        status="Pending",
        area_id=area1.id,
        polygon_id=polygon1.id,
        ai_results="{}"
    )
    db.session.add(plan1)
    db.session.commit()

    print("Database seeded successfully!")

    # Seed Users & Reports
    users = [
        User(username="maria_santos", email="maria@gmail.com",
             password_hash="hashed_password_1"),
        User(username="john_kamau", email="john@yahoo.com",
             password_hash="hashed_password_2"),
        User(username="aisha_mohammed", email="aisha@gmail.com",
             password_hash="hashed_password_3"),
        User(username="david_ochieng", email="david@yahoo.com",
             password_hash="hashed_password_4"),
        User(username="grace_wanjiru", email="grace@gmail.com",
             password_hash="hashed_password_5"),
        User(username="peter_mwangi", email="peter@yahoo.com",
             password_hash="hashed_password_6"),
        User(username="faith_akinyi", email="faith@gmail.com",
             password_hash="hashed_password_7"),
        User(username="james_otieno", email="james@yahoo.com",
             password_hash="hashed_password_8"),
    ]

    db.session.add_all(users)
    db.session.commit()

    reports_data = [
        {"title": "Illegal Dumping Site", "description": "Large amounts of waste illegally dumped near the river.",
            "location": "Kibera, Nairobi", "image_url": "https://images.unsplash.com/photo-1611284446314-60a58ac0deb9?w=800"},
        {"title": "Polluted River", "description": "Industrial waste flowing directly into the river.",
            "location": "Mombasa Coast", "image_url": "https://images.unsplash.com/photo-1621451537084-482c73073a0f?w=800"},
        {"title": "Deforestation", "description": "Trees being cut down at an alarming rate.",
            "location": "Kakamega Forest", "image_url": "https://images.unsplash.com/photo-1559827260-dc66d52bef19?w=800"},
        {"title": "Air Pollution", "description": "Heavy smoke and emissions.", "location": "Industrial Area, Nairobi",
            "image_url": "https://images.unsplash.com/photo-1611273426858-450d8e3c9fce?w=800"},
    ]

    base_time = datetime.now()
    for data in reports_data:
        user = random.choice(users)
        created_at = base_time - timedelta(days=random.randint(0, 30))
        report = Report(
            title=data["title"],
            description=data["description"],
            location=data["location"],
            image_url=data["image_url"],
            user_id=user.id,
            created_at=created_at
        )
        db.session.add(report)

    db.session.commit()
    print("✅ Database seeding completed successfully!")
