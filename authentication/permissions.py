from rest_framework.permissions import BasePermission


def _get_role(request):
    return getattr(getattr(request.user, 'profile', None), 'role', None)


class IsAdmin(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and _get_role(request) == 'admin'


class IsTeacher(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and _get_role(request) in ('teacher', 'school_teacher')


class IsSchoolStaff(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and _get_role(request) in ('school_teacher', 'school_principle')


class IsAdminOrMarketing(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and _get_role(request) in ('admin', 'marketing')


class IsAdminOrAccount(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and _get_role(request) in ('admin', 'account')


class IsStaff(BasePermission):
    """Any non-student role."""
    STAFF_ROLES = ('teacher', 'school_teacher', 'school_principle', 'admin', 'account', 'marketing')

    def has_permission(self, request, view):
        return request.user.is_authenticated and _get_role(request) in self.STAFF_ROLES
