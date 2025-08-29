"""
Plant species and disease models
"""

from app.models.database import db


class PlantSpecies(db.Model):
    __tablename__ = "plant_species"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)


class Disease(db.Model):
    __tablename__ = "diseases"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    treatment = db.Column(db.Text)
    plant_id = db.Column(db.Integer, db.ForeignKey("plant_species.id"), nullable=False)

    plant = db.relationship("PlantSpecies", backref="diseases")
