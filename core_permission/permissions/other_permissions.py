from django.conf import settings
from rest_access_policy import AccessPolicy


# documentacion de permisos: https://rsinger86.github.io/drf-access-policy/
# para usar multiples permisos en una clase: https://github.com/caxap/rest_condition

superadmin = settings.CONS['GROUPS']['SUPERADMIN']


class BaseSuperuserPermissions(AccessPolicy):
	'''
	Permiso a todo.
	Permiso a ser seteado a nivel global.
	'''
	def __init__(self):
		self.statements += [
			{
				'action': ['*'],
				'principal': ['group:' + superadmin],
				'effect': 'allow' 
			}
		]

