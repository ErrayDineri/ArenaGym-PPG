from rest_framework import routers
from .views import UserViewSet, ModeratorViewSet, CourtViewSet, ReservationViewSet, PaymentViewSet
router=routers.DefaultRouter()
router.register(r'users', UserViewSet, basename='user')
router.register(r'moderators', ModeratorViewSet, basename='moderator')
router.register(r'courts', CourtViewSet, basename='court')
router.register(r'reservations', ReservationViewSet, basename='reservation')
router.register(r'payments', PaymentViewSet, basename='payment')
urlpatterns = router.urls