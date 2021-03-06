# -*- coding: utf-8 -*-
from django.shortcuts import render_to_response, render
from django.template import RequestContext
from members.models import Member
from groups.models import Group
from events.models import Role, EventType, Event, EventRole, EventCreation, EventRoleForm, GroupInvitation, MemberInvitation, MemberResponse
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import get_object_or_404, render_to_response
from django.contrib.auth.models import User

from django.utils import timezone
from datetime import datetime
from dateutil import parser

import simplejson as json
#import json

now = datetime.now()

def calendar_events_list(start, end):
	# Get all events between the two dates:
	print 'Retrieve events between {} and {}'.format(start, end)
	import time
	#print time.gmtime(int(start))
	#print int(start)
	#print datetime.fromtimestamp(int(start))
	calendar_begins = datetime.fromtimestamp(int(start))
	calendar_ends = datetime.fromtimestamp(int(end))
	import calendar
	print 'The calendar runs from {} to {}'.format(calendar_begins, calendar_ends)#time.strftime("%Y", time.gmtime(calendar.timegm(calendar_begins))), time.strftime("%Y", time.gmtime(calendar.timegm(calendar_ends))))
	events = Event.objects.filter(date_time_end__gt=calendar_begins).filter(date_time_begin__lt=calendar_ends)
	events_list = []
	for event in events:
		events_list.append({
			'title': event.title,
			'start': calendar.timegm(event.date_time_begin.utctimetuple()),
			'end': calendar.timegm(event.date_time_end.utctimetuple()),
			'id': event.id,
			'url': '/vidburdur/'+str(event.id),
		})
	import pprint
	pprint.pprint(events_list)
	return HttpResponse(json.dumps(events_list), mimetype='application/javascript')
	print 'FINISHED'

def list_events(request):
	if request.is_ajax():
		# Prepare events for calendar
		return calendar_events_list(request.GET['start'], request.GET['end'])
	# Otherwise it's just a normal request for the events page.
	recent_events_list = Event.objects.filter(date_time_begin__lte=now).order_by('-date_time_begin')[:20]
	coming_events_list = Event.objects.filter(date_time_begin__gte=now).order_by('date_time_begin')[:20]
	# TODO: Add incidents?
	# recent_incidents_list = Incident.objects.filter(date_time_begin__lte=now).order_by('-date_time_begin')[:20]
	return render_to_response('events/events_index.html', { 'recent_events_list': recent_events_list, 'coming_events_list': coming_events_list })

from django.views.decorators.csrf import csrf_exempt

@csrf_exempt
def event_response(request):
	print 'in event_response'
	if not request.user.is_authenticated():
		cm = User.objects.get(id=2)
	else:
		cm = request.user.member
	print cm
	if request.is_ajax():
		#import pprint
		action = request.POST['action']
		if action == 'attend':
			act = 'Y'
		elif action == 'absent':
			act = 'N'
		eventrole_id = request.POST['eventrole']

		print 'action: {} or {}'.format(action,act)
		print 'eventrole.id: {}'.format(eventrole_id)

		print 'OK, now for my second act...'
		#TODO: read current member info from login!!!
		#mr = MemberResponse(event_role__id=eventrole_id, member=cm, response='Y')
		#event = get_object_or_404(Event, id=pk)
		#print event
		event_role = get_object_or_404(EventRole, id=eventrole_id)
		#event_role = EventRole.objects.get(event_role__id=14)
		print event_role.id
		try:
			mr = MemberResponse.objects.get(event_role=event_role, member=cm)
			print '>> MemberResponse {} found'.format(mr)
			mr.response=act
		except:
			mr = MemberResponse(event_role=event_role, member=cm, response=act)
			print '>> No MemberResponse found. Creating a new one: {}'.format(mr)

		try:
			mr.clean_fields()
			mr.save()
			print '>> SAVED'
		except:
			print '>> FAILED'
			return HttpResponse('Failed: could not save member response')
		##print 'Hér kemur JSON útgáfan:'
		##data = json.loads(request.POST['data'])
		##pprint.pprint(data)
	#else:
		#print 'not ajax'
	#TODO: Have to return the change so that the script can update the attendance list.
	data = {
		'user_id': cm.user.id,
		'user_name': cm.__unicode__(),
		'username': cm.user.username,
		'event_id': event_role.event.id,
		'role_id': event_role.role.id,
		'eventrole_id': event_role.id,
		'action': action,
	}
	print 'Data: {}'.format(data)
	jsondata = json.dumps(data)
	print 'JSON: ',jsondata
	print 'XXXXX responding'
	return HttpResponse(json.dumps(data))##, mimetype='application/javascript')
	#return HttpResponse(jsondata)

