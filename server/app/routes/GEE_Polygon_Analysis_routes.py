import os
import re
import json

from flask import Blueprint, jsonify, request
from flask_cors import CORS
from dotenv import load_dotenv
import ee

from app import db
from app.models import DevelopmentPlan, PolygonAnalysis, Polygon, User

# Load environment variables from .env
load_dotenv()

# Define the blueprint
gee_bp = Blueprint("gee", __name__)
CORS(gee_bp)  # Enable CORS for this blueprint

ee_initialized = False


def init_ee():
    """Initialize Google Earth Engine with service account from environment."""
    global ee_initialized
    if ee_initialized:
        return True

    try:
        # Get service account email and JSON key string
        service_account = os.environ.get("GEE_SERVICE_ACCOUNT")
        key_json_str = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS_JSON")

        if not service_account or not key_json_str:
            raise ValueError(
                "GEE_SERVICE_ACCOUNT or GOOGLE_APPLICATION_CREDENTIALS_JSON not set")

        # Parse the JSON string
        sa_info = json.loads(key_json_str)

        # Initialize EE using ServiceAccountCredentials
        credentials = ee.ServiceAccountCredentials(
            service_account=service_account,
            key_file=None,
            private_key=sa_info["private_key"]
        )

        ee.Initialize(credentials, project=sa_info["project_id"])
        ee_initialized = True
        print("Earth Engine initialized successfully!")
        return True

    except Exception as e:
        import traceback
        print("Failed to initialize Earth Engine:", e)
        traceback.print_exc()
        return False


def wkt_to_coords(wkt_str):
    """Convert WKT POLYGON string to coordinates list."""
    if not wkt_str.startswith("POLYGON(("):
        raise ValueError("Invalid WKT format")

    coords_str = re.search(r"\(\((.*)\)\)", wkt_str).group(1)
    coords = [[float(x) for x in pair.strip().split()]
              for pair in coords_str.split(",")]
    return [coords]


@gee_bp.route("/development_plans/<int:plan_id>/analyze", methods=["GET"])
def get_analysis(plan_id):
    """Retrieve stored analysis results for a plan."""
    try:
        analysis = PolygonAnalysis.query.filter_by(
            development_plan_id=plan_id).first()
        if not analysis:
            return jsonify({"error": "No analysis found for this plan"}), 404
        return jsonify(analysis.to_dict()), 200
    except Exception as e:
        print("Error fetching analysis:", e)
        return jsonify({"error": str(e)}), 500


@gee_bp.route("/development_plans/<int:plan_id>/analyze", methods=["POST"])
def analyze_plan(plan_id):
    """Run GEE analysis for a development plan."""
    data = request.get_json()
    user_id = data.get("user_id")

    if not user_id:
        return jsonify({"error": "user_id is required"}), 400

    plan = DevelopmentPlan.query.get(plan_id)
    if not plan:
        return jsonify({"error": "Plan not found"}), 404

    try:
        polygon = plan.polygon
        coords_list = wkt_to_coords(polygon.coordinates)
        geom = ee.Geometry.Polygon(coords_list)

        # Example: analyze ESA WorldCover
        image = ee.ImageCollection("ESA/WorldCover/v100").first().select("Map")
        clipped = image.clip(geom)
        stats = clipped.reduceRegion(
            reducer=ee.Reducer.frequencyHistogram(),
            geometry=geom,
            scale=50,
            maxPixels=1e13,
        )

        hist = ee.Dictionary(stats.get("Map")).getInfo()
        total_pixels = sum(hist.values())
        built_up_pct = round(hist.get("50", 0) / total_pixels * 100, 2)
        flora_pct = round(hist.get("10", 0) / total_pixels * 100, 2)

        plan_area = plan.area_size
        built_up_area = plan_area * (built_up_pct / 100)
        flora_area = plan_area * (flora_pct / 100)

        polygon_area_ee = geom.area().divide(1e6).getInfo()
        total_flora_in_polygon = polygon_area_ee * (flora_pct / 100)
        flora_loss_pct = (flora_area / total_flora_in_polygon *
                          100) if total_flora_in_polygon > 0 else 0
        new_built_up_area = polygon_area_ee * (built_up_pct / 100) + plan_area
        new_built_up_pct = new_built_up_area / polygon_area_ee * 100

        # Determine status
        if flora_loss_pct <= 10 and new_built_up_pct <= 60:
            status = "Pass"
        elif flora_loss_pct <= 20 and new_built_up_pct <= 70:
            status = "Pass"
        else:
            status = "Fail"

        # Save analysis
        analysis = PolygonAnalysis(
            development_plan_id=plan.id,
            polygon_id=plan.polygon_id,
            built_up_area=built_up_area,
            flora_area=flora_area,
            built_up_pct=built_up_pct,
            flora_pct=flora_pct,
            flora_loss_pct=flora_loss_pct,
            new_built_up_pct=new_built_up_pct,
            status=status,
            user_id=user_id,
        )

        plan.status = status
        db.session.add(analysis)
        db.session.commit()

        result = analysis.to_dict()
        result.update({
            "status": status,
            "polygon_area": round(polygon_area_ee, 4),
            "plan_area": plan_area,
            "flora_loss_area": round(flora_area, 4),
            "flora_loss_pct": round(flora_loss_pct, 2),
            "new_built_up_pct": round(new_built_up_pct, 2),
            "recommendation": get_recommendation(plan.type, flora_pct, flora_loss_pct, new_built_up_pct),
        })

        return jsonify(result), 200

    except Exception as e:
        db.session.rollback()
        print("Error running GEE analysis:", e)
        return jsonify({"error": str(e)}), 500


def get_recommendation(plan_type, current_flora_pct, flora_loss_pct, new_built_up_pct):
    """Generate a recommendation based on impact metrics."""
    if flora_loss_pct > 20:
        return (
            f"High impact: This {plan_type} development will destroy {flora_loss_pct:.1f}% of the polygon's flora. "
            "It is recommended to reconsider the plan or reduce the development footprint."
        )
    elif flora_loss_pct > 10:
        return (
            f"Moderate impact: This {plan_type} development will destroy {flora_loss_pct:.1f}% of the polygon's flora. "
            "Consider mitigation measures."
        )
    else:
        return (
            f"Low impact: This {plan_type} development has minimal impact on the polygon's flora. "
            "Plan can proceed."
        )
