from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html
from .models import (
    Organisation,
    OrganisationPointAccount,
    ProductPointAccount,
    PointTransaction,
    OrganisationPointGrant,
    PlatformFeeConfiguration,
    PlatformFee,
    BountyCart,
    BountyCartItem,
    SalesOrder,
    PointOrder
)

@admin.register(Organisation)
class OrganisationAdmin(admin.ModelAdmin):
    list_display = ('name', 'country', 'tax_id')
    search_fields = ('name', 'country', 'tax_id')

class PointTransactionInline(admin.TabularInline):
    model = PointTransaction
    extra = 0
    fields = ('amount', 'transaction_type', 'created_at')
    readonly_fields = ('created_at',)

@admin.register(OrganisationPointAccount)
class OrganisationPointAccountAdmin(admin.ModelAdmin):
    list_display = ('organisation', 'balance')
    search_fields = ('organisation__name',)
    inlines = [PointTransactionInline]

@admin.register(ProductPointAccount)
class ProductPointAccountAdmin(admin.ModelAdmin):
    list_display = ('product', 'balance')
    search_fields = ('product__name',)
    inlines = [PointTransactionInline]

@admin.register(PointTransaction)
class PointTransactionAdmin(admin.ModelAdmin):
    list_display = ('account', 'product_account', 'amount', 'transaction_type', 'created_at')
    list_filter = ('transaction_type',)
    search_fields = ('account__organisation__name', 'product_account__product__name', 'description')

@admin.register(OrganisationPointGrant)
class OrganisationPointGrantAdmin(admin.ModelAdmin):
    list_display = ('organisation', 'amount', 'granted_by', 'created_at')
    search_fields = ('organisation__name', 'granted_by__username')

@admin.register(PlatformFeeConfiguration)
class PlatformFeeConfigurationAdmin(admin.ModelAdmin):
    list_display = ('percentage', 'applies_from_date')
    ordering = ('-applies_from_date',)

@admin.register(PlatformFee)
class PlatformFeeAdmin(admin.ModelAdmin):
    list_display = ('bounty_cart', 'amount', 'fee_rate')
    search_fields = ('bounty_cart__id',)

class BountyCartItemInline(admin.TabularInline):
    model = BountyCartItem
    extra = 0

@admin.register(BountyCart)
class BountyCartAdmin(admin.ModelAdmin):
    list_display = ('user', 'organisation', 'product', 'status', 'created_at')
    list_filter = ('status',)
    search_fields = ('user__username', 'organisation__name', 'product__name')
    inlines = [BountyCartItemInline]

@admin.register(BountyCartItem)
class BountyCartItemAdmin(admin.ModelAdmin):
    list_display = ('cart', 'bounty', 'funding_amount', 'funding_type')
    list_filter = ('funding_type',)
    search_fields = ('cart__id', 'bounty__title')

@admin.register(SalesOrder)
class SalesOrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'bounty_cart', 'status', 'total_usd', 'created_at')
    list_filter = ('status',)
    search_fields = ('id', 'bounty_cart__id')
    readonly_fields = ('total_usd_cents', 'platform_fee', 'tax_amount_cents')

    def total_usd(self, obj):
        return f"${obj.total_usd:.2f}"
    total_usd.short_description = 'Total USD'

@admin.register(PointOrder)
class PointOrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'product_account', 'bounty', 'amount', 'status', 'created_at')
    list_filter = ('status',)
    search_fields = ('id', 'product_account__product__name', 'bounty__title')