from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny

from store.models import (
    StatusChoices,
    SliderType,
    VariantType,
    Category,
    Brand,
    Color,
    Size,
    Product,
    Gallery,
    VariantOption,
    Slider,
    Review,
    AllowPayment,
)

from store.serializers import (
    CategorySerializer,
    BrandSerializer,
    ColorSerializer,
    SizeSerializer,
    ProductSerializer,
    GallerySerializer,
    VariantOptionSerializer,
    SliderSerializer,
    ReviewSerializer,
    AllowPaymentSerializer
)

# =========================================================
# BASE RESPONSE HELPER
# =========================================================
def success(message, data=None, code=200):
    return Response({
        "success": True,
        "message": message,
        "data": data
    }, status=code)


def error(message, code=400):
    return Response({
        "success": False,
        "message": message
    }, status=code)
    

# ============== HOME VIEW =============
class HomeViewAPI(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        # sliders filtering and serialization
        sliders_qs = Slider.objects.filter(status=StatusChoices.Active).select_related("product")

        data = {
            "sliders": SliderSerializer(sliders_qs.filter(slider_type=SliderType.SLIDER), many=True).data,
            "adds": SliderSerializer(sliders_qs.filter(slider_type=SliderType.ADD), many=True).data,
            "featured": SliderSerializer(sliders_qs.filter(slider_type=SliderType.FEATURE), many=True).data,
            "promotions": SliderSerializer(sliders_qs.filter(slider_type=SliderType.PROMOTION), many=True).data,
        }

        return Response(data, status=status.HTTP_200_OK)