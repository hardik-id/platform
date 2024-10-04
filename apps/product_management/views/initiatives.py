from django.views.generic import ListView, DetailView, CreateView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse
from django.db.models import Sum, Q

from ..models import Initiative, Product, Challenge, Bounty
from ..forms import InitiativeForm
from .. import utils

class InitiativeListView(ListView):
    model = Initiative
    context_object_name = "initiatives"
    template_name = "product_management/initiatives.html"
    paginate_by = 10

    def get_queryset(self):
        return Initiative.objects.all().order_by('-created_at')

class ProductInitiativesView(utils.BaseProductDetailView, ListView):
    template_name = "product_management/product_initiatives.html"
    context_object_name = "initiatives"

    def get_queryset(self):
        product = self.get_context_data()['product']
        return Initiative.objects.filter(product=product).annotate(
            total_points=Sum(
                'challenge__bounty__reward_amount',
                filter=Q(challenge__bounty__status=Bounty.BountyStatus.AVAILABLE) &
                      Q(challenge__bounty__reward_type=Bounty.RewardType.POINTS)
            )
        )

class InitiativeDetailView(utils.BaseProductDetailView, DetailView):
    template_name = "product_management/initiative_detail.html"
    model = Initiative
    context_object_name = "initiative"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["challenges"] = Challenge.objects.filter(
            initiative=self.object, 
            status=Challenge.ChallengeStatus.ACTIVE
        )
        context["bounty_status"] = Bounty.BountyStatus
        return context

class CreateInitiativeView(LoginRequiredMixin, utils.BaseProductDetailView, CreateView):
    form_class = InitiativeForm
    template_name = "product_management/create_initiative.html"
    login_url = "sign_in"

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["slug"] = self.kwargs.get("product_slug")
        return kwargs

    def get_success_url(self):
        return reverse(
            "product_initiatives",
            args=(self.kwargs.get("product_slug"),),
        )

    def form_valid(self, form):
        product = Product.objects.get(slug=self.kwargs.get("product_slug"))
        form.instance.product = product
        return super().form_valid(form)

class UpdateInitiativeView(LoginRequiredMixin, utils.BaseProductDetailView, UpdateView):
    model = Initiative
    form_class = InitiativeForm
    template_name = "product_management/update_initiative.html"
    login_url = "sign_in"

    def get_success_url(self):
        return reverse(
            "initiative_detail",
            args=(self.object.product.slug, self.object.pk),
        )

    def form_valid(self, form):
        # You might want to add some checks here, e.g., if the user has permission to update
        return super().form_valid(form)