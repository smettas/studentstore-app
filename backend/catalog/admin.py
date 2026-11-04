from django import forms
from django.core.exceptions import ValidationError
from django.contrib import admin
from .models import Category, StudyLevel, Brand, Product, ProductImage, ProductReview

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "parent", "is_active")
    prepopulated_fields = {"slug": ("name",)}

@admin.register(StudyLevel)
class StudyLevelAdmin(admin.ModelAdmin):
    list_display = ("name", "slug")
    prepopulated_fields = {"slug": ("name",)}

@admin.register(Brand)
class BrandAdmin(admin.ModelAdmin):
    prepopulated_fields = {"slug": ("name",)}

class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 0

class ProductPricingForm(forms.ModelForm):
    pack_quantity = forms.CharField(
        max_length=120, required=False, label="Pack quantity / configuration",
        help_text="Stored in product specifications; verify the actual saleable pack before publishing.",
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            self.fields["pack_quantity"].initial = (self.instance.specifications or {}).get("pack_quantity", "")

    def save(self, commit=True):
        product = super().save(commit=False)
        pack = self.cleaned_data.get("pack_quantity", "").strip()
        data = dict(product.specifications or {})
        previous = data.get("pack_quantity", "")
        if "pack_quantity" in self.changed_data or not product.pk:
            data["pack_quantity"] = pack
            if pack and pack != previous:
                data["pack_review_required"] = False
        product.specifications = data
        if commit:
            product.save()
            self.save_m2m()
        return product

    class Meta:
        model = Product
        fields = "__all__"
        labels = {
            "price": "MRP / original price (₹)",
            "discount_price": "Offer / selling price (₹) — optional",
        }
        help_texts = {
            "price": "Enter the regular product price. When there is no offer, customers pay this amount.",
            "discount_price": "Leave blank for no discount. Enter a lower selling price to show the crossed-out MRP and automatically calculated % OFF.",
        }

    def clean(self):
        data = super().clean()
        mrp, offer = data.get("price"), data.get("discount_price")
        if mrp is not None and mrp <= 0:
            self.add_error("price", "MRP must be greater than zero.")
        if offer is not None and (offer <= 0 or (mrp is not None and offer >= mrp)):
            self.add_error("discount_price", "Offer price must be greater than zero and lower than MRP. Leave blank for no offer.")
        return data


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    form = ProductPricingForm
    @admin.display(description="Offer %")
    def offer_percentage(self, obj):
        if obj.discount_price is None or not obj.price or obj.discount_price >= obj.price:
            return "—"
        return f"{round((obj.price - obj.discount_price) * 100 / obj.price)}% OFF"

    list_display = ("sku", "name", "category", "price", "discount_price", "offer_percentage", "stock", "is_active")
    list_filter = ("category", "brand", "study_levels", "product_type", "is_active")
    search_fields = ("name", "sku", "brand__name", "category__name")
    list_editable = ("stock", "is_active")
    actions = ("activate_selected", "deactivate_selected")

    @admin.action(description="Activate selected products")
    def activate_selected(self, request, queryset):
        queryset.update(is_active=True)

    @admin.action(description="Deactivate selected products")
    def deactivate_selected(self, request, queryset):
        queryset.update(is_active=False)
    prepopulated_fields = {"slug": ("name",)}
    filter_horizontal = ("study_levels",)
    inlines = [ProductImageInline]


@admin.register(ProductReview)
class ProductReviewAdmin(admin.ModelAdmin):
    list_display = ("product", "user", "rating", "is_approved", "created_at")
    list_filter = ("is_approved", "rating", "created_at")
    search_fields = ("product__name", "product__sku", "comment", "title")
    list_editable = ("is_approved",)
    readonly_fields = ("product", "user", "rating", "title", "comment", "created_at", "updated_at")
    actions = ["approve_reviews", "hide_reviews"]

    @admin.action(description="Approve selected reviews")
    def approve_reviews(self, request, queryset):
        queryset.update(is_approved=True)

    @admin.action(description="Hide selected reviews")
    def hide_reviews(self, request, queryset):
        queryset.update(is_approved=False)
