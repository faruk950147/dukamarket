from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.reverse import reverse
from rest_framework import status
from rest_framework.permissions import AllowAny
from django.db.models import Prefetch, Sum, Avg, Q, Value, F
from django.db.models.functions import Coalesce
from decimal import Decimal
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.core.paginator import Paginator

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

# ========================== HELPER FUNCTIONS ==============================
def get_product_variants(product):
    # note: we already prefetched variants in get_object, 
    # so we can use them directly
    variants = product.variants.all().order_by("id")
    variant = variants.first()

    if not variant:
        return error(message="No available variants for this product.", code=404)

    sizes = []
    seen_sizes = set()

    for v in variants:
        if v.size and v.size_id not in seen_sizes:
            sizes.append({"id": v.size_id, "code": v.size.title})
            seen_sizes.add(v.size_id)

    if variant.size:
        colors = [
            {"id": v.color_id, "code": v.color.title}
            for v in variants if v.size_id == variant.size_id and v.color
        ]
    else:
        colors = [
            {"id": v.color_id, "code": v.color.title}   
            for v in variants if v.color
        ]

    return success(
        message="Product variants fetched successfully.",
        data={
            'sizes': sizes,
            'colors': colors,
            'variant': {
                "id": variant.id,
                "stock": variant.stock,
                "size": variant.size.title if variant.size else None,
                "color": variant.color.title if variant.color else None,
            }
        }
    )

def success(message, data=None, code=200):
    return Response(
        {
            "success": True,
            "message": message,
            "data": data
        },
        status=code
    )

def error(message, code=400):
    return Response(
        {
            "success": False,
            "message": message
        },
        status=code
    )

# ========================= API ROOT ==============================
class APIRoot(APIView):
    permission_classes = [AllowAny]
    def get(self, request, format=None):
        product = Product.objects.filter(status=StatusChoices.Active).select_related(
            "category", "brand"
        ).first()

        return Response({
            "home": "http://127.0.0.1:8000/api/store/home/",
            "product_detail": f"http://127.0.0.1:8000/api/store/product/detail/{product.slug}/{product.id}/",
            "get_variant_by_size": "http://127.0.0.1:8000/api/store/get/variant/by/size/",
            "get_variant_by_color": "http://127.0.0.1:8000/api/store/get/variant/by/color/",
            "get_filter_products": "http://127.0.0.1:8000/api/store/get/filter/products/",
            "product_reviews": "http://127.0.0.1:8000/api/store/product/reviews/",
            "shopping": "http://127.0.0.1:8000/api/store/shopping/",
            "category_products": "http://127.0.0.1:8000/api/store/category/products/",
            "searching_products": "http://127.0.0.1:8000/api/store/searching/products/",
            "auto_search_complete": "http://127.0.0.1:8000/api/store/auto/search/complete/",
        })
        
# ========================== HOME API ==============================
class HomeViewAPI(APIView):
    permission_classes = [AllowAny]

    def get(self, request):

        sliders_qs = (
            Slider.objects
            .filter(status=StatusChoices.Active)
            .select_related("product")
        )

        allow_payment_qs = AllowPayment.objects.filter(
            status=StatusChoices.Active
        )

        products_qs = (
            Product.objects
            .filter(status=StatusChoices.Active)
            .annotate(
                total_variant_stock=Coalesce(Sum("variants__stock",
                    filter=Q(variants__status=StatusChoices.Active)
                ), Value(0)),
                avg_rate=Coalesce(Avg("reviews__rating",
                    filter=Q(reviews__status=StatusChoices.Active)
                ),Value(Decimal("0.0")))
            )
            .filter(Q(stock__gt=0) | Q(total_variant_stock__gt=0))
            .select_related("category", "brand")
            .prefetch_related(
                Prefetch(
                    "variants",
                    queryset=VariantOption.objects.filter(
                        status=StatusChoices.Active
                    ).select_related("size", "color")
                ),
                Prefetch(
                    "reviews",
                    queryset=Review.objects.filter(
                        status=StatusChoices.Active
                    )
                ),
                Prefetch(
                    "galleries",
                    queryset=Gallery.objects.filter(
                        status=StatusChoices.Active
                    )
                ))
        )

        data = {
            "sliders": SliderSerializer(
                sliders_qs.filter(slider_type=SliderType.SLIDER), many=True
            ).data,

            "adds": SliderSerializer(
                sliders_qs.filter(slider_type=SliderType.ADD), many=True
            ).data,

            "featured": SliderSerializer(
                sliders_qs.filter(slider_type=SliderType.FEATURE), many=True
            ).data,

            "promotions": SliderSerializer(
                sliders_qs.filter(slider_type=SliderType.PROMOTION), many=True
            ).data,

            "allow_payment": AllowPaymentSerializer(
                allow_payment_qs, many=True
            ).data,

            "products": ProductSerializer(
                products_qs, many=True
            ).data,
        }

        return success(message="Home data fetched successfully.", data=data)
        
