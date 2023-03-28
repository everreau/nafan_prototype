from django.views.generic import TemplateView
from django.views.generic.detail import DetailView
from django.views.generic.list import ListView
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin

from .models import *
from .forms import *

#
# Dashboard
#

class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = "dashboard.html"

    def get_context_data(self,*args, **kwargs):
        context = super(DashboardView, self).get_context_data(*args,**kwargs)
        if self.request.user.is_site_admin:
            context['join_requests'] = JoinRequest.objects.all()
        return context
    
#
# Repositories
#

class RepositoryDetailView(DetailView):
    model = Repository

class RepositoryListView(ListView):
    model = Repository

    def get_queryset(self):
        if self.request.user:
            return self.request.user.get_user_repositories()
        else:
            return Repository.objects.filter(status=Repository.PUBLIC)

class RepositoryCreateView(UserPassesTestMixin, CreateView):
    model = Repository
    fields = '__all__'

    def test_func(self):
        return self.request.user.is_site_admin

class RepositoryUpdateView(UserPassesTestMixin, UpdateView):
    model = Repository
    fields = '__all__'

    def test_func(self):
        return self.request.user.is_site_admin

class RepositoryDeleteView(UserPassesTestMixin, DeleteView):
    model = Repository
    success_url = reverse_lazy('list-repositories')

    def test_func(self):
        return self.request.user.is_site_admin

class RepositoryAddUserView(UserPassesTestMixin, CreateView):
    model = UserRole
    fields = '__all__'

    def get_initial(self):
        initial = super().get_initial()
        initial.update({'repository': Repository.objects.get(slug=self.kwargs['slug'])})
        return initial

    def test_func(self):
        return self.request.user.is_site_admin or self.request.user.is_admin_of(self.request.slug)

#
# Users
#

class UserListView(ListView):
    model = User

    def test_func(self):
        return self.request.user.is_site_admin

class UserCreateView(UserPassesTestMixin, CreateView):
    model = User
    fields = ['email', 'first_name', 'last_name', 'is_site_admin']

    def test_func(self):
        return self.request.user.is_site_admin

class UserUpdateView(UserPassesTestMixin, UpdateView):
    model = User
    fields = ['email', 'first_name', 'last_name', 'is_site_admin']

    def test_func(self):
        return self.request.user.is_site_admin

class UserDeleteView(UserPassesTestMixin, DeleteView):
    model = User
    success_url = reverse_lazy('list-users')

    def test_func(self):
        return self.request.user.is_site_admin

#
# Join Requests
#

class JoinRequestCreateView(CreateView):
    model = JoinRequest
    fields = '__all__'
    template_name = "join_us.html"
    success_url = reverse_lazy('join-us-success')

#
# Harvest Profiles
#

class ProfileDetailView(UserPassesTestMixin, DetailView):
    model = HarvestProfile

    def test_func(self):
        return self.request.user.is_repo_member(self.get_object().repository)

class ProfileListView(UserPassesTestMixin, ListView):
    model = HarvestProfile

    def get_queryset(self):
        return self.model._default_manager.filter(repository__slug=self.kwargs['slug'])

    def get_context_data(self,*args, **kwargs):
        context = super(ProfileListView, self).get_context_data(*args,**kwargs)
        context['repository'] = Repository.objects.get(slug=self.kwargs['slug'])
        return context

    def test_func(self):
        return self.request.user.is_repo_admin(Repository.objects.get(slug=self.kwargs['slug']))

class ProfileCreateView(UserPassesTestMixin, CreateView):
    model = HarvestProfile
    fields = ("repository", "name", "location", "harvest_type", "default_format",)

    def get_initial(self):
        initial = super().get_initial()
        initial.update({'repository': Repository.objects.get(slug=self.kwargs['slug'])})
        return initial
    
    def test_func(self):
        return self.request.user.is_repo_admin(Repository.objects.get(slug=self.kwargs['slug']))

class ProfileUpdateView(UserPassesTestMixin, UpdateView):
    model = HarvestProfile
    fields = '__all__'

    def test_func(self):
        return self.request.user.is_repo_admin(self.get_object().repository)

class ProfileDeleteView(UserPassesTestMixin, DeleteView):
    model = HarvestProfile

    def get_success_url(self):
        return reverse_lazy('list-profiles', kwargs={'slug': self.get_object().repository.slug})

    def test_func(self):
        return self.request.user.is_repo_admin(self.get_object().repository)

#
# Finding Aids
#

class FindingAidDetailView(DetailView):
    model = FindingAid

class FindingAidListView(ListView):
    model = FindingAid

    def get_context_data(self, *args, **kwargs):
        context = super(FindingAidListView, self).get_context_data(*args, **kwargs)
        context.update({'repository': Repository.objects.get(slug=self.kwargs['slug'])})
        return context

    def get_queryset(self):
        return self.model._default_manager.filter(repository__slug=self.kwargs['slug'])

class FindingAidCreateView(UserPassesTestMixin, CreateView):
    model = FindingAid
    fields = '__all__'
    forms = {
        'dacs': DACSForm,
        'ead': EADForm,
        'marc': MARCForm,
        'pdf': PDFForm
    }

    def get_initial(self):
        initial = super().get_initial()
        initial.update({'repository': Repository.objects.get(slug=self.kwargs['slug'])})
        return initial
    
    def get_form_class(self):
        form_type = self.request.GET.get("record_type", False)
        if form_type:
            return self.forms[form_type]
        else:  
            return super().get_form_class()

    def test_func(self):
        return self.request.user.is_repo_admin(Repository.objects.get(slug=self.kwargs['slug']))

class FindingAidUpdateView(UserPassesTestMixin, UpdateView):
    model = FindingAid
    fields = '__all__'

    def test_func(self):
        return self.request.user.is_repo_admin(self.get_object().repository)

class FindingAidDeleteView(UserPassesTestMixin, DeleteView):
    model = FindingAid

    def get_success_url(self):
        return reverse('detail-repository', kwargs={'slug' : self.object.repository.slug})

    def test_func(self):
        return self.request.user.is_repo_admin(self.get_object().repository)

#
# Finding Aid Defaults
#

class FindingAidDefaultUpdateView(UserPassesTestMixin, UpdateView):
    model = FindingAidDefaults
    fields = '__all__'

    def get_success_url(self):
        return reverse('list-findingaids', kwargs={'slug' : self.object.repository.slug})

    def test_func(self):
        return self.request.user.is_repo_admin(self.get_object().repository)

class FindingAidDefaultCreateView(UserPassesTestMixin, CreateView):
    model = FindingAidDefaults
    fields = '__all__'
    
    def get_success_url(self):
        return reverse('list-findingaids', kwargs={'slug' : self.object.repository.slug})

    def get_initial(self):
        initial = super().get_initial()
        initial.update({'repository': Repository.objects.get(slug=self.kwargs['slug'])})
        return initial

    def test_func(self):
        return self.request.user.is_repo_admin(Repository.objects.get(slug=self.kwargs['slug']))

class FindingAidDefaultDeleteView(UserPassesTestMixin, DeleteView):
    model = FindingAidDefaults

    def get_success_url(self):
        return reverse('detail-repository', kwargs={'slug' : self.object.repository.slug})

    def test_func(self):
        return self.request.user.is_repo_admin(self.get_object().repository)

