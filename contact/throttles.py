from rest_framework.throttling import AnonRateThrottle, UserRateThrottle


class ContactAnonThrottle(AnonRateThrottle):
    rate = '5/hour'
    scope = 'contact'


class ContactUserThrottle(UserRateThrottle):
    rate = '10/hour'
    scope = 'contact_user'
