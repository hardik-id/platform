from django.contrib import admin
from .models import (
    Organisation,
    OrganisationWallet,
    OrganisationWalletTransaction,
    OrganisationPointAccount,
    ProductPointAccount,
    PointTransaction,
    OrganisationPointGrant,
    PlatformFeeConfiguration,
    Cart,
    CartLineItem,
    SalesOrder,
    SalesOrderLineItem,
    PointOrder,
)

@admin.register(Organisation)
class OrganisationAdmin(admin.ModelAdmin):
    list_display = ("name", "country", "tax_id")
    search_fields = ("name", "tax_id")
    list_filter = ("country",)

class OrganisationWalletTransactionInline(admin.TabularInline):
    model = OrganisationWalletTransaction
    extra = 0
    readonly_fields = ("created_at", "transaction_type", "amount_usd", "description")

    def amount_usd(self, obj):
        return f"${obj.amount_cents / 100:.2f}"
    amount_usd.short_description = "Amount (USD)"

@admin.register(OrganisationWallet)
class OrganisationWalletAdmin(admin.ModelAdmin):
    list_display = ("organisation", "balance_usd", "created_at")
    search_fields = ("organisation__name",)
    inlines = [OrganisationWalletTransactionInline]

    def balance_usd(self, obj):
        return f"${obj.balance_usd_cents / 100:.2f}"
    balance_usd.short_description = "Balance (USD)"

@admin.register(OrganisationWalletTransaction)
class OrganisationWalletTransactionAdmin(admin.ModelAdmin):
    list_display = ("wallet", "transaction_type", "amount_usd", "created_at")
    list_filter = ("transaction_type",)
    search_fields = ("wallet__organisation__name", "description")

    def amount_usd(self, obj):
        return f"${obj.amount_cents / 100:.2f}"
    amount_usd.short_description = "Amount (USD)"

@admin.register(OrganisationPointAccount)
class OrganisationPointAccountAdmin(admin.ModelAdmin):
    list_display = ("organisation", "balance", "created_at")
    search_fields = ("organisation__name",)

@admin.register(ProductPointAccount)
class ProductPointAccountAdmin(admin.ModelAdmin):
    list_display = ("product", "balance", "created_at")
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

class CartLineItemInline(admin.TabularInline):
    model = CartLineItem
    extra = 0
    readonly_fields = ("total_price_cents", "total_price_points")

@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ("person", "organisation", "status", "created_at", "total_amount", "country")
    inlines = [CartLineItemInline]

    def total_amount(self, obj):
        return f"${obj.total_amount:.2f}"
    total_amount.short_description = "Total Amount"

@admin.register(CartLineItem)
class CartLineItemAdmin(admin.ModelAdmin):
    list_display = ("cart", "item_type", "quantity", "unit_price_usd", "unit_price_points", "bounty")
    list_filter = ("item_type",)
    search_fields = ("cart__id", "bounty__title")

    def unit_price_usd(self, obj):
        return f"${obj.unit_price_cents / 100:.2f}"
    unit_price_usd.short_description = "Unit Price (USD)"

class SalesOrderLineItemInline(admin.TabularInline):
    model = SalesOrderLineItem
    extra = 0
    readonly_fields = ("total_price_cents",)

@admin.register(SalesOrder)
class SalesOrderAdmin(admin.ModelAdmin):
    list_display = ("id", "cart", "status", "total_usd", "created_at")
    list_filter = ("status",)
    search_fields = ("id", "cart__id")
    readonly_fields = ("total_usd_cents_including_fees_and_taxes",)
    inlines = [SalesOrderLineItemInline]

    def total_usd(self, obj):
        return f"${obj.total_usd_cents_including_fees_and_taxes / 100:.2f}"
    total_usd.short_description = "Total USD"

@admin.register(SalesOrderLineItem)
class SalesOrderLineItemAdmin(admin.ModelAdmin):
    list_display = ("sales_order", "item_type", "quantity", "unit_price_usd", "total_price_usd", "bounty")
    list_filter = ("item_type",)
    search_fields = ("sales_order__id", "bounty__title")

    def unit_price_usd(self, obj):
        return f"${obj.unit_price_cents / 100:.2f}"
    unit_price_usd.short_description = "Unit Price (USD)"

    def total_price_usd(self, obj):
        return f"${obj.total_price_cents / 100:.2f}"
    total_price_usd.short_description = "Total Price (USD)"

@admin.register(PointOrder)
class PointOrderAdmin(admin.ModelAdmin):
    list_display = ("id", "cart", "product_account", "total_points", "status", "created_at", "parent_order")
    list_filter = ("status",)
    search_fields = ("id", "cart__id", "product_account__product__name")

    def total_points(self, obj):
        return f"{obj.total_points:,}"
    total_points.short_description = "Total Points"
