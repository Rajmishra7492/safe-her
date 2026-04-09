import os
import uuid
from datetime import datetime

from bson import ObjectId
from flask import Blueprint, current_app, jsonify, request

from utils.auth import token_required
from utils.risk_detection import analyze_audio, analyze_risk, combine_multimodal_risk

main_bp = Blueprint("main", __name__)


def _safe_object_id(raw_id):
    try:
        return ObjectId(raw_id)
    except Exception:
        return None


def _save_upload(file_obj, prefix):
    if not file_obj:
        return None, None
    ext = os.path.splitext(file_obj.filename or "")[1].lower() or ".bin"
    name = f"{prefix}_{uuid.uuid4().hex}{ext}"
    upload_dir = current_app.config["UPLOAD_DIR"]
    os.makedirs(upload_dir, exist_ok=True)
    abs_path = os.path.join(upload_dir, name)
    file_obj.save(abs_path)
    web_path = f"/static/uploads/{name}"
    return abs_path, web_path


@main_bp.route("/dashboard", methods=["GET"])
@token_required()
def dashboard():
    db = current_app.config["db"]
    user = db.users.find_one({"_id": ObjectId(request.user_id)}, {"password": 0})
    if not user:
        return jsonify({"error": "User not found"}), 404

    role = user.get("role", "admin" if user.get("is_admin", False) else "user")
    return jsonify({
        "message": "Dashboard data fetched",
        "user": {
            "id": str(user["_id"]),
            "name": user.get("name"),
            "email": user.get("email"),
            "is_admin": user.get("is_admin", False),
            "role": role,
        },
        "counts": {
            "contacts": db.contacts.count_documents({"user_id": request.user_id}),
            "alerts": db.alerts.count_documents({"user_id": request.user_id}),
            "incidents": db.incidents.count_documents({"user_id": request.user_id}),
        },
    })


@main_bp.route("/sos", methods=["POST"])
@token_required()
def sos():
    db = current_app.config["db"]

    if request.files or (request.content_type and "multipart/form-data" in request.content_type):
        lat = request.form.get("latitude")
        lng = request.form.get("longitude")
        image_file = request.files.get("image")
        audio_file = request.files.get("audio")
    else:
        data = request.get_json(silent=True) or {}
        lat = data.get("latitude")
        lng = data.get("longitude")
        image_file = None
        audio_file = None

    if lat is None or lng is None:
        return jsonify({"error": "Latitude and longitude are required"}), 400

    image_abs, image_web = _save_upload(image_file, "panic_img")
    audio_abs, audio_web = _save_upload(audio_file, "panic_audio")

    image_analysis = analyze_risk(image_abs) if image_abs else {
        "risk_score": 0,
        "faces_detected": 0,
        "avg_brightness": 255,
        "is_night": False,
        "triggered": False,
        "notes": "No image uploaded",
    }
    audio_analysis = analyze_audio(audio_abs)
    risk = combine_multimodal_risk(image_analysis, audio_analysis)

    result = db.alerts.insert_one({
        "user_id": request.user_id,
        "type": "SOS",
        "latitude": lat,
        "longitude": lng,
        "message": "Emergency SOS triggered",
        "image_path": image_web,
        "audio_path": audio_web,
        "image_analysis": image_analysis,
        "audio_analysis": audio_analysis,
        "risk_score": risk.get("risk_score", 0),
        "risk_level": risk.get("risk_level", "Low"),
        "created_at": datetime.utcnow(),
    })

    notified = db.contacts.count_documents({"user_id": request.user_id})
    return jsonify({
        "message": "SOS alert sent successfully",
        "alert_id": str(result.inserted_id),
        "notified_contacts": notified,
        "risk": risk,
        "uploads": {"image": image_web, "audio": audio_web},
    })


@main_bp.route("/analyze", methods=["POST"])
@token_required()
def analyze_preview():
    image_file = request.files.get("image")
    audio_file = request.files.get("audio")
    image_abs, image_web = _save_upload(image_file, "analyze_img")
    audio_abs, audio_web = _save_upload(audio_file, "analyze_audio")

    image_analysis = analyze_risk(image_abs) if image_abs else {
        "risk_score": 0,
        "faces_detected": 0,
        "avg_brightness": 255,
        "is_night": False,
        "triggered": False,
        "notes": "No image uploaded",
    }
    audio_analysis = analyze_audio(audio_abs)
    combined = combine_multimodal_risk(image_analysis, audio_analysis)

    return jsonify({
        "image_analysis": image_analysis,
        "audio_analysis": audio_analysis,
        "combined_risk": combined,
        "uploads": {"image": image_web, "audio": audio_web},
    })


@main_bp.route("/contacts", methods=["GET", "POST"])
@token_required()
def contacts():
    db = current_app.config["db"]
    if request.method == "GET":
        rows = list(db.contacts.find({"user_id": request.user_id}).sort("created_at", -1))
        return jsonify({"contacts": [{
            "id": str(row["_id"]),
            "name": row.get("name"),
            "phone": row.get("phone"),
            "relation": row.get("relation", ""),
            "created_at": row.get("created_at").isoformat() if row.get("created_at") else None,
        } for row in rows]})

    body = request.get_json(silent=True) or {}
    name = body.get("name", "").strip()
    phone = body.get("phone", "").strip()
    relation = body.get("relation", "").strip()
    if not name or not phone:
        return jsonify({"error": "Name and phone are required"}), 400

    result = db.contacts.insert_one({
        "user_id": request.user_id,
        "name": name,
        "phone": phone,
        "relation": relation,
        "created_at": datetime.utcnow(),
    })
    return jsonify({"message": "Contact added", "contact_id": str(result.inserted_id)}), 201