# ========================== PRODUCT DETAIL API ==============================
class ProductDetailViewAPI(APIView):
    permission_classes = [AllowAny]

    def get_object(self, slug, id):
        return get_object_or_404(
            Product.objects.select_related("category", "brand").prefetch_related(
                Prefetch("variants", queryset=VariantOption.objects.filter(
                    status=StatusChoices.Active,
                    stock__gt=0).select_related("size", "color")),
                Prefetch("galleries", queryset=Gallery.objects.filter(
                    status=StatusChoices.Active)),
                Prefetch("reviews", queryset=Review.objects.filter(
                    status=StatusChoices.Active)),
            ).annotate(
                avg_rate=Avg("reviews__rating",
                    filter=Q(reviews__status=StatusChoices.Active))),
            slug=slug,
            id=id,
            status=StatusChoices.Active,
        )

    def get(self, request, slug, id):

        product = self.get_object(slug, id)

        # ================= VISITED =================
        session_key = f'viewed_product_{product.id}'

        if not request.session.get(session_key):
            Product.objects.filter(id=product.id).update(
                visited=F('visited') + 1
            )
            request.session[session_key] = True
            product.visited += 1

        # ================= RELATED PRODUCTS =================
        related_products = (
            Product.objects
            .filter(
                category_id=product.category_id,
                status=StatusChoices.Active
            )
            .exclude(id=product.id)
            .select_related("category", "brand")
            .prefetch_related("galleries")
            .order_by("-visited", "-id")[:1]
        )

        # ================= VARIANTS LOGIC =================
        if product.variants_type != VariantType.NONE:
            # note: we already prefetched variants in get_object, 
            # so we can use them directly
            variants = product.variants.all().order_by("id")
            variant = variants.first()

            if not variant:
                return error(message="No available variants for this product.", code=404)

            sizes = []
            seen_sizes = set()

            for v in variants:
                if v.size and v.size_id not in seen_sizes:
                    sizes.append({"id": v.size_id, "code": v.size.title})
                    seen_sizes.add(v.size_id)

            if variant.size:
                colors = [
                    {"id": v.color_id, "code": v.color.title}
                    for v in variants if v.size_id == variant.size_id and v.color
                ]
            else:
                colors = [
                    {"id": v.color_id, "code": v.color.title}   
                    for v in variants if v.color
                ]

        else:
            variants = []
            sizes, colors, variant = [], [], None

        # ================= RESPONSE =================
        data = {
            "product": ProductSerializer(product).data,
            "visited": product.visited,

            "related_products": ProductSerializer(related_products, many=True).data,
            
            "variants": VariantOptionSerializer(variants, many=True).data,

            "sizes": sizes,
            "colors": colors,

            'variant': ({
                "id": variant.id,
                "stock": variant.stock,
                "size": variant.size.title if variant.size else None,
                "color": variant.color.title if variant.color else None,
            } if variant else None),
                        
            "galleries": GallerySerializer(product.galleries.all(), many=True).data,

            "reviews": ReviewSerializer(product.reviews.all(), many=True).data,
        }

        return success(message="Product details fetched successfully.", data=data)

