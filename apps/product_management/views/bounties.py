from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.http import JsonResponse, HttpResponseRedirect
from django.db import models
from django.contrib import messages

from ..models import Bounty, Challenge, Product
from ..forms import BountyForm, BountyClaimForm
from .. import utils
from apps.talent.utils import serialize_skills
from apps.talent.models import Skill, Expertise, BountyClaim
from apps.talent.forms import PersonSkillFormSet

class BountyListView(ListView):
    model = Bounty
    context_object_name = "bounties"
    template_name = "product_management/bounty/list.html"
    paginate_by = 51

    def get_template_names(self):
        if self.request.htmx:
            return ["product_management/bounty/partials/list_partials.html"]
        return ["product_management/bounty/list.html"]

    def get_queryset(self):
        filters = ~models.Q(challenge__status=Challenge.ChallengeStatus.DRAFT)

        if expertise := self.request.GET.get("expertise"):
            filters &= models.Q(expertise=expertise)

        if status := self.request.GET.get("status"):
            filters &= models.Q(status=status)

        if skill := self.request.GET.get("skill"):
            filters &= models.Q(skill=skill)
        return Bounty.objects.filter(filters).select_related("challenge", "skill").prefetch_related("expertise")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["BountyStatus"] = Bounty.BountyStatus

        expertises = []
        if skill := self.request.GET.get("skill"):
            expertises = Expertise.get_roots().filter(skill=skill)

        context["skills"] = [serialize_skills(skill) for skill in Skill.get_roots()]
        context["expertises"] = [utils.serialize_other_type_tree(expertise) for expertise in expertises]
        return context

    def render_to_response(self, context, **response_kwargs):
        if self.request.htmx and self.request.GET.get("target") == "skill":
            list_html = render(
                self.request,
                "product_management/bounty/partials/list_partials.html",
                context,
            ).content.decode('utf-8')
            expertise_html = render(
                self.request,
                "product_management/bounty/partials/expertise.html",
                context,
            ).content.decode('utf-8')

            return JsonResponse(
                {
                    "list_html": list_html,
                    "expertise_html": expertise_html,
                    "item_found_count": context["object_list"].count(),
                }
            )
        return super().render_to_response(context, **response_kwargs)

class ProductBountyListView(utils.BaseProductDetailView, ListView):
    model = Bounty
    context_object_name = "bounties"
    template_name = "product_management/product_bounties.html"

    def get_queryset(self):
        product = self.get_context_data().get("product")
        return Bounty.objects.filter(challenge__product=product).exclude(
            challenge__status=Challenge.ChallengeStatus.DRAFT
        )

class BountyDetailView(utils.BaseProductDetailView, DetailView):
    model = Bounty
    template_name = "product_management/bounty_detail.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        bounty = self.object
        user = self.request.user
        
        context.update({
            "product": bounty.challenge.product,
            "challenge": bounty.challenge,
            "claimed_by": bounty.claimed_by,
            "show_actions": False,
            "can_be_claimed": False,
            "can_be_modified": False,
            "is_product_admin": False,
            "created_bounty_claim_request": False,
            "bounty_claim": None,
        })

        if user.is_authenticated:
            person = user.person
            bounty_claim = bounty.bountyclaim_set.filter(person=person).first()

            context["can_be_modified"] = utils.has_product_modify_permission(user, context["product"])

            if bounty.status == Bounty.BountyStatus.AVAILABLE:
                context["can_be_claimed"] = not bounty_claim

            if bounty_claim and bounty_claim.status == BountyClaim.Status.REQUESTED and not bounty.claimed_by:
                context["created_bounty_claim_request"] = True
                context["bounty_claim"] = bounty_claim

        context["show_actions"] = any([
            context["can_be_claimed"],
            context["can_be_modified"],
            context["created_bounty_claim_request"]
        ])

        return context

class CreateBountyView(LoginRequiredMixin, utils.BaseProductDetailView, CreateView):
    model = Bounty
    form_class = BountyForm
    template_name = "product_management/create_bounty.html"

    def get_success_url(self):
        return reverse("challenge_detail", args=(self.object.challenge.product.slug, self.object.challenge.pk))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["challenge"] = Challenge.objects.get(pk=self.kwargs.get("challenge_id"))
        context["skills"] = [serialize_skills(skill) for skill in Skill.get_roots()]
        context["empty_form"] = PersonSkillFormSet().empty_form
        return context

    def form_valid(self, form):
        form.instance.challenge = Challenge.objects.get(pk=self.kwargs.get("challenge_id"))
        form.instance.skill = Skill.objects.get(id=form.cleaned_data.get("skill"))
        response = super().form_valid(form)
        if form.cleaned_data.get("expertise_ids"):
            form.instance.expertise.add(
                *Expertise.objects.filter(id__in=form.cleaned_data.get("expertise_ids").split(","))
            )
        return response

