from django.db import models
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from django.utils.html import format_html
from django.utils.text import slugify
from django.core.validators import (
    FileExtensionValidator,
    MaxValueValidator,
    MinValueValidator,
)
from django.core.exceptions import ValidationError
from django.utils import timezone
from decimal import Decimal

from validation.validators import validate_image_size
from mixins.mixing import ImageTagMixin, ColorTagMixin

User =  get_user_model()

# ======================== SLUG GENERATOR ========================
def generate_unique_slug(model_class, title):
    base_slug = slugify(title)
    slug = base_slug
    counter = 1

    while model_class.objects.filter(slug=slug).exists():
        slug = f"{base_slug}-{counter}"
        counter += 1

    return slug

# ======================== CONSTANTS ========================
class Constants:
    IMAGE_VALIDATORS = [
        FileExtensionValidator(allowed_extensions=["jpg", "jpeg", "png", "webp"]),
        validate_image_size,
    ]

# ======================== STATUS CHOICES ========================
class StatusChoices(models.TextChoices):
    Active = "active", _("Active")
    Inactive = "inactive", _("Inactive")

# ======================== VARIANT ========================
class VariantType(models.TextChoices):
    NONE = "none", _("None")
    COLOR = "color", _("Color")
    SIZE = "size", _("Size")
    COLOR_SIZE = "color_size", _("Color Size")

# ======================== SLIDER ========================
class SliderType(models.TextChoices):
    NONE = "none", _("None")
    SLIDER = "slider", _("Slider")
    ADD = "add", _("Add")
    FEATURE = "feature", _("Feature")
    PROMOTION = "promotion", _("Promotion")

# ======================== BASE MIXIN ========================
class BaseMixin(models.Model):
    status = models.CharField(
        _("status"),
        max_length=20,
        choices=StatusChoices.choices,
        default=StatusChoices.Active,
    )
    created_at = models.DateTimeField(_("created_at"), auto_now_add=True)
    updated_at = models.DateTimeField(_("updated_at"), auto_now=True)

    class Meta:
        abstract = True

# ======================== COMMON MIXIN ========================
class CommonMixin(models.Model):
    slug = models.SlugField(_("slug"), max_length=255, unique=True, blank=True)
    keyword = models.CharField(_("keyword"), max_length=255, blank=True, null=True)
    description = models.CharField(_("description"), max_length=255, blank=True, null=True)

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        if hasattr(self, "title") and self.title and not self.slug:
            self.slug = generate_unique_slug(self.__class__, self.title)

        super().save(*args, **kwargs)

# ======================== CATEGORY ========================
class Category(BaseMixin, CommonMixin, ImageTagMixin):
    parent = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="children",
    )
    title = models.CharField(_("title"), max_length=255, unique=True)
    
    image = models.ImageField(
        _("image"),
        upload_to="categories/%Y/%m/%d/",
        default="defaults/default.jpg",
        validators=Constants.IMAGE_VALIDATORS,
    )
    
    is_featured = models.BooleanField(_("is_featured"), default=False)
    
    class Meta:
        db_table = "store_categories"
        verbose_name = "01. Category"
        verbose_name_plural = "01. Categories"
        
        ordering = ["id"]
        
        indexes = [
            models.Index(fields=["parent", "title", "slug"]),
            models.Index(fields=["is_featured", "status", "created_at"]),
        ]

    def clean(self):
        if self.parent and self.parent == self:
            raise ValidationError(_("Category cannot be its own parent."))

    def __str__(self):
        return f"{self.title} ({self.get_status_display()})"

# ======================== BRAND ========================
class Brand(BaseMixin, CommonMixin, ImageTagMixin):
    title = models.CharField(_("title"), max_length=255, unique=True)

    image = models.ImageField(
        _("image"),
        upload_to="brands/%Y/%m/%d/",
        default="defaults/default.jpg",
        validators=Constants.IMAGE_VALIDATORS,
    )
    
    is_featured = models.BooleanField(_("is_featured"), default=False)
    
    class Meta:
        db_table = "store_brands"
        verbose_name = "02. Brand"
        verbose_name_plural = "02. Brands"
        
        ordering = ["id"]
        
        indexes = [
            models.Index(fields=["title", "slug"]),
            models.Index(fields=["is_featured", "status", "created_at"]),
        ]

    def __str__(self):
        return f"{self.title} ({self.get_status_display()})"

# ======================== COLOR VARIANT ========================
class Color(BaseMixin, ColorTagMixin):
    title = models.CharField(_("title"), max_length=255, unique=True)
    code = models.CharField(_("code"), max_length=20, unique=True)
    
    class Meta:
        db_table = "store_colors"
        verbose_name = '03. Product Color'
        verbose_name_plural = '03. Product Colors'
        
        ordering = ['id']
        
        indexes = [
            models.Index(fields=["title", "code"]),
            models.Index(fields=["status", "created_at"]),
        ]

    def __str__(self):
        return f"{self.title} ({self.get_status_display()})"

