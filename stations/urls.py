from django.urls import path, include
from rest_framework import routers

from stations.views import (
    StationViewSet,
    RouteViewSet,
    TrainTypeViewSet,
    CrewViewSet,
    TrainViewSet,
    JourneyViewSet,
    OrderViewSet,
)

router = routers.DefaultRouter()
router.register("stations", StationViewSet)
router.register("routes", RouteViewSet)
router.register("train_types", TrainTypeViewSet)
router.register("crews", CrewViewSet)
router.register("trains", TrainViewSet)
router.register("journeys", JourneyViewSet)
router.register("orders", OrderViewSet)

urlpatterns = [path("", include(router.urls))]

app_name = "stations"