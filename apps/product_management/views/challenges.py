from django.views.generic import DetailView, CreateView, UpdateView, DeleteView, ListView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from django.http import HttpResponseRedirect
from django.contrib import messages
from django.db.models import Sum, Case, When, Value, IntegerField

from ..models import Challenge, Product, Initiative, Bounty
from ..forms import ChallengeForm
from .. import utils
from apps.talent.forms import PersonSkillFormSet
from apps.talent.models import BountyClaim
from apps.security.models import ProductRoleAssignment

class ChallengeListView(ListView):
    model = Challenge
    context_object_name = "challenges"
    template_name = "product_management/challenges.html"
    paginate_by = 10

    def get_queryset(self):
        queryset = super().get_queryset()
        return queryset.exclude(status=Challenge.ChallengeStatus.DRAFT)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["challenge_status"] = Challenge.ChallengeStatus
        return context

class ProductChallengesView(utils.BaseProductDetailView, ListView):
    template_name = "product_management/product_challenges.html"
    context_object_name = "challenges"

    def get_queryset(self):
        product = self.get_context_data()["product"]
        return Challenge.objects.filter(product=product).annotate(
            custom_order=Case(
                When(status=Challenge.ChallengeStatus.ACTIVE, then=Value(0)),
                When(status=Challenge.ChallengeStatus.BLOCKED, then=Value(1)),
                When(status=Challenge.ChallengeStatus.COMPLETED, then=Value(2)),
                When(status=Challenge.ChallengeStatus.CANCELLED, then=Value(3)),
                default=Value(4),
                output_field=IntegerField(),
            )
        ).order_by("custom_order")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["challenge_status"] = Challenge.ChallengeStatus
        return context

class ChallengeDetailView(utils.BaseProductDetailView, DetailView):
    model = Challenge
    context_object_name = "challenge"
    template_name = "product_management/challenge_detail.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        challenge = self.object
        user = self.request.user

        context["BountyStatus"] = Bounty.BountyStatus
        context["bounties"] = challenge.bounty_set.all()
        context["total_reward"] = challenge.get_total_reward()
        context["does_have_permission"] = utils.has_product_modify_permission(user, context.get("product"))

        if user.is_authenticated:
            person = user.person
            context["agreement_status"] = person.contributor_agreement.filter(
                agreement_template__product=challenge.product
            ).exists()
            context["agreement_template"] = challenge.product.contributor_agreement_templates.first()

        return context

class CreateChallengeView(LoginRequiredMixin, utils.BaseProductDetailView, CreateView):
    model = Challenge
    form_class = ChallengeForm
    template_name = "product_management/create_challenge.html"
    login_url = "sign_in"

    def get_success_url(self):
        return reverse("challenge_detail", args=(self.object.product.slug, self.object.id))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        product = get_object_or_404(Product, slug=self.kwargs.get("product_slug"))
        context["product"] = product
        context["empty_form"] = PersonSkillFormSet().empty_form
        return context

    def form_valid(self, form):
        form.instance.product = get_object_or_404(Product, slug=self.kwargs.get("product_slug"))
        form.instance.created_by = self.request.user.person
        return super().form_valid(form)

class UpdateChallengeView(LoginRequiredMixin, utils.BaseProductDetailView, UpdateView):
    model = Challenge
    form_class = ChallengeForm
    template_name = "product_management/update_challenge.html"
    login_url = "sign_in"

    def get_success_url(self):
        return reverse("challenge_detail", args=(self.object.product.slug, self.object.id))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["product"] = self.object.product
        return context

    def form_valid(self, form):
        form.instance.updated_by = self.request.user.person
        return super().form_valid(form)

class DeleteChallengeView(LoginRequiredMixin, DeleteView):
    model = Challenge
    template_name = "product_management/delete_challenge.html"
    login_url = "sign_in"

    def get_success_url(self):
        return reverse("product_challenges", args=[self.object.product.slug])

    def dispatch(self, request, *args, **kwargs):
        challenge = self.get_object()
        person = request.user.person
        if challenge.can_delete_challenge(person) or challenge.created_by == person:
            return super().dispatch(request, *args, **kwargs)
        messages.error(request, "You do not have rights to remove this challenge.")
        return redirect("challenge_detail", product_slug=challenge.product.slug, pk=challenge.pk)

    def delete(self, request, *args, **kwargs):
        messages.success(request, "The challenge has been successfully deleted!")
        return super().delete(request, *args, **kwargs)

def redirect_challenge_to_bounties(request):
    return redirect(reverse("bounties"))