# ======================= SIZE VARIANT ========================
class Size(BaseMixin):
    title = models.CharField(_("title"), max_length=255, unique=True)
    code = models.CharField(_("code"), max_length=20, unique=True)
    
    class Meta:
        db_table = "store_sizes"
        verbose_name = '04. Product Size'
        verbose_name_plural = '04. Product Sizes'
        
        ordering = ['id']
        
        indexes = [
            models.Index(fields=["title", "code"]),
            models.Index(fields=["status", "created_at"]),
        ]

    def __str__(self):
        return f"{self.title} ({self.get_status_display()})"

# ======================== PRODUCT ========================
class Product(BaseMixin, CommonMixin, ImageTagMixin):
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="products",
    )
    brand = models.ForeignKey(
        Brand,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="products",
    )
    variants_type = models.CharField(
        max_length=20,
        choices=VariantType.choices,
        default=VariantType.NONE,
    )

    title = models.CharField(_("title"), max_length=255, unique=True)
    tag = models.CharField(_("tag"), max_length=150, blank=True, null=True)

    old_price = models.DecimalField(
        _("old price"),
        max_digits=10,
        decimal_places=2,
        default=Decimal("0.00"),
    )
    sale_price = models.DecimalField(
        _("sale price"),
        max_digits=10,
        decimal_places=2,
        default=Decimal("0.00"),
    )
    discount = models.DecimalField(
        _("discount"),
        max_digits=10,
        decimal_places=2,
        default=Decimal("0.00"),
    )
    stock = models.PositiveIntegerField(
        _("stock"),
        default=0,
        validators=[MaxValueValidator(10000)],
    )

    sold = models.PositiveIntegerField(_("sold"), default=0)
    visited = models.PositiveIntegerField(_("visited"), default=0)

    prev_des = models.TextField(_("prev_des"), blank=True, null=True)
    add_des = models.TextField(_("add_des"), blank=True, null=True)
    short_des = models.TextField(_("short_des"), blank=True, null=True)
    long_des = models.TextField(_("long_des"), blank=True, null=True)

    deadline = models.DateTimeField(_("deadline"), blank=True, null=True)
    is_deadline = models.BooleanField(
        _("is_deadline"),
        default=False
    )
    is_featured = models.BooleanField(
        _("is_featured"),
        default=False,
    )

    class Meta:
        db_table = "store_products"
        verbose_name = "05. Product"
        verbose_name_plural = "05. Products"
        
        ordering = ["id"]
        
        indexes = [
            models.Index(fields=["category", "brand", "variants_type"]),
            models.Index(fields=[
                "title", "slug", "tag", "old_price", "sale_price", "stock"
            ]),
            models.Index(fields=["sold", "visited", "deadline", "is_deadline"]),
            models.Index(fields=["is_featured", "status", "created_at"]),
        ]

    def automatic_discount_calculation(self):
        # automatic discount calculation based on old_price and sale_price
        if self.old_price > 0:
            self.discount = (
                ((self.old_price - self.sale_price) / self.old_price)
                * Decimal("100")
            ).quantize(Decimal("0.01"))

        else:
            self.discount = Decimal("0.00")

    def clean(self):
        if self.is_deadline and self.deadline and self.deadline < timezone.now():
            raise ValidationError("Deadline cannot be in the past.")

        if self.sale_price > self.old_price:
            raise ValidationError("Sale price cannot be greater than old price.")

        if self.discount < 0 or self.discount > 100:
            raise ValidationError("Discount must be between 0 and 100.")

    def save(self, *args, **kwargs):
        validate = kwargs.pop("validate", True)

        self.automatic_discount_calculation()

        if validate:
            self.full_clean()

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.title} ({self.get_status_display()})"

# ======================== GALLERY ========================
class Gallery(BaseMixin, ImageTagMixin):
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="galleries",
    )
    image = models.ImageField(
        _("image"),
        upload_to="products/gallery/%Y/%m/%d/",
        validators=Constants.IMAGE_VALIDATORS,
    )

    class Meta:
        db_table = "store_galleries"
        verbose_name = "06. Gallery"
        verbose_name_plural = "06. Galleries"
        
        ordering = ["id"]
        
        indexes = [
            models.Index(fields=["product"]),
            models.Index(fields=["status"]),
            models.Index(fields=["created_at"]),
        ]

    def __str__(self):
        return f"Gallery for {self.product.title} ({self.get_status_display()})"

