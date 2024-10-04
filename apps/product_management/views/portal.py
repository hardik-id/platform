from django.views.generic import TemplateView, ListView, DetailView, CreateView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import HttpResponse, HttpResponseRedirect, get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.db.models import Q

from ..models import Product, Challenge, Bounty, ProductContributorAgreementTemplate
from ..forms import ProductRoleAssignmentForm, ContributorAgreementTemplateForm
from .. import utils
from apps.talent.models import Person, BountyDeliveryAttempt, BountyClaim
from apps.common.mixins import PersonSearchMixin
from apps.security.models import ProductRoleAssignment
from apps.common import mixins as common_mixins

class PortalBaseView(LoginRequiredMixin):
    login_url = "sign_in"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        person = self.request.user.person
        photo_url = person.get_photo_url()
        product_queryset = Product.objects.filter(content_type__model="person", object_id=person.id)
        context.update({"person": person, "photo_url": photo_url, "products": product_queryset})
        return context

class PortalDashboardView(PortalBaseView, TemplateView):
    """
    This view represents the dashboard (home/landing screen) of the portal.
    """
    template_name = "product_management/portal/dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        person = context.get("person")
        active_bounty_claims = BountyClaim.objects.filter(person=person, status=BountyClaim.Status.GRANTED)
        product_roles_queryset = ProductRoleAssignment.objects.filter(person=person).exclude(
            role=ProductRoleAssignment.ProductRoles.CONTRIBUTOR
        )
        product_ids = product_roles_queryset.values_list("product_id", flat=True)
        products = Product.objects.filter(id__in=product_ids)
        context.update({"active_bounty_claims": active_bounty_claims, "products": products})

        slug = self.kwargs.get("product_slug", "")
        if Product.objects.filter(slug=slug).exists():
            context["product"] = Product.objects.get(slug=slug)

        context["default_tab"] = self.kwargs.get("default_tab", 0)
        return context

class ManageBountiesView(PortalBaseView, TemplateView):
    template_name = "product_management/portal/my_bounties.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        person = self.request.user.person
        queryset = BountyClaim.objects.filter(
            person=person,
            status__in=[BountyClaim.Status.GRANTED, BountyClaim.Status.REQUESTED],
        )
        context.update({"bounty_claims": queryset})
        return context

class ManageUsersView(PortalBaseView, TemplateView):
    template_name = "product_management/portal/manage_users.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        slug = self.kwargs.get("product_slug")
        product = Product.objects.get(slug=slug)
        product_users = ProductRoleAssignment.objects.filter(product=product).order_by("-role")
        context["product"] = product
        context["product_users"] = product_users
        return context

class AddProductUserView(PortalBaseView, PersonSearchMixin, CreateView):
    model = ProductRoleAssignment
    form_class = ProductRoleAssignmentForm
    template_name = "product_management/portal/add_product_user.html"

    def get_form_kwargs(self, *args, **kwargs):
        kwargs = super().get_form_kwargs(*args, **kwargs)
        if product_slug := self.kwargs.get("product_slug", None):
            kwargs.update(initial={"product": Product.objects.get(slug=product_slug)})
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if context["search_result"]:
            return context
        slug = self.kwargs.get("product_slug")
        product = Product.objects.get(slug=slug)
        product_users = ProductRoleAssignment.objects.filter(product=product).order_by("-role")
        context["product"] = product
        context["product_users"] = product_users
        return context

    def form_valid(self, form):
        product = Product.objects.get(slug=self.kwargs.get("product_slug"))
        form.instance.product = product
        return super().form_valid(form)

    def get_success_url(self):
        return reverse("manage-users", args=(self.kwargs.get("product_slug"),))

class UpdateProductUserView(PortalBaseView, PersonSearchMixin, UpdateView):
    model = ProductRoleAssignment
    form_class = ProductRoleAssignmentForm
    template_name = "product_management/portal/update_product_user.html"
    context_object_name = "product_role_assignment"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if context["search_result"]:
            return context
        slug = self.kwargs.get("product_slug")
        product = Product.objects.get(slug=slug)
        product_users = ProductRoleAssignment.objects.filter(product=product).order_by("-role")
        context["product"] = product
        context["product_users"] = product_users
        return context

    def get_success_url(self):
        return reverse("manage-users", args=(self.kwargs.get("product_slug"),))

