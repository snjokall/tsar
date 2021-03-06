# -*- coding: utf-8 -*-
from django.shortcuts import render_to_response, get_object_or_404
from members.models import Member
from groups.models import Group, Membership
from events.models import Event

import datetime

now=datetime.datetime.now()

def index(request):
	all_groups_list = Group.objects.all().order_by('title')
	return render_to_response('groups/groups_index.html', { 'group_list': all_groups_list })

from django.contrib.auth.decorators import login_required

#@login_required
def group_page(request, slug):
	g = get_object_or_404(Group, slug=slug)
	#import pprint
	#pprint.pprint(g.members.all())
	om = Member.objects.exclude(membership__group__slug=slug)
	recent_events_list=Event.objects.filter(eventrole__groupinvitation__group__slug=slug).filter(date_time_begin__lte=now).distinct()
	coming_events_list=Event.objects.filter(eventrole__groupinvitation__group__slug=slug).filter(date_time_begin__gte=now).distinct()
	return render_to_response('groups/group_page.html', { 'group': g, 'members': om, 'recent_events_list': recent_events_list, 'coming_events_list': coming_events_list, })
