from django.template import Library
from ..models import LRCDatabaseUser, StaffUserPosition, Semester

register = Library()

@register.filter(name='get_si_courses')
def get_si_courses(user: LRCDatabaseUser):
    active_position = StaffUserPosition.objects.filter(person=user, semester=Semester.objects.get_active_sem(), position="SI").all()
    pos_list = [{'course_name':str(pos.si_course.course),'course_id':pos.si_course.course.id} for pos in active_position]
    return pos_list

@register.filter(name='get_tutor_courses')
def get_tutor_courses(user: LRCDatabaseUser):
	active_position = StaffUserPosition.objects.filter(person=user, semester=Semester.objects.get_active_sem(), position="Tutor").all()
	pos_list = []
	for pos in active_position:
		for course in pos.tutor_courses.all():
			pos_list.append({'course_name':str(course),'course_id':course.id})
	return pos_list

@register.filter(name='get_peers')
def get_peers(user: LRCDatabaseUser):
	active_position = StaffUserPosition.objects.filter(person=user, semester=Semester.objects.get_active_sem(), position="PM").all()
	peers = []
	for pos in active_position:
		for peer in pos.peers_list():
			peers.append({'name':str(peer),'id':peer.id})
	return peers

@register.filter(name='positions')
def positions(user: LRCDatabaseUser):
	active_position = StaffUserPosition.objects.filter(person=user, semester=Semester.objects.get_active_sem()).all()
	positions = [] 
	for pos in active_position:
		if pos.position == "SI":
			positions.append(f"SI - {pos.si_course.short_name()}")
		elif pos.position == "Tutor":
			for tcourse in pos.tutor_courses.all():
				positions.append(f"Tutor - {tcourse.short_name()}")
		elif pos.position == "PM":
			for peer in pos.peers.all():
				positions.append(f"PM - {peer}")
	return positions