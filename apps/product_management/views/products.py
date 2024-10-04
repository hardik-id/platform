from django.views.generic import ListView, DetailView, CreateView, UpdateView, RedirectView, TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from django.contrib.contenttypes.models import ContentType
from django.db import models

from ..models import Product, Challenge, ProductArea, Initiative, Idea, Bug, Bounty
from ..forms import ProductForm, OrganisationForm
from .. import utils
from apps.commerce.models import Organisation
from apps.security.models import ProductRoleAssignment
from apps.common import mixins as common_mixins

class ProductListView(ListView):
    model = Product
    context_object_name = "products"
    queryset = Product.objects.filter(is_private=False).order_by("created_at")
    template_name = "product_management/products.html"
    paginate_by = 8

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["challenge_status"] = Challenge.ChallengeStatus
        return context

class ProductRedirectView(utils.BaseProductDetailView, RedirectView):
    def get(self, request, *args, **kwargs):
        return redirect(reverse("product_summary", kwargs=kwargs))

class ProductSummaryView(utils.BaseProductDetailView, TemplateView):
    template_name = "product_management/product_summary.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        product = context["product"]
        challenges = Challenge.objects.filter(product=product, status=Challenge.ChallengeStatus.ACTIVE)

        context["can_modify_product"] = utils.has_product_modify_permission(self.request.user, product)
        context["challenges"] = challenges
        context["point_balance"] = product.point_balance

        product_tree = product.product_trees.first()
        if product_tree:
            product_areas = ProductArea.get_root_nodes().filter(product_tree=product_tree)
            context["tree_data"] = [utils.serialize_tree(node) for node in product_areas]
        else:
            context["tree_data"] = []

        return context

class CreateProductView(LoginRequiredMixin, common_mixins.AttachmentMixin, CreateView):
    model = Product
    form_class = ProductForm
    template_name = "product_management/create_product.html"
    login_url = "sign_in"

    def get_success_url(self):
        return reverse("product_summary", args=(self.object.slug,))

    def form_valid(self, form):
        response = super().form_valid(form)
        if not self.request.htmx:
            ProductRoleAssignment.objects.create(
                person=self.request.user.person,
                product=form.instance,
                role=ProductRoleAssignment.ProductRoles.ADMIN,
            )
        return response

class UpdateProductView(LoginRequiredMixin, common_mixins.AttachmentMixin, UpdateView):
    model = Product
    form_class = ProductForm
    template_name = "product_management/update_product.html"
    login_url = "sign_in"

    def get_success_url(self):
        return reverse("update-product", args=(self.object.id,))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        initial = {}
        if self.object.content_type_id == ContentType.objects.get_for_model(self.request.user.person).id:
            initial_make_me_owner = self.object.object_id == self.request.user.id
            initial = {"make_me_owner": initial_make_me_owner}
            context["make_me_owner"] = initial_make_me_owner

        if self.object.content_type_id == ContentType.objects.get_for_model(Organisation).id:
            initial_organisation = Organisation.objects.filter(id=self.object.object_id).first()
            initial = {"organisation": initial_organisation}
            context["organisation"] = initial_organisation

        context["form"] = self.form_class(instance=self.object, initial=initial)
        context["product_instance"] = self.object
        return context

    def form_valid(self, form):
        return super().form_save(form)

class CreateOrganisationView(LoginRequiredMixin, CreateView):
    model = Organisation
    form_class = OrganisationForm
    template_name = "product_management/create_organisation.html"
    success_url = reverse_lazy("create-product")
    login_url = "sign_in"

    def post(self, request, *args, **kwargs):
        if self._is_htmx_request(self.request):
            return super().post(request, *args, **kwargs)

        form = self.form_class(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect(self.success_url)

        return super().post(request, *args, **kwargs)

class ProductIdeasAndBugsView(utils.BaseProductDetailView, TemplateView):
    template_name = "product_management/product_ideas_and_bugs.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        product = context["product"]
        user = self.request.user

        ideas = Idea.objects.filter(product=product)
        if user.is_authenticated:
            ideas_with_votes = [
                {
                    "idea_obj": idea,
                    "num_votes": idea.ideavote_set.count(),
                    "user_has_voted": idea.ideavote_set.filter(voter=user).exists(),
                }
                for idea in ideas
            ]
        else:
            ideas_with_votes = [{"idea_obj": idea} for idea in ideas]

        context.update({
            "ideas": ideas_with_votes,
            "bugs": Bug.objects.filter(product=product),
        })

        return context

class ProductTreeInteractiveView(utils.BaseProductDetailView, TemplateView):
    template_name = "product_management/product_tree.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        product = context["product"]
        
        context["can_modify_product"] = utils.has_product_modify_permission(self.request.user, product)
        
        product_tree = product.product_trees.first()
        if product_tree:
            product_areas = ProductArea.get_root_nodes().filter(product_tree=product_tree)
            context["tree_data"] = [utils.serialize_tree(node) for node in product_areas]
        else:
            context["tree_data"] = []
        
        return context

class ProductInitiativesView(utils.BaseProductDetailView, TemplateView):
    template_name = "product_management/product_initiatives.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        initiatives = Initiative.objects.filter(product=context["product"]).annotate(
            total_points=models.Sum(
                "challenge__bounty__reward_amount",
                filter=models.Q(challenge__bounty__status=Bounty.BountyStatus.AVAILABLE)
                & models.Q(challenge__bounty__reward_type=Bounty.RewardType.POINTS),
            )
        )
        context["initiatives"] = initiatives
        return context

class ProductSettingView(LoginRequiredMixin, common_mixins.AttachmentMixin, UpdateView):
    model = Product
    form_class = ProductForm
    template_name = "product_management/dashboard/product_setting.html"
    login_url = "sign_in"

    def get_success_url(self):
        return reverse("product-setting", args=(self.object.id,))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        initial = {}
        if self.object.content_type_id == ContentType.objects.get_for_model(self.request.user.person).id:
            initial_make_me_owner = self.object.object_id == self.request.user.id
            initial = {"make_me_owner": initial_make_me_owner}
            context["make_me_owner"] = initial_make_me_owner

        if self.object.content_type_id == ContentType.objects.get_for_model(Organisation).id:
            initial_organisation = Organisation.objects.filter(id=self.object.object_id).first()
            initial = {"organisation": initial_organisation}
            context["organisation"] = initial_organisation

        context["form"] = self.form_class(instance=self.object, initial=initial)
        context["product_instance"] = self.object
        return context

    def form_valid(self, form):
        return super().form_save(form)
    
class ProductRoleAssignmentView(utils.BaseProductDetailView, TemplateView):
    template_name = "product_management/product_people.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        product = context["product"]

        context.update(
            {
                "product_people": ProductRoleAssignment.objects.filter(product=product),
            }
        )

        return context