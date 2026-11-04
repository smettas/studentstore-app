import re
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from .models import DeliveryPincode, DeliverySettings

def serviceability(pincode):
    settings = DeliverySettings.objects.order_by("pk").first()
    if not settings or not settings.enabled:
        return {"serviceable":False,"cod_available":False,"detail":"Delivery is not configured yet."}
    record = DeliveryPincode.objects.filter(pincode=pincode).first()
    permitted = bool(record.is_serviceable) if record else settings.allow_all_india
    cod = permitted and settings.cod_enabled and (record.cod_available if record else True)
    days_min = record.min_days if record else settings.estimated_min_days
    days_max = record.max_days if record else settings.estimated_max_days
    return {"pincode":pincode,"city":record.city if record else "","state":record.state if record else "", "serviceable":permitted,"cod_available":cod,"min_days":days_min,"max_days":days_max,"estimate_note":settings.notice if permitted else "Delivery is not available for this pincode."}

class DeliveryCheckView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []
    def get(self,request):
        pin=request.query_params.get("pincode","").strip()
        if not re.fullmatch(r"[1-9][0-9]{5}",pin):return Response({"pincode":["Enter a valid 6-digit Indian pincode."]},status=400)
        return Response(serviceability(pin))