#========================== SIZE WISE COLOR ==========================
class GetVariantBySizeViewAPI(APIView):
    def post(self, request):
        try:
            product_id = request.data.get('product_id')
            size_id = request.data.get('size_id')

            variant = VariantOption.objects.filter(
                product_id=product_id,
                size_id=size_id,
                status=StatusChoices.Active,
                stock__gt=0
            ).select_related(
                'product', 'size', 'color'
            ).order_by('id').first()

            if not variant:
                return error(
                    message="Variant not found",
                    code=404
                )

            data = {
                "variant": VariantOptionSerializer(variant).data,
                "details": {
                    "id": variant.id,
                    "stock": variant.stock,
                    "size": variant.size.title if variant.size else None,
                    "color": variant.color.title if variant.color else None,
                }
            }

            return success(
                message="Variant fetched successfully.",
                data=data
            )

        except Exception as e:
            return error(message=str(e), code=500)

#========================== JUST COLOR ==========================
class GetVariantByColorViewAPI(APIView):
    def post(self, request):
        try:
            variant_id = request.data.get('variant_id')

            variant = VariantOption.objects.select_related(
                'product', 'size', 'color'
            ).filter(
                id=variant_id,
                status=StatusChoices.Active,
                stock__gt=0
            ).first()

            if not variant:
                return error(
                    message="Variant not found",
                    code=404
                )

            data = {
                "variant": VariantOptionSerializer(variant).data,
                "details": {
                    "id": variant.id,
                    "stock": variant.stock,
                    "size": variant.size.title if variant.size else None,
                    "color": variant.color.title if variant.color else None,
                }
            }

            return success(
                message="Variant fetched successfully.",
                data=data
            )

        except Exception as e:
            return error(message=str(e), code=500)

# ======================== GET FILTER ===========================
class GetFilterProductsViewAPI(APIView):
    def post(self, request):   
        products_qs = (
            Product.objects
            .filter(status=StatusChoices.Active)
            .annotate(
                total_variant_stock=Coalesce(Sum("variants__stock",
                    filter=Q(variants__status=StatusChoices.Active)
                ), Value(0)),
                avg_rate=Coalesce(Avg("reviews__rating",
                    filter=Q(reviews__status=StatusChoices.Active)
                ),Value(Decimal("0.0")))
            )
            .filter(Q(stock__gt=0) | Q(total_variant_stock__gt=0))
            .select_related("category", "brand")
            .prefetch_related(
                Prefetch(
                    "variants",
                    queryset=VariantOption.objects.filter(
                        status=StatusChoices.Active
                    ).select_related("size", "color")
                ),
                Prefetch(
                    "reviews",
                    queryset=Review.objects.filter(
                        status=StatusChoices.Active
                    )
                ),
                Prefetch(
                    "galleries",
                    queryset=Gallery.objects.filter(
                        status=StatusChoices.Active
                    )
                ))
        )

        category_ids = request.data.get("category", [])
        if category_ids:
            products_qs = products_qs.filter(
                category_id__in=category_ids
            )

        brand_ids = request.data.get("brand", [])
        if brand_ids:
            products_qs = products_qs.filter(
                brand_id__in=brand_ids
            )

        max_price = request.data.get("maxPrice")

        if max_price:
            products_qs = products_qs.filter(
                sale_price__lte=Decimal(max_price)
            )

        serializer = ProductSerializer(
            products_qs,
            many=True
        )

        return Response(serializer.data)

# ========================= REVIEW ===============================
class ProductReviewViewAPI(APIView):

    def post(self, request):

        serializer = ReviewSerializer(data=request.data)

        if serializer.is_valid():
            serializer.save(user=request.user)

            return Response({
                    "success": True,
                    "message": "Review submitted",
                    "data": serializer.data
                },
                status=status.HTTP_201_CREATED)

        return Response({
                "success": False,
                "errors": serializer.errors
            },
            status=status.HTTP_400_BAD_REQUEST)