class UpdateBountyView(LoginRequiredMixin, utils.BaseProductDetailView, UpdateView):
    model = Bounty
    form_class = BountyForm
    template_name = "product_management/update_bounty.html"

    def get_success_url(self):
        return reverse("challenge_detail", args=(self.object.challenge.product.slug, self.object.challenge.pk))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["challenge"] = self.object.challenge
        context["skills"] = [serialize_skills(skill) for skill in Skill.get_roots()]
        context["empty_form"] = PersonSkillFormSet().empty_form
        return context

    def form_valid(self, form):
        form.instance.skill = Skill.objects.get(id=form.cleaned_data.get("skill"))
        response = super().form_valid(form)
        if form.cleaned_data.get("expertise_ids"):
            form.instance.expertise.set(
                Expertise.objects.filter(id__in=form.cleaned_data.get("expertise_ids").split(","))
            )
        return response

class DeleteBountyView(LoginRequiredMixin, DeleteView):
    model = Bounty
    
    def get_success_url(self):
        return reverse("challenge_detail", args=(self.object.challenge.product.slug, self.object.challenge.pk))

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        success_url = self.get_success_url()
        self.object.delete()
        messages.success(request, "The bounty has been successfully deleted.")
        return HttpResponseRedirect(success_url)

class BountyClaimView(LoginRequiredMixin, CreateView):
    form_class = BountyClaimForm

    def post(self, request, pk, *args, **kwargs):
        form = self.form_class(request.POST)
        if not form.is_valid():
            return JsonResponse({"errors": form.errors}, status=400)

        bounty = get_object_or_404(Bounty, pk=pk)
        instance = form.save(commit=False)
        instance.bounty = bounty
        instance.person = request.user.person
        instance.status = BountyClaim.Status.REQUESTED
        instance.save()

        return render(
            request,
            "product_management/partials/buttons/delete_bounty_claim_button.html",
            context={"bounty_claim": instance},
        )

def bounty_claim_actions(request, pk):
    instance = get_object_or_404(BountyClaim, pk=pk)
    action_type = request.GET.get("action")
    
    if action_type == "accept":
        instance.status = BountyClaim.Status.GRANTED
        BountyClaim.objects.filter(bounty__challenge=instance.bounty.challenge).exclude(pk=pk).update(status=BountyClaim.Status.REJECTED)
    elif action_type == "reject":
        instance.status = BountyClaim.Status.REJECTED
    else:
        return JsonResponse({"error": "Invalid action"}, status=400)

    instance.save()
    return redirect(reverse("dashboard-product-bounties", args=(instance.bounty.challenge.product.slug,)))

class DeleteBountyClaimView(LoginRequiredMixin, DeleteView):
    model = BountyClaim
    success_url = reverse_lazy("dashboard-bounty-requests")

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        if self.object.status == BountyClaim.Status.REQUESTED:
            self.object.status = BountyClaim.Status.CANCELLED
            self.object.save()
            messages.success(request, "The bounty claim has been successfully cancelled.")
        else:
            messages.error(request, "Only active claims can be cancelled.")

        if request.htmx:
            return render(
                request,
                "product_management/partials/buttons/create_bounty_claim_button.html",
                {"bounty": self.object.bounty},
            )

        return HttpResponseRedirect(self.get_success_url())

class DashboardProductBountiesView(LoginRequiredMixin, ListView):
    model = BountyClaim
    context_object_name = "bounty_claims"
    template_name = "product_management/dashboard/manage_bounties.html"

    def get_queryset(self):
        product_slug = self.kwargs.get("product_slug")
        product = get_object_or_404(Product, slug=product_slug)
        return BountyClaim.objects.filter(
            bounty__challenge__product=product,
            status=BountyClaim.Status.REQUESTED,
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["product"] = get_object_or_404(Product, slug=self.kwargs.get("product_slug"))
        return context

class DashboardProductBountyFilterView(LoginRequiredMixin, ListView):
    model = Bounty
    template_name = "product_management/dashboard/bounty_table.html"
    context_object_name = "bounties"

    def get_queryset(self):
        product = get_object_or_404(Product, slug=self.kwargs.get("product_slug"))
        queryset = Bounty.objects.filter(challenge__product=product)

        if query_parameter := self.request.GET.get("q"):
            for q in query_parameter.split(" "):
                key, value = q.split(":")
                if key == "sort":
                    if value == "reward-asc":
                        queryset = queryset.order_by("reward_amount")
                    elif value == "reward-desc":
                        queryset = queryset.order_by("-reward_amount")

        if search_query := self.request.GET.get("search-bounty"):
            queryset = queryset.filter(challenge__title__icontains=search_query)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["product"] = get_object_or_404(Product, slug=self.kwargs.get("product_slug"))
        return context