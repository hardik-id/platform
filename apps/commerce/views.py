from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.generic import ListView, DetailView
from django.utils.decorators import method_decorator
from django.db import transaction
from django.http import JsonResponse

from .models import BountyCart, BountyCartItem, Organisation, OrganisationPointAccount, PointTransaction
from apps.product_management.models import Bounty

@login_required
def create_or_get_cart(request):
    cart, created = BountyCart.objects.get_or_create(
        user=request.user,
        status=BountyCart.BountyCartStatus.CREATED
    )
    return cart

@login_required
def add_to_cart(request, bounty_id):
    bounty = get_object_or_404(Bounty, id=bounty_id)
    cart = create_or_get_cart(request)
    
    try:
        if bounty.reward_type == Bounty.RewardType.POINTS:
            BountyCartItem.objects.create(
                cart=cart,
                bounty=bounty,
                points=bounty.reward_amount
            )
        else:  # USD
            BountyCartItem.objects.create(
                cart=cart,
                bounty=bounty,
                usd_amount=bounty.reward_amount
            )
        messages.success(request, f"{bounty.title} added to cart.")
    except Exception as e:
        messages.error(request, f"Error adding {bounty.title} to cart: {str(e)}")
    
    return redirect('view_cart')

@login_required
def remove_from_cart(request, item_id):
    item = get_object_or_404(BountyCartItem, id=item_id, cart__user=request.user)
    item.delete()
    messages.success(request, "Item removed from cart.")
    return redirect('view_cart')

@method_decorator(login_required, name='dispatch')
class CartView(DetailView):
    model = BountyCart
    template_name = 'commerce/cart.html'
    context_object_name = 'cart'

    def get_object(self):
        return create_or_get_cart(self.request)

@login_required
def process_cart(request):
    cart = get_object_or_404(BountyCart, user=request.user, status=BountyCart.BountyCartStatus.CREATED)
    
    try:
        with transaction.atomic():
            if cart.process_cart():
                messages.success(request, "Cart processed successfully.")
                return redirect('cart_success')
            else:
                messages.error(request, "Failed to process cart. Please check your points balance or payment method.")
    except Exception as e:
        messages.error(request, f"An error occurred while processing your cart: {str(e)}")
    
    return redirect('view_cart')

@login_required
def cart_success(request):
    return render(request, 'commerce/cart_success.html')

@method_decorator(login_required, name='dispatch')
class OrganisationPointAccountView(DetailView):
    model = OrganisationPointAccount
    template_name = 'commerce/point_account.html'
    context_object_name = 'point_account'

    def get_object(self):
        return get_object_or_404(OrganisationPointAccount, organisation__user=self.request.user)

@login_required
def grant_points(request):
    if request.method == 'POST' and request.user.is_staff:
        organisation_id = request.POST.get('organisation_id')
        amount = int(request.POST.get('amount', 0))
        description = request.POST.get('description', '')
        
        organisation = get_object_or_404(Organisation, id=organisation_id)
        point_account, created = OrganisationPointAccount.objects.get_or_create(organisation=organisation)
        
        point_account.add_points(amount)
        PointTransaction.objects.create(
            account=point_account,
            amount=amount,
            transaction_type='GRANT',
            description=description
        )
        
        messages.success(request, f"{amount} points granted to {organisation.name}")
        return redirect('organisation_point_account', pk=point_account.pk)
    
    return JsonResponse({'error': 'Invalid request'}, status=400)

@method_decorator(login_required, name='dispatch')
class PointTransactionListView(ListView):
    model = PointTransaction
    template_name = 'commerce/point_transactions.html'
    context_object_name = 'transactions'
    paginate_by = 20

    def get_queryset(self):
        return PointTransaction.objects.filter(account__organisation__user=self.request.user).order_by('-created_at')