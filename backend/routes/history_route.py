from flask import Blueprint, jsonify
from services.history_service import get_recent_history

history_bp = Blueprint("history_bp",__name__)

@history_bp.route("/history",methods=["GET"])
def history():
  
  return jsonify(get_recent_history())