# ======================= VARIANT OPTION ========================
class VariantOption(BaseMixin):
    product = models.ForeignKey(
        Product,
        related_name='variants',
        on_delete=models.CASCADE
    )
    color = models.ForeignKey(
        Color,
        blank=True,
        null=True,
        on_delete=models.SET_NULL
    )
    size = models.ForeignKey(
        Size,
        blank=True,
        null=True,
        on_delete=models.SET_NULL
    )

    image_id = models.PositiveIntegerField(
        blank=True,
        null=True,
        default=0
    )

    sku = models.CharField(
        max_length=100,
        unique=True
    )
    variant_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00')
    )
    stock = models.PositiveIntegerField(default=0)

    class Meta:
        db_table = "store_variant_options"
        verbose_name = "07. Variant Option"
        verbose_name_plural = "07. Variant Options"

        ordering = ["id"]

        indexes = [
            models.Index(fields=["product"]),
            models.Index(fields=["color"]),
            models.Index(fields=["size"]),
            models.Index(fields=["sku", "variant_price", "stock"]),
            models.Index(fields=["status"]),
            models.Index(fields=["created_at"]),
        ]

    def clean(self):
        if self.product.variants_type == 'color' and not self.color:
            raise ValidationError("This product requires a color variant.")

        if self.product.variants_type == 'size' and not self.size:
            raise ValidationError("This product requires a size variant.")

        if self.product.variants_type == 'color_size':
            if not self.color or not self.size:
                raise ValidationError("This product requires both color and size.")

        if self.product.variants_type == 'none':
            if self.color or self.size:
                raise ValidationError("This product does not use variants.")

    def get_image(self):
        image = Gallery.objects.filter(
            id=self.image_id,
            product=self.product
        ).first()

        return image.image if image else None

    @property
    def image_url(self):
        img = self.get_image() 
        return img.url if img else None

    @property
    def image_tag(self):
        img = self.get_image()

        if img and hasattr(img, 'url'):
            return format_html(
                '''
                <img src="{}" style="width:30px; height:30px; 
                object-fit:cover; border-radius:5px; border:1px solid #ddd;"/>
                ''',
                img.url
            )
        return format_html('<span>No Image</span>')

    def __str__(self):
        size = self.size.title if self.size else "No Size"
        color = self.color.title if self.color else "No Color"
        return f"({self.product.title}) - ({size} - {color})"

# ======================== SLIDER ========================
class Slider(BaseMixin, ImageTagMixin):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    slider_type = models.CharField(max_length=10, choices=SliderType.choices, default=SliderType.NONE)
    headline = models.CharField(max_length=150, blank=True, null=True)
    paragraph = models.CharField(max_length=150, blank=True, null=True)
    image = models.ImageField(upload_to='sliders/%Y/%m/%d/', default='defaults/default.jpg', validators=[validate_image_size])

    class Meta:
        db_table = "store_sliders"
        verbose_name = "08. Slider"
        verbose_name_plural = "08. Sliders"

        ordering = ["id"]

        indexes = [
            models.Index(fields=["product"]),
            models.Index(fields=["slider_type"]),
            models.Index(fields=["created_at"]),
        ]

    def __str__(self):
        return f"{self.product.title} ({self.get_status_display()})"    

# ======================== REVIEW ========================
class Review(BaseMixin, ImageTagMixin):
    product = models.ForeignKey(Product, related_name='reviews', on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    subject = models.CharField(max_length=50)
    comment = models.TextField(max_length=500)
    rating = models.FloatField(default=1, validators=[MinValueValidator(1), MaxValueValidator(5)])
    
    class Meta:
        db_table = "store_reviews"
        verbose_name = "09. Review"
        verbose_name_plural = "09. Reviews"

        ordering = ["id"]

        indexes = [
            models.Index(fields=["product"]),
            models.Index(fields=["user"]),
            models.Index(fields=["rating"]),
            models.Index(fields=["created_at"]),
        ]

    def __str__(self):
        return self.subject or f"Review by {self.user.username}"        

# ========================= ALLOW PAYMENT ========================
class AllowPayment(BaseMixin, ImageTagMixin):
    title = models.CharField(max_length=150, unique=True)
    help_time = models.CharField(max_length=150, default="24/7 Support")
    image = models.ImageField(upload_to='allows_payments/%Y/%m/%d/', default='defaults/default.jpg', validators=[validate_image_size])
    is_featured = models.BooleanField(default=False)

    class Meta:
        db_table = "store_allow_payments"
        verbose_name = '10. Allow Payment'
        verbose_name_plural = '10. Allow Payments'
        
        ordering = ['id']
        
        indexes = [ 
            models.Index(fields=["title"]),
            models.Index(fields=["is_featured", "status", "created_at"]),
        ]

    def __str__(self):
        return f"{self.title} ({self.get_status_display()})"       
        