class PortalProductDetailView(PortalBaseView, DetailView):
    model = Product
    template_name = "product_management/portal/product_detail.html"

    def get_object(self, queryset=None):
        slug = self.kwargs.get("product_slug")
        return get_object_or_404(self.model, slug=slug)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            "challenges": Challenge.objects.filter(product=self.object).order_by("-created_at"),
            "default_tab": self.kwargs.get("default_tab", 0),
        })
        return context

class BountyClaimRequestsView(LoginRequiredMixin, ListView):
    model = BountyClaim
    context_object_name = "bounty_claims"
    template_name = "product_management/portal/bounty_claim_requests.html"

    def get_queryset(self):
        person = self.request.user.person
        return BountyClaim.objects.filter(
            person=person,
            status__in=[BountyClaim.Status.GRANTED, BountyClaim.Status.REQUESTED],
        )

class ReviewWorkView(LoginRequiredMixin, ListView):
    model = BountyDeliveryAttempt
    context_object_name = "bounty_deliveries"
    queryset = BountyDeliveryAttempt.objects.filter(kind=BountyDeliveryAttempt.SubmissionType.NEW)
    template_name = "product_management/portal/review_work.html"

class ContributorAgreementTemplateListView(LoginRequiredMixin, ListView):
    model = ProductContributorAgreementTemplate
    context_object_name = "contributor_agreement_templates"
    template_name = "product_management/portal/contributor_agreement_templates.html"

    def get_queryset(self):
        product_slug = self.kwargs.get("product_slug")
        return ProductContributorAgreementTemplate.objects.filter(product__slug=product_slug).order_by("-created_at")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        slug = self.kwargs.get("product_slug")
        context.update({"product": Product.objects.get(slug=slug)})
        return context

class CreateContributorAgreementTemplateView(LoginRequiredMixin, CreateView):
    model = ProductContributorAgreementTemplate
    form_class = ContributorAgreementTemplateForm
    template_name = "product_management/portal/create_contributor_agreement_template.html"

    def get_form_kwargs(self, *args, **kwargs):
        kwargs = super().get_form_kwargs(*args, **kwargs)
        if product_slug := self.kwargs.get("product_slug", None):
            kwargs.update(initial={"product": Product.objects.get(slug=product_slug)})
        return kwargs

    def form_valid(self, form):
        form.instance.created_by = self.request.user.person
        return super().form_valid(form)

    def get_success_url(self):
        return reverse(
            "contributor-agreement-template-detail",
            args=(self.object.product.slug, self.object.id),
        )

class ContributorAgreementTemplateView(DetailView):
    model = ProductContributorAgreementTemplate
    template_name = "product_management/portal/contributor_agreement_template_detail.html"
    context_object_name = "contributor_agreement_template"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        slug = self.kwargs.get("product_slug")
        context.update({
            "product": Product.objects.get(slug=slug),
            "pk": self.object.pk,
        })
        return context

# Views moved from challenges.py
class DashboardProductChallengesView(LoginRequiredMixin, ListView):
    model = Challenge
    context_object_name = "challenges"
    template_name = "product_management/dashboard/manage_challenges.html"

    def get_queryset(self):
        product_slug = self.kwargs.get("product_slug")
        return Challenge.objects.filter(product__slug=product_slug).order_by("-created_at")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["product"] = get_object_or_404(Product, slug=self.kwargs.get("product_slug"))
        return context

class DashboardProductChallengeFilterView(LoginRequiredMixin, ListView):
    template_name = "product_management/dashboard/challenge_table.html"
    context_object_name = "challenges"

    def get_queryset(self):
        product = get_object_or_404(Product, slug=self.kwargs.get("product_slug"))
        queryset = Challenge.objects.filter(product=product)

        sort_param = self.request.GET.get("q", "")
        if "sort:created-asc" in sort_param:
            queryset = queryset.order_by("created_at")
        elif "sort:created-desc" in sort_param:
            queryset = queryset.order_by("-created_at")

        search_query = self.request.GET.get("search-challenge")
        if search_query:
            queryset = queryset.filter(title__icontains=search_query)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["product"] = get_object_or_404(Product, slug=self.kwargs.get("product_slug"))
        return context
    
