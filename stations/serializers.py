from django.db import transaction
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from stations.models import (
    Station,
    Route,
    Crew,
    Ticket,
    TrainType,
    Train,
    Order,
    Journey,
)


class StationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Station
        fields = ("id", "name", "latitude", "longitude")


class CrewSerializer(serializers.ModelSerializer):
    class Meta:
        model = Crew
        fields = ("id", "first_name", "last_name")


class RouteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Route
        fields = ("id", "source", "destination", "distance")


class RouteListSerializer(serializers.ModelSerializer):
    source = serializers.CharField(source="source.name", read_only=True)
    destination = serializers.CharField(
        source="destination.name", read_only=True
    )

    class Meta:
        model = Route
        fields = ("id", "source", "destination", "distance")


class RouteDetailSerializer(serializers.ModelSerializer):
    source = StationSerializer(read_only=True)
    destination = StationSerializer(read_only=True)

    class Meta:
        model = Route
        fields = ("id", "source", "destination", "distance")


class TrainTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = TrainType
        fields = ("id", "name")


class TicketSerializer(serializers.ModelSerializer):
    def validate(self, attrs):
        data = super(TicketSerializer, self).validate(attrs=attrs)
        Ticket.validate_ticket(
            attrs["cargo"],
            attrs["seat"],
            attrs["journey"].train,
            serializers.ValidationError,
        )
        return data

    class Meta:
        model = Ticket
        fields = ("id", "cargo", "seat", "journey", "order")


class TrainTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = TrainType
        fields = ("id", "name")


class TrainSerializer(serializers.ModelSerializer):
    class Meta:
        model = Train
        fields = (
            "id",
            "name",
            "cargo_num",
            "places_in_cargo",
            "train_type",
            "image",
        )


class TrainListSerializer(serializers.ModelSerializer):
    train_type = serializers.CharField(
        source="train_type.name", read_only=True
    )
    capacity = serializers.SerializerMethodField()

    class Meta:
        model = Train
        fields = (
            "id",
            "name",
            "cargo_num",
            "places_in_cargo",
            "capacity",
            "train_type",
            "image",
        )


class TrainDetailSerializer(serializers.ModelSerializer):
    train_type = TrainTypeSerializer(read_only=True)

    class Meta:
        model = Train
        fields = (
            "id",
            "name",
            "cargo_num",
            "places_in_cargo",
            "train_type",
            "image",
        )


class TrainImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Train
        fields = ("id", "image")


class JourneySerializer(serializers.ModelSerializer):
    route = serializers.SlugRelatedField(
        many=True, read_only=True, slug_field="full_direction"
    )
    departure_time = serializers.SlugRelatedField(
        many=True, read_only=True, slug_field="departure_time"
    )
    arrival_time = serializers.SlugRelatedField(
        many=True, read_only=True, slug_field="arrival_time"
    )
    class Meta:
        model = Journey
        fields = ("id", "route", "train",
                  "departure_time", "arrival_time")


class JourneySessionListSerializer(JourneySerializer):
    route_source = serializers.CharField(
        source="route.source.name", read_only=True
    )
    route_destination = serializers.CharField(
        source="route.destination.name", read_only=True
    )
    train_name = serializers.CharField(
        source="train.name", read_only=True
    )
    train_capacity = serializers.SerializerMethodField()
    tickets_available = serializers.IntegerField(read_only=True)

    class Meta:
        model = Journey
        fields = (
            "id",
            "route_source",
            "route_destination",
            "train_name",
            "train_capacity",
            "tickets_available",
            "departure_time",
            "arrival_time",
        )


class JourneyListSerializer(serializers.ModelSerializer):
    route_title = serializers.CharField(
        source="route.__str__", read_only=True
    )
    train_name = serializers.CharField(
        source="train.name", read_only=True
    )
    tickets_available = serializers.IntegerField(read_only=True)

    class Meta:
        model = Journey
        fields = (
            "id",
            "route_title",
            "train_name",
            "departure_time",
            "arrival_time",
            "tickets_available",
        )


class TicketSeatsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ticket
        fields = ("cargo", "seat")


class JourneyDetailSerializer(serializers.ModelSerializer):
    route = RouteListSerializer(read_only=True)
    train = TrainListSerializer(read_only=True)
    crew = CrewSerializer(many=True, read_only=True)
    taken_places = TicketSeatsSerializer(
        source="tickets", many=True, read_only=True
    )

    class Meta:
        model = Journey
        fields = (
            "id",
            "route",
            "train",
            "crew",
            "departure_time",
            "arrival_time",
            "taken_places",
        )


class TicketListSerializer(TicketSerializer):
    Journey = JourneySessionListSerializer(many=False, read_only=True)


class OrderSerializer(serializers.ModelSerializer):
    tickets = TicketSerializer(many=True, read_only=False, allow_empty=False)

    class Meta:
        model = Order
        fields = ("id", "tickets", "created_at", "user",)

    def create(self, validated_data):
        with transaction.atomic():
            tickets_data = validated_data.pop("tickets")
            order = Order.objects.create(**validated_data)
            for ticket_data in tickets_data:
                Ticket.objects.create(order=order, **ticket_data)
            return order


class OrderListSerializer(OrderSerializer):
    tickets = TicketListSerializer(many=True, read_only=True)