def display_event(request, pk):
	event = get_object_or_404(Event, id=pk)
	#TODO: read this from login info!!!
	if not request.user.is_authenticated():
		cm = User.objects.get(id=2)
	else:
		cm = request.user.member
	# Compile a list of members who are invited.
	# Workflow:
	# Create an empty list of invited members.
	# For each role
	#	for each invited group
	#		for each member
	#			if member is not on the invited list
	#				add member to the list
	#	for each invited member
	#		if member is not on the invited list
	#			add member to the list
	role_data = []
	
	for eventrole in EventRole.objects.filter(event=event):
		print 'On EventRole {}:'.format(eventrole)
		attending = []
		absent = []
		for memberresponse in eventrole.memberresponse_set.all():
			print '> memberresponse: {}'.format(memberresponse)
			if memberresponse.response == 'Y':
				attending.append(memberresponse.member)
			if memberresponse.response == 'N':
				absent.append(memberresponse.member)
		print '> Attending members {}:'.format(attending)
		print '> Absent members: {}'.format(absent)
		invitedmembers = []
		print '>> Members invited through groups'
		for member in Member.objects.filter(group__groupinvitation__event_role=eventrole).filter(group__groupinvitation__event_role__event=event):
			print '>>   {}'.format(member.user.username)
			if member not in invitedmembers and member not in attending and member not in absent:
				invitedmembers.append(member)
				print '++   {}'.format(member)
		print '>> Members invited directly'
		for member in Member.objects.filter(memberinvitation__event_role=eventrole).filter(memberinvitation__event_role__event=event):
			print '>>   {}'.format(member)
			if member not in invitedmembers and member not in attending and member not in absent:
				invitedmembers.append(member)
				print '++   {}'.format(member)

		# Check to see whether the current member has responded or is invited to a particular role.
		cm_status = 'not invited'
		if cm in invitedmembers:
			cm_status = 'invited'
		if cm in absent:
			cm_status = 'absent'
		if cm in attending:
			cm_status = 'attending'
		role_data.append({ 'eventrole': eventrole, 'invitedmembers': invitedmembers, 'absentmembers': absent, 'attendingmembers': attending, 'cm_status': cm_status, })

# TODO: Currently members can sign up for multiple roles. This is probably a good thing as members may be both a driver and participant and we want to log each role.
#	# Now let's make sure that a member who is attending a role doesn't get invited
#	# to others.
#	# TODO: Perhaps we should implement a way of attending more than one role.
#	# Perhaps a pop-up to allow members to split their time among the roles.
#	for role in role_data:
#		if role['cm_status'] == 'attending':
#			for tmprole in role_data:
#				if tmprole['cm_status'] == 'invited' or tmprole['cm_status'] == 'absent':
#					tmprole['cm_status'] = 'attending elsewhere'
#			role['cm_status'] = 'attending'
	import pprint
	pprint.pprint(role_data)
	return render_to_response('events/event_page.html', { 'event': event, 'cm': cm, 'role_data': role_data, 'status_list': ['attending', 'absent', 'unclear'] })

def display_or_save_event_form(request):
	event_types = EventType.objects.all()
	event_roles = Role.objects.all()
	members = Member.objects.all()
	groups = Group.objects.all()
	form = EventCreation(request.POST)
	#if request.method == 'POST':
	#	event_role_form = EventRoleForm(request.POST)
	#	if (form.is_valid()):
	#		form.save()
	#	return HttpResponse(json.dumps({ 'form': form, 'event_role_form': event_role_form, 'event_types': event_types, 'event_roles': event_roles, 'members': members, 'groups': groups, }))
	#else:
	return render(request, 'events/create_event.html', { 'form': form, 'event_types': event_types, 'event_roles': event_roles, 'members': members, 'groups': groups, })

