from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import CreditPackViewSet, TransactionViewSet

router = DefaultRouter()
router.register(r"credit-packs", CreditPackViewSet, basename="credit-packs")
router.register(r"transactions", TransactionViewSet, basename="transactions")

urlpatterns = [
    path("", include(router.urls)),
]