class ProductChallengesManagementView(LoginRequiredMixin, ListView):
    model = Challenge
    context_object_name = "challenges"
    template_name = "product_management/portal/manage_challenges.html"

    def get_queryset(self):
        product_slug = self.kwargs.get("product_slug")
        return Challenge.objects.filter(product__slug=product_slug).order_by("-created_at")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["product"] = get_object_or_404(Product, slug=self.kwargs.get("product_slug"))
        return context

class ProductChallengeFilterView(LoginRequiredMixin, ListView):
    template_name = "product_management/portal/challenge_table.html"
    context_object_name = "challenges"

    def get_queryset(self):
        product = get_object_or_404(Product, slug=self.kwargs.get("product_slug"))
        queryset = Challenge.objects.filter(product=product)

        sort_param = self.request.GET.get("q", "")
        if "sort:created-asc" in sort_param:
            queryset = queryset.order_by("created_at")
        elif "sort:created-desc" in sort_param:
            queryset = queryset.order_by("-created_at")

        search_query = self.request.GET.get("search-challenge")
        if search_query:
            queryset = queryset.filter(title__icontains=search_query)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["product"] = get_object_or_404(Product, slug=self.kwargs.get("product_slug"))
        return context


class DashboardProductBountiesView(LoginRequiredMixin, ListView):
    model = Bounty
    context_object_name = "bounty_claims"
    template_name = "product_management/dashboard/manage_bounties.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data()

        slug = self.kwargs.get("product_slug")
        context.update({"product": Product.objects.get(slug=slug)})
        return context

    def get_queryset(self):
        product_slug = self.kwargs.get("product_slug")
        product = Product.objects.get(slug=product_slug)
        return BountyClaim.objects.filter(
            bounty__challenge__product=product,
            status=BountyClaim.Status.REQUESTED,
        )

def bounty_claim_actions(request, pk):
    instance = BountyClaim.objects.get(pk=pk)
    action_type = request.GET.get("action")
    if action_type == "accept":
        instance.status = BountyClaim.Status.GRANTED

        # If one claim is accepted for a particular challenge, the other claims automatically fails.
        challenge = instance.bounty.challenge
        _ = BountyClaim.objects.filter(bounty__challenge=challenge).update(status=BountyClaim.Status.REJECTED)
    elif action_type == "reject":
        instance.status = BountyClaim.Status.REJECTED
    else:
        raise BadRequest()

    instance.save()

    return redirect(reverse("dashboard-product-bounties", args=(instance.bounty.challenge.product.slug,)))


class DashboardProductBountyFilterView(LoginRequiredMixin, TemplateView):
    template_name = "product_management/dashboard/bounty_table.html"
    login_url = "sign_in"

    def get_context_data(self, **kwargs):
        context = super().get_context_data()

        slug = self.kwargs.get("product_slug")
        context.update({"product": Product.objects.get(slug=slug)})
        return context

    def get(self, request, *args, **kwargs):
        context = self.get_context_data()

        product = context.get("product")
        queryset = Bounty.objects.filter(challenge__product=product)

        if query_parameter := request.GET.get("q"):
            for q in query_parameter.split(" "):
                q = q.split(":")
                key = q[0]
                if key == "sort":
                    value = q[1]

                    if value == "points-asc":
                        queryset = queryset.order_by("points")
                    elif value == "points-desc":
                        queryset = queryset.order_by("-points")

        if query_parameter := request.GET.get("search-bounty"):
            queryset = Bounty.objects.filter(challenge__title__icontains=query_parameter)

        context.update({"bounties": queryset})

        return render(request, self.template_name, context)
    
class ProductSettingView(LoginRequiredMixin, common_mixins.AttachmentMixin, UpdateView):
    model = Product
    #form_class = forms.ProductForm
    template_name = "product_management/dashboard/product_setting.html"
    login_url = "sign_in"

    def get_success_url(self):
        return reverse("product-setting", args=(self.object.id,))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        initial = {}

        #context["form"] = self.form_class(instance=self.object, initial=initial)
        context["product_instance"] = self.object

        return context

    def form_valid(self, form):
        return super().form_save(form)

    def form_invalid(self, form):
        print(form.errors)
        return super().form_invalid(form)