#TODO: Do we need to remove orphaned invitations once an EventRole has been removed?
#TODO: Reorder these try-s to shorten them so that the exceptions make more sense.
def save_event(request):
	if request.is_ajax() or True:
		print 'Is AJAX'
		# TODO: Add handler for these below. They are required and must be submitted or else the form will not validate. Or perhaps the clean_fields() exception is enough...?
		import pprint
		print 'Hér kemur hrátt data:'
		pprint.pprint(request.POST['data'])
		print 'Hér kemur JSON útgáfan:'
		data = json.loads(request.POST['data'])
		pprint.pprint(data)
		t = data['title']
		d = data['description']
		dtb = timezone.make_aware(parser.parse(data['date_time_begin']),timezone.get_default_timezone())
		dte = timezone.make_aware(parser.parse(data['date_time_end']),timezone.get_default_timezone())
		et_id = data['event_type']
		try:
			event_id = data['event_id']
			if event_id == '':
			# If no event id has been supplied, we'll create a new event.
				event = Event(title=t, description=d, date_time_begin=dtb, date_time_end=dte, event_type_id=et_id)
			else:
			# else we update the existing one.
				event = Event.objects.get(pk=event_id)
				event.title = t
				event.description = d
				event.date_time_begin = dtb
				event.date_time_end = dte
				event.event_type_id = et_id
				#return HttpResponse('Event fields updated.')
			# Now save the event
			try:
				event.clean_fields()
				event.save()
				print 'The event is: ------'
				print (vars(event))
				print '--------------------'
			except:
				return HttpResponse ("Hello, world. Could not save event.")

			# Now that the event has been taken care of, let's sort out the event roles etc.
			# Flow:
			# For each role:
			for role in Role.objects.all():
				print 'Role ID %s' % role.id
				print 'Role is %s' % role
				try: #if we want the role:
					currentparticipants = [] # This will be populated below if the event exists (and currently has any participants).
					currentgroups = [] # This will be populated below if the event exists (and currently has any participants).
					currentmembers= [] # This will be populated below if the event exists (and currently has any participants).

					wantedparticipantIDs = data['role'][role.id]['participants']
					print 'Wanted participantsID: {}'.format(wantedparticipantIDs)
					wantedgroups = [Group.objects.get(pk=int(groupid[1:])) for groupid in wantedparticipantIDs if groupid[0]=='g']
					print 'We want event role {} with groups {}'.format(role, wantedgroups)
					wantedmembers= [Member.objects.get(pk=int(memberid[1:])) for memberid in wantedparticipantIDs if memberid[0]=='m']
					print 'We want event role {} with members {}'.format(role, wantedmembers)
					try: #check whether the EventRole already exists
						# In the event that an EventRole already exists, we have to:
						#  1. Get the EventRole, stored in eventrole.
						#  2. Remove unwanted participants
						# Adding wanted participants is shared with EventRoles that
						# need to be created so we're doing that later on.
						#  3. Update the minimum and maximum number of participants

						# 1.
						eventrole = EventRole.objects.get(event_id=event.id,role_id=role.id)
						print 'EventRole "{}" already exists.'.format(eventrole)

						# 2.
						#currentgroups= GroupInvitation.objects.filter(event_role=eventrole)
						currentgroups = eventrole.invited_groups.all()
						currentmembers= eventrole.invited_members.all()
						print 'currentgroups: {}'.format(currentgroups)
						print 'currentmembers: {}'.format(currentmembers)
						print 'EventRole already has these invitations:'
						for group in currentgroups:
							print '>>{} ({})'.format(group, group.id)
							#print 'Comare {} with {}'.format(group.id,wantedgroups)
							if group not in wantedgroups:
								print '-- ID is {}: We don\'t want {}.'.format(group.id,group)
								#gi = GroupInvitation(event_role=eventrole,group=group)
								#print 'Removing group {} from eventrole {}'.format(group,eventrole)
								#print 'DEBUG'
								try:
									print 'DEBUG: {}'.format(eventrole.invited_groups)
									gi = GroupInvitation.objects.get(event_role=eventrole,group=group)
									#print gi
									gi.delete()
									print 'BINGO'
								except:
									print 'Could not remove group {} from {}'.format(group,currentgroups)
							else:
								print '++ ID is {}: We keep {}.'.format(group.id,group)
						for member in currentmembers:
							print '>>{} ({})'.format(member, member.id)
							if member not in wantedmembers:
								print '-- ID is {}: We don\'t want {}.'.format(member.id,member)
								try:
									print 'DEBUG: {}'.format(eventrole.invited_members)
									mi = MemberInvitation.objects.get(event_role=eventrole,member=member)
									#print mi
									mi.delete()
									print 'BINGO'
								except:
									print 'Could not remove member {} from {}'.format(member,currentmembers)
							else:
								print '++ ID is {}: We keep {}.'.format(member.id,member)
						# 3.
						if eventrole.minimum != int(data['role'][role.id]['min']) or eventrole.maximum != int(data['role'][role.id]['max']):
							eventrole.minimum = int(data['role'][role.id]['min'])
							eventrole.maximum = int(data['role'][role.id]['max'])
							try:
								eventrole.clean_fields()
								eventrole.save()
								print 'eventrole saved: {}.'.format(eventrole)
							except:
								return HttpResponse('Hello, world. Could not update eventrole max/min numbers.')
					except: #else
						# Since there is no existing EventRole, we need to:
						#  1. Create an EventRole, and save it as eventrole.
						# and that's it! Adding participants is done below for both
						# existing and recently created EventRoles.
						eventrole = EventRole(event_id=event.id,role_id=role.id,minimum=int(data['role'][role.id]['min']), maximum=int(data['role'][role.id]['max']))
						print 'No EventRole exists, creating {}.'.format(eventrole)
						try:
							eventrole.clean_fields()
							eventrole.save()
							print 'eventrole saved: {}.'.format(eventrole)
						except:
							return HttpResponse('Hello, world. Could not save eventrole.')

					# Now that we have the eventrole and it has been stripped of its
					# unwanted participatns, let's add the wanted ones.
					# Workflow:
					# For each wanted participant,
					#   if they're not currently invited,
					#     create a GroupInvitation and attach it to the EventRole

					# For each participant
					print 'Adding invitations:'
					print 'Wanted groups: {}'.format(wantedgroups)
					print 'Wanted members: {}'.format(wantedmembers)
					for group in wantedgroups:
						print '>>{} ({})'.format(group, group.id)
						if group not in currentgroups:
							print '++ Group {} is not invited: Create GroupInvitation!'.format(group)
							gi = GroupInvitation(event_role=eventrole, group=group)
							print '++ GroupInvitation created: '.format(gi)
							try:
								gi.clean_fields()
								gi.save()
								print '++ GroupInvitation saved'
							except:
								print 'ERROR: Could not save GroupInvitation {}'.format(gi)
						else:
							print '.. Group {} already invited: nothing to do. :-)'.format(group)
					print 'Groups done!'
					for member in wantedmembers:
						print '>>{} ({})'.format(member, member.id)
						if member not in currentmembers:
							print '++ Member {} is not invited: Create MemberInvitation!'.format(member)
							mi = MemberInvitation(event_role=eventrole, member=member)
							print '++ MemberInvitation created: '.format(mi)
							try:
								mi.clean_fields()
								mi.save()
								print '++ MemberInvitation saved'
							except:
								print 'ERROR: Could not save MemberInvitation {}'.format(mi)
						else:
							print '.. Member {} already invited: nothing to do. :-)'.format(member)
					print 'All done!'
				except: #if we don't want the role:
					print 'No role wanted.'
					try: # check if the role exists and must be removed
						eventrole = EventRole.objects.get(event__id=event.id,role__id=role.id)
						print 'Removing eventrole: %s' % eventrole
						eventrole.delete()
					except: # No role wanted. No role exists. All good.
						print 'No role exists. All good.'
				print ' ..... '
		except:
			return HttpResponse("Hello, world. Could not create event.")
		return HttpResponse(event.id)
	else:
		return HttpResponse("Hello, world. Not AJAX request.")

#def group_save(request):
#	if request.is_ajax():
#		eventId = request.POST['eid']
#		roleId = request.POST['rid']
#		group = request.POST['grp']
#		member = request.POST['grp']
#		mininum = request.POST['min']
#		maximum = request.POST['max']
#	else:
#		# Perhaps just merge this with the standard view response.
#		return HttpResponse("Group save request isn't an AJAX request.")
