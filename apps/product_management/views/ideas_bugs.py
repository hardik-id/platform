from django.views.generic import CreateView, DeleteView, DetailView, ListView, RedirectView, TemplateView, UpdateView

from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect, get_object_or_404
from django.urls import reverse
from django.http import HttpResponse
from django.db.models import Count


from ..models import Idea, Bug, Product, IdeaVote
from ..forms import IdeaForm, BugForm
from .. import utils

class ProductIdeasAndBugsView(utils.BaseProductDetailView, TemplateView):
    template_name = "product_management/product_ideas_and_bugs.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        product = context["product"]

        ideas_with_votes = []
        user = self.request.user

        if user.is_authenticated:
            for idea in Idea.objects.filter(product=product):
                num_votes = IdeaVote.objects.filter(idea=idea).count()
                user_has_voted = IdeaVote.objects.filter(voter=user, idea=idea).exists()
                ideas_with_votes.append(
                    {
                        "idea_obj": idea,
                        "num_votes": num_votes,
                        "user_has_voted": user_has_voted,
                    }
                )
        else:
            for idea in Idea.objects.filter(product=product):
                ideas_with_votes.append(
                    {
                        "idea_obj": idea,
                    }
                )

        context.update(
            {
                "ideas": ideas_with_votes,
                "bugs": Bug.objects.filter(product=product),
            }
        )

        return context

class ProductIdeaListView(utils.BaseProductDetailView, ListView):
    model = Idea
    template_name = "product_management/product_idea_list.html"
    context_object_name = "ideas"

    def get_queryset(self):
        product = self.get_context_data().get("product")
        return self.model.objects.filter(product=product).annotate(vote_count=Count('ideavote'))

class ProductBugListView(utils.BaseProductDetailView, ListView):
    model = Bug
    template_name = "product_management/product_bug_list.html"
    context_object_name = "bugs"

    def get_queryset(self):
        product = self.get_context_data().get("product")
        return self.model.objects.filter(product=product)

class CreateProductIdea(LoginRequiredMixin, utils.BaseProductDetailView, CreateView):
    template_name = "product_management/add_product_idea.html"
    form_class = IdeaForm

    def form_valid(self, form):
        form.instance.person = self.request.user.person
        form.instance.product = get_object_or_404(Product, slug=self.kwargs.get("product_slug"))
        return super().form_valid(form)

    def get_success_url(self):
        return reverse("product_ideas_bugs", kwargs={"product_slug": self.kwargs.get("product_slug")})

class UpdateProductIdea(LoginRequiredMixin, utils.BaseProductDetailView, UpdateView):
    template_name = "product_management/update_product_idea.html"
    model = Idea
    form_class = IdeaForm

    def dispatch(self, request, *args, **kwargs):
        obj = self.get_object()
        if obj.person != request.user.person:
            return self.handle_no_permission()
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self):
        return reverse("product_idea_detail", kwargs=self.kwargs)

class ProductIdeaDetail(utils.BaseProductDetailView, DetailView):
    template_name = "product_management/product_idea_detail.html"
    model = Idea
    context_object_name = "idea"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["vote_count"] = IdeaVote.objects.filter(idea=self.object).count()
        if self.request.user.is_authenticated:
            context["user_has_voted"] = IdeaVote.objects.filter(voter=self.request.user, idea=self.object).exists()
        return context

class CreateProductBug(LoginRequiredMixin, utils.BaseProductDetailView, CreateView):
    template_name = "product_management/add_product_bug.html"
    form_class = BugForm

    def form_valid(self, form):
        form.instance.person = self.request.user.person
        form.instance.product = get_object_or_404(Product, slug=self.kwargs.get("product_slug"))
        return super().form_valid(form)

    def get_success_url(self):
        return reverse("product_ideas_bugs", kwargs={"product_slug": self.kwargs.get("product_slug")})

class ProductBugDetail(utils.BaseProductDetailView, DetailView):
    template_name = "product_management/product_bug_detail.html"
    model = Bug
    context_object_name = "bug"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["actions_available"] = self.object.person == self.request.user.person if self.request.user.is_authenticated else False
        return context

class UpdateProductBug(LoginRequiredMixin, utils.BaseProductDetailView, UpdateView):
    template_name = "product_management/update_product_bug.html"
    model = Bug
    form_class = BugForm

    def dispatch(self, request, *args, **kwargs):
        obj = self.get_object()
        if obj.person != request.user.person:
            return self.handle_no_permission()
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self):
        return reverse("product_bug_detail", kwargs=self.kwargs)

def cast_vote_for_idea(request, pk):
    if not request.user.is_authenticated:
        return HttpResponse("You must be logged in to vote.", status=403)
    
    idea = get_object_or_404(Idea, pk=pk)
    vote, created = IdeaVote.objects.get_or_create(idea=idea, voter=request.user)
    
    if not created:
        vote.delete()
    
    vote_count = IdeaVote.objects.filter(idea=idea).count()
    return HttpResponse(vote_count)