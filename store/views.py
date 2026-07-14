from django.shortcuts import render, get_object_or_404
from django.views import View
from django.contrib import messages
from django.views.decorators.cache import never_cache
from django.utils.decorators import method_decorator
from django.contrib.sites.shortcuts import get_current_site
from django.db.models import Prefetch, Avg, Q, Sum, Value
from django.db.models.functions import Coalesce
from django.template.loader import render_to_string
from django.http import JsonResponse
import logging

# import from local
from mixins.mixing import LoginRequiredMixin, LogoutRequiredMixin
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


logger = logging.getLogger('project')

def get_product_variants(product):
    # note: we already prefetched variants in get_object, 
    # so we can use them directly
    variants = product.variants.all().order_by("id")
    variant = variants.first()

    if not variant:
        return {"sizes": [], "colors": [],"variant": None}

    # sizes
    seen_sizes = set()
    sizes = []

    for v in variants:
        if v.size and v.size_id not in seen_sizes:
            sizes.append({"id": v.size_id, "code": v.size.title})
            seen_sizes.add(v.size_id)

    # colors
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

    return {
        "sizes": sizes,
        "colors": colors,
        "variant": {
            "id": variant.id,
            "stock": variant.stock,
            "size": variant.size.title if variant.size else None,
            "color": variant.color.title if variant.color else None,
        }
    }

# ================== HOME PAGE ==================
@method_decorator(never_cache, name='dispatch')
class HomeView(LoginRequiredMixin, View):
    def get(self, request):
        current_site = get_current_site(request)
        print("Current Site: ", current_site.domain)
        print("Custom Host: ", request.get_host())
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
                ),Value(0.0))
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

        logger.info(f"Home page accessed by user: {request.user.username}")
        messages.success(request, f'Welcome to our store for user: {request.user.username}')
        return render(request, 'store/home.html')

# ================= PRODUCT DETAIL PAGE ==================
@method_decorator(never_cache, name='dispatch')
class ProductView(LoginRequiredMixin, View):
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
        current_site = get_current_site(request)
        print("Current Site: ", current_site.domain)

        logger.info(f"Product page accessed by user: {request.user.username}")
        messages.success(request, f'Product details page loaded for user: {request.user.username}')
        return render(request, 'store/product-detail.html', {'product': product})

# =========== SIZE WISE COLOR VARIANT FETCH ===========
@method_decorator(never_cache, name='dispatch')
class GetVariantBySizeView(View):
    def post(self, request):
        try:
            product_id = request.POST.get('product_id')
            size_id = request.POST.get('size_id')

            variants_qs = VariantOption.objects.filter(
                product_id=product_id,
                size_id=size_id,
                status=StatusChoices.Active,
                stock__gt=0
            ).select_related(
                'product', 'size', 'color'
            ).order_by('id')

            variant = variants_qs.first()

            if not variant:
                return JsonResponse(
                    {'error': 'Variant not found'},
                    status=404
                )

            html = render_to_string(
                'store/components/color_options.html',
                {
                    'colors': variants_qs,
                    'variant': variant
                },
                request=request
            )

            return JsonResponse({
                'rendered_colors': html,
                'id': variant.id,
                'price': str(variant.price),
                'image': variant.image_url,
                'stock': variant.stock,
                'size': variant.size.code if variant.size else '',
                'color': variant.color.title if variant.color else '',
                'sku': variant.sku or '',
            })

        except Exception as e:
            logger.error(
                f"GetVariantBySizeView error: {e}",
                exc_info=True
            )
            return JsonResponse(
                {'error': 'Unable to fetch variant'},
                status=500
            )

# =========== JUST COLOR FETCH ===========
@method_decorator(never_cache, name='dispatch')
class GetVariantByColorView(View):
    def post(self, request):
        try:
            variant_id = request.POST.get('variant_id')

            variant = VariantOption.objects.select_related(
                'product',
                'size',
                'color'
            ).filter(
                id=variant_id,
                status=StatusChoices.Active,
                stock__gt=0
            ).first()

            if not variant:
                return JsonResponse(
                    {'error': 'Variant not found'},
                    status=404
                )

            return JsonResponse({
                'id': variant.id,
                'price': str(variant.price),
                'stock': variant.stock,
                'image': variant.image_url,
                'size': variant.size.code if variant.size else '',
                'color': variant.color.title if variant.color else '',
                'sku': variant.sku or '',
            })

        except Exception as e:
            logger.error(
                f"GetVariantByColorView error: {e}",
                exc_info=True
            )
            return JsonResponse(
                {'error': 'Unable to fetch variant'},
                status=500
            )

# ======================== GET FILTER ===========================
class GetFilterProductsView(View):
    def post(self, request):   
        pass

# ========================= REVIEW ===============================
class ProductReviewView(View):
    def post(self, request):
        pass

# =============================== SHOP LIST =========================
class ShopView(View):
    def get(self, request):
        pass
    
# =============================== CATEGORY PRODUCT ==========================
class CategoryProductView(View):
    def get(self, request):
        pass

# ============================= SEARCH ===============================
class SearchingView(View):
    def post(self, request):
        pass
    
# ====================== AUTO COMPLETE ==========================
class AutoSearchComplete(View):
    def post(self, request):
        pass




        
        
        
        
        