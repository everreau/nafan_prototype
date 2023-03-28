from django.urls import path
from django.views.generic import TemplateView
from django.contrib.auth.decorators import login_required, permission_required

from .views import *

urlpatterns = [
    # TODO:
    #  - search results
    #  - repository record
    #  - collection guides (pdf/ead/marc/local)
    path("", TemplateView.as_view(template_name="home.html"), name="home"),
    # TODO: 
    #   - DB table to add help pages?
    #   - Link from homepage?
    path("help", TemplateView.as_view(template_name="help.html"), name="help"),
    path("joinus", JoinRequestCreateView.as_view(), name="join-us"),
    path("joinus/success", TemplateView.as_view(template_name="join_us_success.html"), name="join-us-success"),

    # TODO: 
    # Accept Join
    # Reject Join
    path("dashboard/", DashboardView.as_view(), name="dashboard"),

    # Users
    # TODO:
    # add user role view
    # layout
    # username or fullname search
    # filter by active or inactive
    path('users', UserListView.as_view(), name='list-users'),

    # TODO: layout
    path('users/add', UserCreateView.as_view(), name='create-user'),
    path('users/<int:pk>/update', UserUpdateView.as_view(), name='update-user'),
    path('users/<int:pk>/delete', UserDeleteView.as_view(), name='delete-user'),

    # Repositories
    # TODO: search/filter by status, name state city
    path('repositories/', RepositoryListView.as_view(), name='list-repositories'),
    # TODO: layout
    path('repositories/view/<str:slug>', RepositoryDetailView.as_view(), name='detail-repository'),

    path('repositories/add', RepositoryCreateView.as_view(), name='create-repository'),
    path('repositories/<str:slug>/update', RepositoryUpdateView.as_view(), name='update-repository'),
    path('repositories/<str:slug>/delete', RepositoryDeleteView.as_view(), name='delete-repository'),
    # TODO: set repository and make hidden
    path('repositories/<str:slug>/add-users', RepositoryAddUserView.as_view(), name='add-repository-user'),

    # Harvest Profiles
    # TODO: template tag for user is admin of this repo
    path('repositories/<str:slug>/profiles', ProfileListView.as_view(), name='list-profiles'),
    # TODO: hide repo selector
    path('repositories/<str:slug>/profiles/add', ProfileCreateView.as_view(), name='create-profile'),
    # TODO: do harvest
    path('repositories/<str:slug>/profiles/<int:pk>', ProfileDetailView.as_view(), name='detail-profile'),
    path('repositories/<str:slug>/profiles/<int:pk>/update', ProfileUpdateView.as_view(), name='update-profile'),
    path('repositories/<str:slug>/profiles/<int:pk>/delete', ProfileDeleteView.as_view(), name='delete-profile'),

    # FindingAids
    path('repositories/<str:slug>/findingaids', FindingAidListView.as_view(), name='list-findingaids'),
    path('repositories/<str:slug>/findingaids/add', FindingAidCreateView.as_view(), name='create-findingaid'),
    path('repositories/<str:slug>/findingaids/<int:pk>', FindingAidDetailView.as_view(), name='detail-findingaid'),
    path('repositories/<str:slug>/findingaids/<int:pk>/update', FindingAidUpdateView.as_view(), name='update-findingaid'),
    path('repositories/<str:slug>/findingaids/<int:pk>/delete', FindingAidDeleteView.as_view(), name='delete-findingaid'),

    # Finding Aid Defaults
    path('repositories/<str:slug>/findingaids/defaults/create', FindingAidDefaultCreateView.as_view(), name='create-defaults'),
    path('repositories/<str:slug>/findingaids/defaults/update/<int:pk>', FindingAidDefaultUpdateView.as_view(), name='update-defaults'),
    path('repositories/<str:slug>/findingaids/defaults/delete', FindingAidDefaultDeleteView.as_view(), name='delete-defaults'),

    # Logs
    path("audit", TemplateView.as_view(template_name="audit.html"), name="audit"),
    path("tracelog", TemplateView.as_view(template_name="tracelog.html"), name="tracelog"),
]
