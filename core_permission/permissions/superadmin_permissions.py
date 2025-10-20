from django.conf import settings
from .other_permissions import BaseSuperuserPermissions

group = settings.CONS['GROUPS']['SUPERADMIN']


class SuperadminReadPermissions(BaseSuperuserPermissions):
    statements = [
        {
            "action": ["<safe_methods>"],
            "principal": ["group:" + group],
            "effect": "allow"
        },
        {
            "action": ["<method:post>",
                       "<method:put>",
                       "<method:patch>",
                       "<method:delete>"],
            "principal": ["group:" + group],
            "effect": "deny"
        }
    ]


class SuperadminReadEditPermissions(BaseSuperuserPermissions):
    statements = [
        {
            "action": ["*"],
            "principal": ["group:" + group],
            "effect": "allow"
        }
    ]