# =============================== SHOP LIST =========================
class ShopViewAPI(APIView):
    permission_classes = [AllowAny]
    def get(self, request):

        products_qs = (
            Product.objects
            .filter(status=StatusChoices.Active)
            .annotate(
                total_variant_stock=Coalesce(
                    Sum(
                        "variants__stock",
                        filter=Q(
                            variants__status=StatusChoices.Active
                        )
                    ),
                    Value(0)
                ),

                avg_rate=Coalesce(
                    Avg(
                        "reviews__rating",
                        filter=Q(
                            reviews__status=StatusChoices.Active
                        )
                    ),
                    Value(Decimal("0.0"))
                )
            )
            .filter(
                Q(stock__gt=0) |
                Q(total_variant_stock__gt=0)
            )
            .select_related(
                "category",
                "brand"
            )
            .prefetch_related(
                Prefetch(
                    "variants",
                    queryset=VariantOption.objects.filter(
                        status=StatusChoices.Active
                    ).select_related(
                        "size",
                        "color"
                    )
                ),

                Prefetch(
                    "reviews",
                    queryset=Review.objects.filter(
                        status=StatusChoices.Active
                    )
                ),

                Prefetch(
                    "galleries",
                    queryset=Gallery.objects.filter(
                        status=StatusChoices.Active
                    )
                )
            )
        )

        banners = Slider.objects.filter(
            slider_type=SliderType.ADD,
            status=StatusChoices.Active
        )[:1]

        try:
            per_page = int(
                request.GET.get("per_page") or 3
            )

            page_number = int(
                request.GET.get("page") or 1
            )

        except ValueError:
            per_page = 3
            page_number = 1


        sort_by = request.GET.get(
            "sort",
            "latest"
        )

        if sort_by == "upcoming":

            products_qs = (
                products_qs
                .filter(
                    deadline__gt=timezone.now()
                )
                .order_by(
                    "deadline"
                )
            )

        else:

            sort_map = {
                "latest": "-created_at",
                "new": "created_at",
            }

            products_qs = (
                products_qs
                .order_by(
                    sort_map.get(
                        sort_by,
                        "-created_at"
                    )
                )
            )


        paginator = Paginator(
            products_qs,
            per_page
        )

        page_obj = paginator.get_page(
            page_number
        )

        data = {
            "banners": SliderSerializer(
                banners,
                many=True
            ).data,

            "products": ProductSerializer(
                page_obj.object_list,
                many=True
            ).data,

            "pagination": {
                "current_page": page_obj.number,
                "total_pages": paginator.num_pages,
                "total_items": paginator.count,
                "has_next": page_obj.has_next(),
                "has_previous": page_obj.has_previous(),
            }
        }

        return success(
            message="Shop data fetched successfully.",
            data=data
        )

# =============================== CATEGORY PRODUCT ==========================
class CategoryProductViewAPI(APIView):
    permission_classes = [AllowAny]

    def get(self, request, slug, id):

        category = get_object_or_404(
            Category,
            slug=slug,
            id=id,
            status=StatusChoices.Active
        )


        products_qs = (
            Product.objects
            .filter(
                category=category,
                status=StatusChoices.Active
            )
            .annotate(
                total_variant_stock=Coalesce(
                    Sum(
                        "variants__stock",
                        filter=Q(
                            variants__status=StatusChoices.Active
                        )
                    ),
                    Value(0)
                ),

                avg_rate=Coalesce(
                    Avg(
                        "reviews__rating",
                        filter=Q(
                            reviews__status=StatusChoices.Active
                        )
                    ),
                    Value(Decimal("0.0"))
                )
            )
            .filter(
                Q(stock__gt=0) |
                Q(total_variant_stock__gt=0)
            )
            .select_related(
                "category",
                "brand"
            )
            .prefetch_related(
                Prefetch(
                    "variants",
                    queryset=VariantOption.objects.filter(
                        status=StatusChoices.Active
                    ).select_related(
                        "size",
                        "color"
                    )
                ),

                Prefetch(
                    "reviews",
                    queryset=Review.objects.filter(
                        status=StatusChoices.Active
                    )
                ),

                Prefetch(
                    "galleries",
                    queryset=Gallery.objects.filter(
                        status=StatusChoices.Active
                    )
                )
            )
        )


        sort_by = request.GET.get(
            "sort",
            "latest"
        )


        if sort_by == "upcoming":

            products_qs = (
                products_qs
                .filter(
                    deadline__gt=timezone.now()
                )
                .order_by(
                    "deadline"
                )
            )

        elif sort_by == "new":

            products_qs = (
                products_qs
                .order_by(
                    "created_at"
                )
            )

        else:

            products_qs = (
                products_qs
                .order_by(
                    "-created_at"
                )
            )


        per_page_options = [
            3,
            6,
            12,
            24
        ]


        try:

            per_page = int(
                request.GET.get(
                    "per_page",
                    3
                )
            )

        except ValueError:

            per_page = 3


        if per_page not in per_page_options:

            per_page = 3


        paginator = Paginator(
            products_qs,
            per_page
        )


        page_obj = paginator.get_page(
            request.GET.get(
                "page",
                1
            )
        )


        banners = (
            Slider.objects
            .filter(
                slider_type=SliderType.ADD,
                status=StatusChoices.Active
            )[:1]
        )


        data = {

            "category": CategorySerializer(
                category
            ).data,

            "banners": SliderSerializer(
                banners,
                many=True
            ).data,

            "products": ProductSerializer(
                page_obj.object_list,
                many=True
            ).data,

            "pagination": {
                "current_page": page_obj.number,
                "total_pages": paginator.num_pages,
                "total_items": paginator.count,
                "has_next": page_obj.has_next(),
                "has_previous": page_obj.has_previous(),
            }
        }


        return success(
            message="Category products fetched successfully.",
            data=data
        )

