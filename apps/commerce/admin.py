from django.contrib import admin
from .models import (
    OrganisationPointAccount,
    ProductPointAccount,
    PointTransaction,
    OrganisationPointGrant,
    PlatformFeeConfiguration,
    Cart,
    SalesOrder,
    SalesOrderLineItem,
    PointOrder,
)


@admin.register(OrganisationPointAccount)
class OrganisationPointAccountAdmin(admin.ModelAdmin):
    list_display = ("organisation", "total_points", "created_at")
    search_fields = ("organisation__name",)


@admin.register(ProductPointAccount)
class ProductPointAccountAdmin(admin.ModelAdmin):
    list_display = ("product", "total_points", "created_at")
    search_fields = ("product__name",)


@admin.register(PointTransaction)
class PointTransactionAdmin(admin.ModelAdmin):
    list_display = ("account", "product_account", "amount", "transaction_type", "created_at")
    search_fields = ("account__organisation__name", "product_account__product__name")
    list_filter = ("transaction_type",)


@admin.register(OrganisationPointGrant)
class OrganisationPointGrantAdmin(admin.ModelAdmin):
    list_display = ("organisation", "amount", "granted_by", "created_at")
    search_fields = ("organisation__name", "granted_by__username")


@admin.register(PlatformFeeConfiguration)
class PlatformFeeConfigurationAdmin(admin.ModelAdmin):
    list_display = ("percentage", "applies_from_date")
    ordering = ("-applies_from_date",)


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ("user", "organisation", "product", "status", "created_at", "total_amount", "user_country")
    list_filter = ("status",)
    search_fields = ("user__username", "organisation__name", "product__name")

    def total_amount(self, obj):
        return f"${obj.total_amount:.2f}"

    total_amount.short_description = "Total Amount"


class SalesOrderLineItemInline(admin.TabularInline):
    model = SalesOrderLineItem
    extra = 0
    readonly_fields = ("total_price_cents",)


@admin.register(SalesOrder)
class SalesOrderAdmin(admin.ModelAdmin):
    list_display = ("id", "cart", "status", "total_usd", "created_at")
    list_filter = ("status",)
    search_fields = ("id", "cart__id")
    readonly_fields = ("total_usd_cents",)
    inlines = [SalesOrderLineItemInline]

    def total_usd(self, obj):
        return f"${obj.total_usd_cents / 100:.2f}"

    total_usd.short_description = "Total USD"


@admin.register(SalesOrderLineItem)
class SalesOrderLineItemAdmin(admin.ModelAdmin):
    list_display = ("sales_order", "item_type", "quantity", "unit_price_cents", "total_price_cents")
    list_filter = ("item_type",)
    search_fields = ("sales_order__id", "bounty__title")


@admin.register(PointOrder)
class PointOrderAdmin(admin.ModelAdmin):
    list_display = ("id", "cart", "product_account", "total_points", "status", "created_at")
    list_filter = ("status",)
    search_fields = ("id", "cart__id", "product_account__product__name")

    def total_points(self, obj):
        return f"{obj.total_points:,}"

    total_points.short_description = "Total Points"
