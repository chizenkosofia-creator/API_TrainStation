import os
import tempfile
from PIL import Image

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from rest_framework import status
from rest_framework.test import APIClient

from stations.models import Train, TrainType, Station, Route, Journey
from stations.serializers import TrainListSerializer, TrainDetailSerializer

TRAIN_URL = reverse("train_station:train-list")
JOURNEY_URL = reverse("train_station:journey-list")


def sample_train_type(**params):
    defaults = {"name": "Express"}
    defaults.update(params)
    return TrainType.objects.create(**defaults)


def sample_train(**params):
    train_type = sample_train_type()
    defaults = {
        "name": "Intercity 101",
        "cargo_num": 10,
        "places_in_cargo": 50,
        "train_type": train_type,
    }
    defaults.update(params)
    return Train.objects.create(**defaults)


def sample_journey(**params):
    source = Station.objects.create(
        name="Kyiv", latitude=50.4501, longitude=30.5234
    )
    destination = Station.objects.create(
        name="Lviv", latitude=49.8397, longitude=24.0297
    )
    route = Route.objects.create(
        source=source, destination=destination, distance=540
    )
    train = sample_train()

    defaults = {
        "route": route,
        "train": train,
        "departure_time": "2026-10-23 10:00:00",
        "arrival_time": "2026-10-23 16:00:00",
    }
    defaults.update(params)
    return Journey.objects.create(**defaults)


def image_upload_url(train_id):
    """Return URL for train image upload"""
    return reverse("train_station:train-upload-image", args=[train_id])


def detail_url(train_id):
    return reverse("train_station:train-detail", args=[train_id])


class UnauthenticatedTrainApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        res = self.client.get(TRAIN_URL)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class AuthenticatedTrainApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            "test@test.com",
            "testpass",
        )
        self.client.force_authenticate(self.user)

    def test_list_trains(self):
        sample_train()
        sample_train(name="Regional Express")

        res = self.client.get(TRAIN_URL)

        trains = Train.objects.order_by("id")
        serializer = TrainListSerializer(trains, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_filter_trains_by_train_type(self):
        type1 = sample_train_type(name="High Speed")
        type2 = sample_train_type(name="Night Express")

        train1 = sample_train(name="Train 1", train_type=type1)
        train2 = sample_train(name="Train 2", train_type=type2)
        train3 = sample_train(name="Train 3")

        res = self.client.get(TRAIN_URL, {"train_type": type1.id})

        serializer1 = TrainListSerializer(train1)
        serializer2 = TrainListSerializer(train2)
        serializer3 = TrainListSerializer(train3)

        self.assertIn(serializer1.data, res.data)
        self.assertNotIn(serializer2.data, res.data)
        self.assertNotIn(serializer3.data, res.data)

    def test_filter_trains_by_name(self):
        train1 = sample_train(name="Intercity")
        train2 = sample_train(name="Night Intercity")
        train3 = sample_train(name="Regional")

        res = self.client.get(TRAIN_URL, {"name": "intercity"})

        serializer1 = TrainListSerializer(train1)
        serializer2 = TrainListSerializer(train2)
        serializer3 = TrainListSerializer(train3)

        self.assertIn(serializer1.data, res.data)
        self.assertIn(serializer2.data, res.data)
        self.assertNotIn(serializer3.data, res.data)

    def test_retrieve_train_detail(self):
        train = sample_train()

        url = detail_url(train.id)
        res = self.client.get(url)

        serializer = TrainDetailSerializer(train)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_create_train_forbidden(self):
        train_type = sample_train_type()
        payload = {
            "name": "Express",
            "cargo_num": 10,
            "places_in_cargo": 60,
            "train_type": train_type.id,
        }
        res = self.client.post(TRAIN_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)


class AdminTrainApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            "admin@admin.com", "testpass", is_staff=True
        )
        self.client.force_authenticate(self.user)

    def test_create_train(self):
        train_type = sample_train_type()
        payload = {
            "name": "Fast Train",
            "cargo_num": 12,
            "places_in_cargo": 40,
            "train_type": train_type.id,
        }
        res = self.client.post(TRAIN_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        train = Train.objects.get(id=res.data["id"])
        self.assertEqual(payload["name"], train.name)
        self.assertEqual(payload["cargo_num"], train.cargo_num)
        self.assertEqual(payload["places_in_cargo"], train.places_in_cargo)
        self.assertEqual(payload["train_type"], train.train_type.id)


class TrainImageUploadTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_superuser(
            "admin@myproject.com", "password"
        )
        self.client.force_authenticate(self.user)
        self.train = sample_train()
        self.journey = sample_journey(train=self.train)

    def tearDown(self):
        self.train.image.delete()

    def test_upload_image_to_train(self):
        """Test uploading an image to train"""
        url = image_upload_url(self.train.id)
        with tempfile.NamedTemporaryFile(suffix=".jpg") as ntf:
            img = Image.new("RGB", (10, 10))
            img.save(ntf, format="JPEG")
            ntf.seek(0)
            res = self.client.post(url, {"image": ntf}, format="multipart")
        self.train.refresh_from_db()

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn("image", res.data)
        self.assertTrue(os.path.exists(self.train.image.path))

    def test_upload_image_bad_request(self):
        """Test uploading an invalid image"""
        url = image_upload_url(self.train.id)
        res = self.client.post(url, {"image": "not image"}, format="multipart")

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_post_image_to_train_list_should_not_work(self):
        url = TRAIN_URL
        train_type = sample_train_type()
        with tempfile.NamedTemporaryFile(suffix=".jpg") as ntf:
            img = Image.new("RGB", (10, 10))
            img.save(ntf, format="JPEG")
            ntf.seek(0)
            res = self.client.post(
                url,
                {
                    "name": "Title",
                    "cargo_num": 5,
                    "places_in_cargo": 20,
                    "train_type": train_type.id,
                    "image": ntf,
                },
                format="multipart",
            )

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        train = Train.objects.get(name="Title")
        self.assertFalse(train.image)

    def test_image_url_is_shown_on_train_detail(self):
        url = image_upload_url(self.train.id)
        with tempfile.NamedTemporaryFile(suffix=".jpg") as ntf:
            img = Image.new("RGB", (10, 10))
            img.save(ntf, format="JPEG")
            ntf.seek(0)
            self.client.post(url, {"image": ntf}, format="multipart")
        res = self.client.get(detail_url(self.train.id))

        self.assertIn("image", res.data)

    def test_image_url_is_shown_on_train_list(self):
        url = image_upload_url(self.train.id)
        with tempfile.NamedTemporaryFile(suffix=".jpg") as ntf:
            img = Image.new("RGB", (10, 10))
            img.save(ntf, format="JPEG")
            ntf.seek(0)
            self.client.post(url, {"image": ntf}, format="multipart")
        res = self.client.get(TRAIN_URL)

        self.assertIn("image", res.data[0].keys())

    def test_put_train_not_allowed(self):
        train_type = sample_train_type()
        payload = {
            "name": "New name",
            "cargo_num": 8,
            "places_in_cargo": 45,
            "train_type": train_type.id,
        }

        train = sample_train()
        url = detail_url(train.id)

        res = self.client.put(url, payload)

        self.assertEqual(res.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_delete_train_not_allowed(self):
        train = sample_train()
        url = detail_url(train.id)

        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
