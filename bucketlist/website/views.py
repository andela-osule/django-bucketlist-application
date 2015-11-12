# -*- coding: utf-8 -*-
from django.views.generic import View, ListView, DetailView, CreateView, DeleteView
from django.views.generic.edit import UpdateView
from django.shortcuts import render, redirect, get_object_or_404
from django.core.urlresolvers import reverse, reverse_lazy
from django.utils.timezone import now
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.template import RequestContext
from django.contrib import messages
from django.db import IntegrityError
from website.models import Bucketlist, BucketlistItem
from .utils import get_http_referer
from .forms import UpdateBucketlistItemForm
import datetime
import pdb
from pdb import Pdb


class LoginRequiredMixin(object):
    @classmethod
    def as_view(cls, **initkwargs):
        view = super(LoginRequiredMixin, cls).as_view(**initkwargs)
        return login_required(view)


class RootView(View):
    template_name = "website/index.html"

    def get(self, request, *args, **kwargs):
        today = datetime.date.today()
        return render(
                request, self.template_name,
                {
                    'today': today,
                    'now': now(),
                    'page_title': 'Home'
                }
            )


class RootFilesView(View):
    """Renders requests for `robots.txt` and `humans.txt`"""

    def get(self, request, *args, **kwargs):
        return render(
            request, self.kwargs.get('filename'),
            {}, content_type="text/plain"
        )


class LoginView(View):
    """Renders requests for authorization.
    """
    def post(self, request, *args, **kwargs):
        username = request.POST.get('username')
        password = request.POST.get('password')
        if not request.POST.get('remember_me', None):
            request.session.set_expiry(0)
        if '@' in username:
            try:
                user = User.objects.get(email=username)
                if not user.check_password(password):
                    messages.error(request, 'Wrong username or password.')
                    return redirect(
                        reverse('app.index'))
                else:
                    user = authenticate(
                        username=user.username,
                        password=user.password)
            except User.DoesNotExist:
                pass
        else:
            user = authenticate(
                username=username,
                password=password)
        if user is not None:
            login(request, user)
            return redirect(
                reverse('app.dashboard'))

        messages.error(request, 'Wrong username or password.')
        return redirect(
                reverse('app.index'))


class LogoutView(View):
    """Renders request to logout authenticated session.
    """
    def get(self, request, *args, **kwargs):
        logout(request)
        return redirect(reverse('app.index'))


class SignUpView(View):
    """Processes request to sign up a user
    """
    def post(self, request, *args, **kwargs):
        email = request.POST.get('email')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        password = request.POST.get('password')
        username = request.POST.get('username')
        try:
            user = User.objects.create_user(
                username=username,
                password=password,
                first_name=first_name,
                last_name=last_name,
                email=email
            )
        except IntegrityError:
            messages.error(request, 'Username is already taken.')
            return redirect(reverse('app.index'))

        if user:
            user = authenticate(username=username, password=password)
            login(request, user)
            messages.success(
                request,
                'Hello {}, please kindly update \
                your profile information.'.format(first_name))
            return redirect(reverse('app.dashboard'))
        return redirect(reverse('app.login'))


class DashboardView(LoginRequiredMixin, View):
    """Renders dashboard for logged in user"""

    def get(self, request, *args, **kwargs):
        bucketlists = Bucketlist.objects.order_by('date_created')
        return render(
            request,
            'website/dashboard.html',
            {
                'bucketlists': bucketlists
            }
        )


class BucketlistListView(LoginRequiredMixin, ListView):
    """Renders bucketlist for logged in user"""
    model = Bucketlist
    template_name = 'website/bucketlist_list.html'
    paginate_by = 5
    
    def get_queryset(self, **kwargs):
        query_string = self.request.GET.get('q', None)
        if query_string:
            return self.model.search(query_string)
        return self.model.objects.all()
    
    def get_context_data(self, **kwargs):
        context = super(BucketlistListView, self).get_context_data(**kwargs)
        context['now'] = now()
        context['q'] = self.request.GET.get('q', None)
        context['object'] = 'bucketlists'
        return context

class BucketlistDetailView(LoginRequiredMixin, DetailView):
    """Renders bucketlist detail and handle POST"""
    model = Bucketlist
    
    def get_context_data(self, **kwargs):
        context = super(BucketlistDetailView, self).get_context_data(**kwargs)
        setattr(
                context['object'],
                'children',
                BucketlistItem.objects.filter(bucketlist=context['object'].id)
            )
        context['now'] = now()
        return context



