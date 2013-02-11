# -*- coding: utf-8 -*-
from django.db import models
from groups.models import Group
from members.models import Member
from django.db.models import get_model
from django import forms
from django.forms import ModelForm
from django.forms.extras.widgets import SelectDateWidget
from django.forms.widgets import SplitDateTimeWidget

class Role(models.Model):
	# The roles that participatns in an event may have (e.g. driver, organiser, instructor, etc.).
	title = models.CharField(max_length=64)

	def __unicode__(self):
		return self.title

class EventType(models.Model):
	# Evetns may be of several different types that one may like to distinguish between (e.g. exercise, course, meeting, social, etc.). One may even wish to serve different sets of tags for each.
	title = models.CharField(max_length=64)
	description = models.TextField(blank=True)

	def __unicode__(self):
		return self.title

class Event(models.Model):
	# The fundamental object. Most of the magic happens in EventRole, however.
	# An event may have several roles and members can be invited to one or more roles, either as members, or through groups which they belong to.
	# Events come in various types, have locations and can be tagged with techniques employed or something similar that will aid in diagnosing events.
	title = models.CharField(max_length=64)
	description = models.TextField(blank=True)
	date_time_begin = models.DateTimeField()
	date_time_end = models.DateTimeField()
	# TODO: Need to implement locations. Character fields or just store this all in a GPX file?
	event_type = models.ForeignKey(EventType)
	# TODO: Add equipment to log equipment use. Better to add this as a relation rather than a tag?

	def __unicode__(self):
		return self.title

class EventRole(models.Model):
	# An event may have several roles, and the same group or member may be invited to each of these. So for each role on each event we need an “event role”.
	# These are associated with:
	# * an event
	# * a role
	# * (optionally) one or more groups through GroupInvitation
	# * (optionally) one or more members through MemberInvitation
	# An event role may have a minimum or maximum number of participants and can even be open to anyone who may wish to join.
	# TODO: Open/closed events. Simple boolean?
	# TODO: The “hidden” parameter should probably be here, rather than in the intermediary models.
	event = models.ForeignKey(Event)
	role = models.ForeignKey(Role)
	invited_groups = models.ManyToManyField(Group, through='GroupInvitation')
	invited_members = models.ManyToManyField(Member, through='MemberInvitation')
	minimum = models.SmallIntegerField(default=0)
	maximum = models.SmallIntegerField(default=0)

	def __unicode__(self):
		return self.event.title +' '+ self.role.title

class GroupInvitation(models.Model):
	# An intermediary model between an event role and a group.
	event_role = models.ForeignKey(EventRole)
	group = models.ForeignKey(Group)
	is_hidden = models.BooleanField(default=False)

	def __unicode__(self):
		return self.event_role.__unicode__() +'>'+ self.group.title

class MemberInvitation(models.Model):
	# An intermediary model between an event role and a member.
	event_role = models.ForeignKey(EventRole)
	member = models.ForeignKey(Member)
	is_hidden = models.BooleanField(default=False)

	def __unicode__(self):
		return self.event_role.__unicode__() +'>'+ self.member.user.username

# TODO: Need to implement some sort of confirmation class.

class EventCreation(ModelForm):
	class Meta:
		model = Event
	title = forms.CharField(max_length=64,label='Titill:',initial='Titill', widget=forms.TextInput(attrs={'placeholder': 'Titill viðburðar'}))
	date_time_begin = forms.DateTimeField(input_formats={'%m/%d/%Y %H:%M'},label='Hefst:')
	date_time_end   = forms.DateTimeField(input_formats={'%m/%d/%Y %H:%M'},label='Lýkur:')
	description = forms.CharField(widget=forms.Textarea(attrs={'cols': '80', 'rows': '5'}),label='',initial='Lýsing')
	event_type = forms.ModelChoiceField(queryset=EventType.objects.all(), empty_label='(ekkert)')
#	class Meta:
#		model = Event
	#TODO: Need to implement locations. Character fields or just store this all in a GPX file?
	#Should locations be tags, or is it sufficient to filter from predefined areas and GPX files?
	#TODO: Add the type after we've created the event as this should probably happen at the same stage as when we add the various tags.
	#event_type = forms.ModelChoiceField(queryset=EventType.objects.all())
	#Add equipment to log equipment use. Better to add this as a relation rather than a tag?

class EventRoleForm(ModelForm):
	class Meta:
		model = EventRole
	invited_groups = forms.ModelMultipleChoiceField(queryset=Group.objects.all())
	invited_members= forms.ModelMultipleChoiceField(queryset=Member.objects.all())
	minimum = forms.CharField(label='Fjöldi:')
	maximum = forms.CharField(label='til')