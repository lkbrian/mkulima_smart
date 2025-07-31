import os
from datetime import datetime
import africastalking
from flask import request, jsonify
from flask_restful import Resource

# Initialize Africa's Talking
username = os.environ.get("AFRICASTALKING_USERNAME", "sandbox")
api_key = os.environ.get("AFRICASTALKING_API_KEY")

africastalking.initialize(username, api_key)

sms = africastalking.SMS


class SMSCallback(Resource):
    def post(self, request):
        data = request.get_json()
        phone_number = data.get("phoneNumber")

        # the Phone number should start with country code + 254712345678 -> format
        if not phone_number:
            return jsonify({"message": "Phone number not found"}), 400

        try:
            response = sms.send(
                message="Hello from AfricasTalking!",
                recipients=[phone_number],
                sender_id="AFTKNG",  # your Alphanumeric sender ID
            )

            return jsonify({"status": "success", "data": response}), 200
        except Exception as e:
            return (
                jsonify(
                    {"message": "An error occurred while sending SMS", "error": str(e)}
                ),
                500,
            )


class HealthCheckResource(Resource):
    """Health check endpoint"""

    def get(self):
        return {
            "status": "healthy",
            "service": "Mkulima Smart SMS API",
            "version": "1.0.0",
            "timestamp": datetime.utcnow().isoformat(),
        }, 200


class FarmingTipsResource(Resource):
    """Get farming tips by category"""

    def get(self):
        try:
            category = request.args.get("category", "general")

            # Predefined farming tips by category
            tips = {
                "crops": [
                    "Plant maize during long rains (March-May) for best yields",
                    "Use certified seeds for better disease resistance",
                    "Apply organic manure 2 weeks before planting",
                    "Practice crop rotation to maintain soil fertility",
                ],
                "livestock": [
                    "Provide clean water daily for healthy animals",
                    "Vaccinate cattle against common diseases",
                    "Build proper shelter to protect from weather",
                    "Feed animals balanced diet with minerals",
                ],
                "weather": [
                    "Check weather forecast before planting",
                    "Harvest crops before heavy rains",
                    "Use mulching to conserve soil moisture",
                    "Plant drought-resistant varieties in dry areas",
                ],
                "general": [
                    "Keep farm records for better planning",
                    "Join farmer groups for knowledge sharing",
                    "Test your soil before applying fertilizers",
                    "Practice sustainable farming methods",
                ],
            }

            category_tips = tips.get(category, tips["general"])

            return {"category": category, "tips": category_tips}, 200

        except Exception as e:
            return {"error": f"Failed to get farming tips: {str(e)}"}, 500