class BucketlistCreateView(LoginRequiredMixin, CreateView):
    model = Bucketlist
    fields = ['name']
    
    def get_success_url(self, pk):
        return reverse_lazy('app.bucketlist', kwargs={'pk': pk})
    
    def post(self, request):
        """ Overwrite post method to save bucketlist with user_id
        """
        form_cls = self.get_form_class()
        form = form_cls(request.POST)
        form_model = form.save(commit=False)
        form_model.user_id = request.user.id
        form_model.save()
        return redirect(self.get_success_url(pk=form_model.id))


class BucketlistUpdateView(LoginRequiredMixin, UpdateView):
    model = Bucketlist
    fields = ['name']
    template_name_suffix = '_update_form'
    success_url = reverse_lazy('app.bucketlists')

    def get_context_data(self, **kwargs):
        context = super(BucketlistUpdateView, self).get_context_data(**kwargs)
        context['now'] = now()
        return context
    

class BucketlistDeleteView(LoginRequiredMixin, DeleteView):
    model = Bucketlist
    success_url = reverse_lazy('app.bucketlists')

class BucketlistItemListView(LoginRequiredMixin, ListView):
    """Renders bucketlist edit view"""
    pass

class BucketlistItemCreateView(LoginRequiredMixin, CreateView):
    model = BucketlistItem
    fields = ['name', 'done']
    
    def get_success_url(self, pk):
        return reverse_lazy('app.bucketlist', kwargs={'pk': pk})
    
    def get_context_data(self, **kwargs):
        context = super(BucketlistItemCreateView, self).get_context_data(**kwargs)
        bucketlist = get_object_or_404(Bucketlist, pk=self.kwargs.get('pk'))
        context['object_name'] = bucketlist.name 
        context['now'] = now()
        return context
    
    def post(self, request, pk):
        """ Overwrite post method to save bucketlist with user_id
        """
        form_cls = self.get_form_class()
        form = form_cls(request.POST)
        form_model = form.save(commit=False)
        form_model.user_id = request.user.id
        bucketlist = get_object_or_404(Bucketlist, pk=pk)
        form_model.bucketlist = bucketlist
        form_model.save()
        return redirect(self.get_success_url(pk=bucketlist.id))
    

class BucketlistItemUpdateView(LoginRequiredMixin, UpdateView):
    model = BucketlistItem
    template_name_suffix = '_update_form'
    fields = ['name', 'done']
    
    def get_success_url(self, **kwargs):
        id, item_id = self.kwargs.values()
        return reverse_lazy('app.bucketlist',
                            kwargs={'pk':id})

    def get_queryset(self, **kwargs):
        pk = self.kwargs.get('pk_item', None)
        return self.model.objects.get(pk=pk)
    
    def get_object(self, queryset=None, **kwargs):
        if queryset is None:
            queryset = self.get_queryset(**kwargs)
        return queryset
    
    def get_context_data(self, **kwargs):
        pk = self.kwargs.get('pk_item')
        context = super(BucketlistItemUpdateView, self).get_context_data(**kwargs)
        context['now'] = now()
        return context

class BucketlistItemDeleteView(LoginRequiredMixin, DeleteView):
    """Renders bucketlist item delete confirmation"""
    model = BucketlistItem
    template_name_suffix = '_confirm_delete'
    
    def get_success_url(self, **kwargs):
        id, item_id = self.kwargs.values()
        return reverse_lazy('app.bucketlist',
                            kwargs={'pk':id})
        
    def get_queryset(self, **kwargs):
        pk = self.kwargs.get('pk_item', None)
        return self.model.objects.get(pk=pk)
    
    def get_object(self, queryset=None, **kwargs):
        if queryset is None:
            queryset = self.get_queryset(**kwargs)
        return queryset
    
    def get_context_data(self, **kwargs):
        pk = self.kwargs.get('pk_item')
        context = super(BucketlistItemDeleteView, self).get_context_data(**kwargs)
        context['now'] = now()
        return context


class BucketlistItemDetailView(LoginRequiredMixin, DetailView):
    """Renders bucketlist item detail view"""
    model = BucketlistItem

    def get_context_data(self, **kwargs):
        id, item_id = self.kwargs.values()
        context = {}
        context['object'] = get_object_or_404(BucketlistItem, pk=item_id)
        print context['object']
        context['now'] = now()
        return context