# ============================= SEARCH ===============================
class SearchingViewAPI(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        query = request.data.get('q', '').strip()

        products_qs = (
            Product.objects
            .filter(status=StatusChoices.Active)
            .annotate(
                total_variant_stock=Coalesce(
                    Sum(
                        "variants__stock",
                        filter=Q(
                            variants__status=StatusChoices.Active
                        )
                    ),
                    Value(0)
                ),

                avg_rate=Coalesce(
                    Avg(
                        "reviews__rating",
                        filter=Q(
                            reviews__status=StatusChoices.Active
                        )
                    ),
                    Value(Decimal("0.0"))
                )
            )
            .filter(
                Q(stock__gt=0) |
                Q(total_variant_stock__gt=0)
            )
            .select_related(
                "category",
                "brand"
            )
            .prefetch_related(
                Prefetch(
                    "variants",
                    queryset=VariantOption.objects.filter(
                        status=StatusChoices.Active
                    ).select_related(
                        "size",
                        "color"
                    )
                ),

                Prefetch(
                    "reviews",
                    queryset=Review.objects.filter(
                        status=StatusChoices.Active
                    )
                ),

                Prefetch(
                    "galleries",
                    queryset=Gallery.objects.filter(
                        status=StatusChoices.Active
                    )
                )
            )
        )

        # Search filter
        if query:
            products_qs = products_qs.filter(
                Q(title__icontains=query) |
                Q(slug__icontains=query) |
                Q(category__title__icontains=query) |
                Q(brand__title__icontains=query)
            ).distinct()

        data = ProductSerializer(
            products_qs,
            many=True,
            context={"request": request}
        ).data

        return Response({
            "success": True,
            "count": len(data),
            "results": data
        })

# ====================== AUTO COMPLETE ==========================
class AutoSearchCompleteAPI(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        term = request.GET.get("term", "").strip()
        results = []

        products_qs = (
            Product.objects
            .filter(status=StatusChoices.Active)
            .annotate(
                total_variant_stock=Coalesce(
                    Sum(
                        "variants__stock",
                        filter=Q(
                            variants__status=StatusChoices.Active
                        )
                    ),
                    Value(0)
                ),

                avg_rate=Coalesce(
                    Avg(
                        "reviews__rating",
                        filter=Q(
                            reviews__status=StatusChoices.Active
                        )
                    ),
                    Value(Decimal("0.0"))
                )
            )
            .filter(
                Q(stock__gt=0) |
                Q(total_variant_stock__gt=0)
            )
            .select_related(
                "category",
                "brand"
            )
        )

        if term:
            products_qs = (
                products_qs
                .filter(
                    Q(title__icontains=term)
                )
                .distinct()[:10]
            )

            for product in products_qs:
                results.append({
                    "id": product.id,
                    "label": product.title,
                    "value": product.title,
                    "slug": product.slug,
                    "avg_rate": product.avg_rate,
                })

        return Response(results)