@main_bp.route("/contacts/<contact_id>", methods=["DELETE"])
@token_required()
def delete_contact(contact_id):
    db = current_app.config["db"]
    obj_id = _safe_object_id(contact_id)
    if not obj_id:
        return jsonify({"error": "Invalid contact id"}), 400

    deleted = db.contacts.delete_one({"_id": obj_id, "user_id": request.user_id})
    if deleted.deleted_count == 0:
        return jsonify({"error": "Contact not found"}), 404
    return jsonify({"message": "Contact deleted"})


@main_bp.route("/report", methods=["POST"])
@token_required()
def report_incident():
    description = request.form.get("description", "").strip()
    location = request.form.get("location", "").strip()
    latitude, longitude = request.form.get("latitude"), request.form.get("longitude")
    image = request.files.get("image")

    if not description or not location:
        return jsonify({"error": "Description and location are required"}), 400

    image_abs, image_web = _save_upload(image, "incident")
    risk = {
        "risk_score": 0,
        "faces_detected": 0,
        "avg_brightness": 0,
        "is_night": False,
        "triggered": False,
        "notes": "No image uploaded",
    }
    if image_abs:
        risk = analyze_risk(image_abs)

    db = current_app.config["db"]
    result = db.incidents.insert_one({
        "user_id": request.user_id,
        "description": description,
        "location": location,
        "latitude": latitude,
        "longitude": longitude,
        "image_path": image_web,
        "risk_analysis": risk,
        "created_at": datetime.utcnow(),
    })

    if risk.get("triggered"):
        db.alerts.insert_one({
            "user_id": request.user_id,
            "type": "AI_RISK",
            "latitude": latitude,
            "longitude": longitude,
            "message": f"Auto-alert generated. Risk score: {risk.get('risk_score')}",
            "risk_score": risk.get("risk_score", 0),
            "risk_level": "High" if risk.get("risk_score", 0) >= 70 else "Medium",
            "created_at": datetime.utcnow(),
        })

    return jsonify({"message": "Incident reported", "incident_id": str(result.inserted_id), "risk_analysis": risk})


@main_bp.route("/alerts", methods=["GET"])
@token_required()
def alerts():
    db = current_app.config["db"]
    rows = list(db.alerts.find({"user_id": request.user_id}).sort("created_at", -1).limit(100))
    return jsonify({"alerts": [{
        "id": str(row["_id"]),
        "type": row.get("type"),
        "message": row.get("message"),
        "latitude": row.get("latitude"),
        "longitude": row.get("longitude"),
        "image_path": row.get("image_path"),
        "audio_path": row.get("audio_path"),
        "risk_score": row.get("risk_score", 0),
        "risk_level": row.get("risk_level", "Low"),
        "created_at": row.get("created_at").isoformat() if row.get("created_at") else None,
    } for row in rows]})


@main_bp.route("/admin", methods=["GET"])
@token_required()
def admin_panel_data():
    db = current_app.config["db"]
    user = db.users.find_one({"_id": ObjectId(request.user_id)})
    if not user or not user.get("is_admin", False):
        return jsonify({"error": "Admin access required"}), 403

    users = list(db.users.find({}, {"password": 0}).sort("created_at", -1).limit(100))
    alerts = list(db.alerts.find({}).sort("created_at", -1).limit(200))
    incidents = list(db.incidents.find({}).sort("created_at", -1).limit(200))
    return jsonify({
        "counts": {
            "users": db.users.count_documents({}),
            "alerts": db.alerts.count_documents({}),
            "incidents": db.incidents.count_documents({}),
        },
        "users": [{
            "id": str(u["_id"]),
            "name": u.get("name"),
            "email": u.get("email"),
            "role": u.get("role", "admin" if u.get("is_admin", False) else "user"),
            "is_admin": u.get("is_admin", False),
        } for u in users],
        "alerts": [{
            "id": str(a["_id"]),
            "user_id": a.get("user_id"),
            "type": a.get("type"),
            "message": a.get("message"),
            "risk_score": a.get("risk_score", 0),
            "risk_level": a.get("risk_level", "Low"),
            "image_path": a.get("image_path"),
            "audio_path": a.get("audio_path"),
        } for a in alerts],
        "incidents": [{
            "id": str(i["_id"]),
            "user_id": i.get("user_id"),
            "description": i.get("description"),
            "location": i.get("location"),
            "risk_score": i.get("risk_analysis", {}).get("risk_score", 0),
        } for i in incidents],
    })


# Compatibility aliases
@main_bp.route("/add-contact", methods=["POST"])
@token_required()
def add_contact_compat():
    return contacts()


@main_bp.route("/report-incident", methods=["POST"])
@token_required()
def report_compat():
    return report_incident()


@main_bp.route("/get-alerts", methods=["GET"])
@token_required()
def alerts_compat():
    return alerts()


@main_bp.route("/admin/analytics", methods=["GET"])
@token_required()
def admin_compat():
    return admin_panel_data()
