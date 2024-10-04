from django.views.generic import CreateView, UpdateView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render, redirect
from django.urls import reverse
from django.http import JsonResponse

from ..models import ProductArea, Product, Challenge
from ..forms import ProductAreaForm
from .. import utils

class ProductTreeInteractiveView(utils.BaseProductDetailView):
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

class ProductAreaCreateView(utils.BaseProductDetailView, CreateView):
    model = ProductArea
    form_class = ProductAreaForm
    template_name = "product_tree/components/partials/create_node_partial.html"

    def get_template_names(self):
        if self.request.method == "POST":
            return ["product_tree/components/partials/add_node_partial.html"]
        elif not self.request.GET.get("parent_id"):
            return ["product_tree/components/partials/create_root_node_partial.html"]
        else:
            return super().get_template_names()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["can_modify_product"] = utils.has_product_modify_permission(self.request.user, context["product"])
        if self.request.method == "GET":
            context["id"] = str(uuid.uuid4())[:8]
            context["parent_id"] = self.request.GET.get("parent_id")
        context["depth"] = self.request.GET.get("depth", 0)
        context["product_slug"] = self.kwargs.get("product_slug")
        return context

    def form_valid(self, form):
        context = self.get_context_data()
        try:
            parent = ProductArea.objects.get(pk=self.request.POST.get("parent_id"))
            new_node = parent.add_child(**form.cleaned_data)
        except ProductArea.DoesNotExist:
            new_node = ProductArea.add_root(**form.cleaned_data)

        context["product_area"] = new_node
        context["node"] = [utils.serialize_tree(new_node)]
        context["depth"] = int(self.request.POST.get("depth", 0))
        return render(self.request, self.get_template_names(), context)

class ProductAreaUpdateView(utils.BaseProductDetailView, UpdateView):
    template_name = "product_management/product_area_detail.html"
    model = ProductArea
    form_class = ProductAreaForm

    def get_success_url(self):
        return reverse("product_tree", args=(self.get_context_data()["product"].slug,))

    def get_template_names(self):
        if self.request.htmx:
            return "product_tree/components/partials/update_node_partial.html"
        else:
            return super().get_template_names()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        product = Product.objects.get(slug=self.kwargs.get("product_slug"))
        product_perm = utils.has_product_modify_permission(self.request.user, product)
        product_area = self.object
        challenges = Challenge.objects.filter(product_area=product_area)

        form = self.form_class(instance=product_area, can_modify_product=product_perm)
        context.update({
            "product": product,
            "product_slug": product.slug,
            "can_modify_product": product_perm,
            "form": form,
            "challenges": challenges,
            "product_area": product_area,
            "margin_left": int(self.request.GET.get("margin_left", 0)) + 4,
            "depth": int(self.request.GET.get("depth", 0)),
        })
        return context

    def form_valid(self, form):
        if not self.request.htmx:
            return super().form_valid(form)
        self.object = form.save()
        context = self.get_context_data()
        return JsonResponse({
            "node_html": render(self.request, "product_tree/components/partials/node.html", context).content.decode('utf-8'),
            "form_html": render(self.request, "product_tree/components/partials/update_form.html", context).content.decode('utf-8')
        })

class ProductAreaDetailView(utils.BaseProductDetailView, DetailView):
    template_name = "product_management/product_area_detail.html"
    model = ProductArea
    context_object_name = "product_area"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["children"] = utils.serialize_tree(self.get_object())["children"]
        context["challenges"] = Challenge.objects.filter(product_area=self.object)
        return context

class CreateCapabilityView(LoginRequiredMixin, utils.BaseProductDetailView, CreateView):
    form_class = ProductAreaForm
    template_name = "product_management/create_capability.html"
    login_url = "sign_in"

    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST)
        if form.is_valid():
            name = form.cleaned_data.get("name")
            description = form.cleaned_data.get("description")
            capability = form.cleaned_data.get("root")
            creation_method = form.cleaned_data.get("creation_method")
            product = Product.objects.get(slug=kwargs.get("product_slug"))
            
            if capability is None or creation_method == "1":
                root = ProductArea.add_root(name=name, description=description)
                root.product.add(product)
            elif creation_method == "2":
                sibling = ProductArea.add_sibling(name=name, description=description)
                sibling.product.add(product)
            elif creation_method == "3":
                child = capability.add_child(name=name, description=description)
                child.product.add(product)

            return redirect(reverse("product_tree", args=(kwargs.get("product_slug"),)))

        return super().post(request, *args, **kwargs)