import os
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import override_settings
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from apps.jobs.models import JobStatus, JobType, ProcessingJob
from apps.jobs.services import ProcessingJobService
from apps.shadowing.models import (
    ShadowingSegment,
    ShadowingVideo,
    UserShadowingSegment,
    UserShadowingStatus,
    UserShadowingVideo,
    VideoStatus,
)
from apps.shadowing.tests.fixtures import create_mock_video_file

User = get_user_model()


@override_settings(
    STORAGES={
        "default": {
            "BACKEND": "django.core.files.storage.InMemoryStorage",
        },
        "staticfiles": {
            "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
        },
    },
    CELERY_TASK_ALWAYS_EAGER=True,
    CELERY_TASK_EAGER_PROPAGATES=True,
)
class ShadowingAPITestBase(APITestCase):
    def setUp(self):
        self.admin_user = User.objects.create_superuser(
            username="shadowing_admin",
            password="adminpassword123",
            email="admin@shadowing.test",
        )
        self.user1 = User.objects.create_user(
            username="student_one",
            password="userpassword123",
            email="student1@shadowing.test",
        )
        self.user2 = User.objects.create_user(
            username="student_two",
            password="userpassword123",
            email="student2@shadowing.test",
        )

        # Create sample ready video
        self.ready_video = ShadowingVideo.objects.create(
            title="Japanese IT Standup Meeting",
            description="Daily scrum dialogue for Japanese IT engineers.",
            level="N3",
            language="ja",
            duration_seconds=120.0,
            file_size=10240,
            status=VideoStatus.READY,
            video_file=create_mock_video_file("standup.mp4"),
        )
        self.segment1 = ShadowingSegment.objects.create(
            video=self.ready_video,
            sequence=1,
            start_time=0.0,
            end_time=3.2,
            text="おはようございます。本日の進捗を報告します。",
            reading="おはようございます。ほんじつのしんちょくをほうこくします。",
            speaker="Tanaka",
        )
        self.segment2 = ShadowingSegment.objects.create(
            video=self.ready_video,
            sequence=2,
            start_time=3.5,
            end_time=7.0,
            text="APIの単体テストを実装中です。",
            reading="APIのたんたいてすとをじっそうちゅうです。",
            speaker="Tanaka",
        )

        # Non-ready video
        self.processing_video = ShadowingVideo.objects.create(
            title="Processing Video",
            description="Video being processed",
            level="N2",
            language="ja",
            status=VideoStatus.PROCESSING,
            video_file=create_mock_video_file("processing.mp4"),
        )


class ShadowingVideoPermissionsAndCRUDAPITests(ShadowingAPITestBase):
    def test_unauthenticated_cannot_list_videos(self):
        res = self.client.get("/api/shadowing/videos/")
        self.assertIn(res.status_code, [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN])

    def test_normal_user_lists_only_ready_videos(self):
        self.client.force_authenticate(user=self.user1)
        res = self.client.get("/api/shadowing/videos/")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        results = res.data["results"] if "results" in res.data else res.data
        titles = [item["title"] for item in results]
        self.assertIn("Japanese IT Standup Meeting", titles)
        self.assertNotIn("Processing Video", titles)

    def test_admin_lists_all_videos_including_non_ready(self):
        self.client.force_authenticate(user=self.admin_user)
        res = self.client.get("/api/shadowing/videos/")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        results = res.data["results"] if "results" in res.data else res.data
        titles = [item["title"] for item in results]
        self.assertIn("Japanese IT Standup Meeting", titles)
        self.assertIn("Processing Video", titles)

    def test_filtering_videos(self):
        self.client.force_authenticate(user=self.admin_user)
        res = self.client.get("/api/shadowing/videos/?status=ready")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        results = res.data["results"] if "results" in res.data else res.data
        for item in results:
            self.assertEqual(item["status"], "ready")

        res_level = self.client.get("/api/shadowing/videos/?level=N3")
        self.assertEqual(res_level.status_code, status.HTTP_200_OK)
        results_level = res_level.data["results"] if "results" in res_level.data else res_level.data
        for item in results_level:
            self.assertEqual(item["level"], "N3")

    def test_searching_videos(self):
        self.client.force_authenticate(user=self.user1)
        res = self.client.get("/api/shadowing/videos/?search=Standup")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        results = res.data["results"] if "results" in res.data else res.data
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["title"], "Japanese IT Standup Meeting")

    def test_normal_user_retrieve_ready_video(self):
        self.client.force_authenticate(user=self.user1)
        res = self.client.get(f"/api/shadowing/videos/{self.ready_video.id}/")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["title"], "Japanese IT Standup Meeting")

    def test_normal_user_cannot_retrieve_non_ready_video(self):
        self.client.force_authenticate(user=self.user1)
        res = self.client.get(f"/api/shadowing/videos/{self.processing_video.id}/")
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)

    def test_admin_retrieve_non_ready_video(self):
        self.client.force_authenticate(user=self.admin_user)
        res = self.client.get(f"/api/shadowing/videos/{self.processing_video.id}/")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["title"], "Processing Video")

    def test_normal_user_cannot_upload_video(self):
        self.client.force_authenticate(user=self.user1)
        video_file = create_mock_video_file("test.mp4")
        data = {"title": "User Upload Attempt", "video_file": video_file}
        res = self.client.post("/api/shadowing/videos/", data, format="multipart")
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    @patch("apps.shadowing.services.process_shadowing_video.delay")
    def test_admin_upload_video_success_dispatches_celery(self, mock_delay):
        self.client.force_authenticate(user=self.admin_user)
        video_file = create_mock_video_file("upload.mp4")
        data = {
            "title": "New Shadowing Lesson",
            "description": "Scrum sprint planning",
            "level": "N2",
            "language": "ja",
            "video_file": video_file,
        }
        with self.captureOnCommitCallbacks(execute=True):
            res = self.client.post("/api/shadowing/videos/", data, format="multipart")
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertIn("video", res.data)
        self.assertIn("job", res.data)
        self.assertEqual(res.data["video"]["status"], VideoStatus.UPLOAD)
        self.assertEqual(res.data["job"]["status"], JobStatus.QUEUED)

        # Verify Celery delay was queued
        mock_delay.assert_called_once()

    def test_upload_missing_file_rejected(self):
        self.client.force_authenticate(user=self.admin_user)
        res = self.client.post("/api/shadowing/videos/", {"title": "No File"}, format="multipart")
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_upload_missing_title_rejected(self):
        self.client.force_authenticate(user=self.admin_user)
        video_file = create_mock_video_file("upload.mp4")
        res = self.client.post("/api/shadowing/videos/", {"title": "", "video_file": video_file}, format="multipart")
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_upload_rejects_server_controlled_fields(self):
        self.client.force_authenticate(user=self.admin_user)
        video_file = create_mock_video_file("upload.mp4")
        data = {
            "title": "Hacked Video",
            "status": "ready",
            "video_file": video_file,
        }
        res = self.client.post("/api/shadowing/videos/", data, format="multipart")
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_normal_user_cannot_patch_video(self):
        self.client.force_authenticate(user=self.user1)
        res = self.client.patch(f"/api/shadowing/videos/{self.ready_video.id}/", {"title": "New Title"})
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_patch_safe_metadata(self):
        self.client.force_authenticate(user=self.admin_user)
        res = self.client.patch(
            f"/api/shadowing/videos/{self.ready_video.id}/",
            {"title": "Updated Standup Title", "description": "Updated description"},
            format="json",
        )
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.ready_video.refresh_from_db()
        self.assertEqual(self.ready_video.title, "Updated Standup Title")
        self.assertEqual(self.ready_video.description, "Updated description")

    def test_admin_patch_rejects_server_controlled_fields(self):
        self.client.force_authenticate(user=self.admin_user)
        res = self.client.patch(
            f"/api/shadowing/videos/{self.ready_video.id}/",
            {"status": "upload"},
            format="json",
        )
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    @patch("apps.shadowing.services.process_shadowing_video.delay")
    def test_admin_patch_file_replacement_creates_new_job_and_dispatches(self, mock_delay):
        self.client.force_authenticate(user=self.admin_user)
        new_file = create_mock_video_file("replacement.mp4")
        with self.captureOnCommitCallbacks(execute=True):
            res = self.client.patch(
                f"/api/shadowing/videos/{self.ready_video.id}/",
                {"video_file": new_file},
                format="multipart",
            )
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn("job", res.data)
        self.ready_video.refresh_from_db()
        self.assertEqual(self.ready_video.status, VideoStatus.UPLOAD)
        mock_delay.assert_called_once()

    def test_admin_patch_file_replacement_conflict_when_processing(self):
        self.client.force_authenticate(user=self.admin_user)
        new_file = create_mock_video_file("replacement.mp4")
        res = self.client.patch(
            f"/api/shadowing/videos/{self.processing_video.id}/",
            {"video_file": new_file},
            format="multipart",
        )
        self.assertEqual(res.status_code, status.HTTP_409_CONFLICT)

    def test_normal_user_cannot_delete_video(self):
        self.client.force_authenticate(user=self.user1)
        res = self.client.delete(f"/api/shadowing/videos/{self.ready_video.id}/")
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_delete_video_success(self):
        self.client.force_authenticate(user=self.admin_user)
        res = self.client.delete(f"/api/shadowing/videos/{self.ready_video.id}/")
        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(ShadowingVideo.objects.filter(id=self.ready_video.id).exists())
        # Verify segments were cascade deleted
        self.assertFalse(ShadowingSegment.objects.filter(video_id=self.ready_video.id).exists())

    def test_admin_delete_video_conflict_when_processing(self):
        self.client.force_authenticate(user=self.admin_user)
        res = self.client.delete(f"/api/shadowing/videos/{self.processing_video.id}/")
        self.assertEqual(res.status_code, status.HTTP_409_CONFLICT)
        self.assertTrue(ShadowingVideo.objects.filter(id=self.processing_video.id).exists())


class ShadowingProcessingStatusAPITests(ShadowingAPITestBase):
    def setUp(self):
        super().setUp()
        self.job = ProcessingJobService.create_job(
            user=self.admin_user,
            job_type=JobType.VIDEO_PROCESSING,
            result={"video_id": str(self.ready_video.id)},
        )
        ProcessingJobService.mark_processing(self.job, progress=40, current_step="transcribing")

    def test_unauthenticated_cannot_access_processing_status(self):
        res = self.client.get(f"/api/shadowing/videos/{self.ready_video.id}/processing/")
        self.assertIn(res.status_code, [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN])

    def test_normal_user_cannot_access_processing_status(self):
        self.client.force_authenticate(user=self.user1)
        res = self.client.get(f"/api/shadowing/videos/{self.ready_video.id}/processing/")
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_access_processing_status_success(self):
        self.client.force_authenticate(user=self.admin_user)
        res = self.client.get(f"/api/shadowing/videos/{self.ready_video.id}/processing/")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["job_id"], str(self.job.id))
        self.assertEqual(res.data["progress"], 40)
        self.assertEqual(res.data["current_step"], "transcribing")

    def test_admin_access_prefers_active_job(self):
        self.client.force_authenticate(user=self.admin_user)
        # Old completed job
        old_job = ProcessingJobService.create_job(
            user=self.admin_user,
            job_type=JobType.VIDEO_PROCESSING,
            result={"video_id": str(self.ready_video.id)},
        )
        ProcessingJobService.mark_processing(old_job)
        ProcessingJobService.mark_completed(old_job, result={"done": True})

        # New queued job
        active_job = ProcessingJobService.create_job(
            user=self.admin_user,
            job_type=JobType.VIDEO_PROCESSING,
            result={"video_id": str(self.ready_video.id)},
        )
        res = self.client.get(f"/api/shadowing/videos/{self.ready_video.id}/processing/")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["job_id"], str(active_job.id))

    def test_admin_access_not_found_returns_404(self):
        self.client.force_authenticate(user=self.admin_user)
        video_no_job = ShadowingVideo.objects.create(
            title="No Job Video",
            status=VideoStatus.READY,
        )
        res = self.client.get(f"/api/shadowing/videos/{video_no_job.id}/processing/")
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)


class ShadowingSegmentsAPITests(ShadowingAPITestBase):
    def test_unauthenticated_cannot_list_segments(self):
        res = self.client.get(f"/api/shadowing/videos/{self.ready_video.id}/segments/")
        self.assertIn(res.status_code, [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN])

    def test_authenticated_user_can_list_segments_for_ready_video(self):
        self.client.force_authenticate(user=self.user1)
        res = self.client.get(f"/api/shadowing/videos/{self.ready_video.id}/segments/")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 2)
        self.assertEqual(res.data[0]["sequence"], 1)
        self.assertEqual(res.data[1]["sequence"], 2)

    def test_non_ready_video_segments_return_404_for_normal_user(self):
        self.client.force_authenticate(user=self.user1)
        res = self.client.get(f"/api/shadowing/videos/{self.processing_video.id}/segments/")
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)

    def test_admin_can_view_segments_for_any_video(self):
        self.client.force_authenticate(user=self.admin_user)
        res = self.client.get(f"/api/shadowing/videos/{self.processing_video.id}/segments/")
        self.assertEqual(res.status_code, status.HTTP_200_OK)


class ShadowingEnrollmentAPITests(ShadowingAPITestBase):
    def test_unauthenticated_cannot_enroll(self):
        res = self.client.post(f"/api/shadowing/videos/{self.ready_video.id}/enroll/")
        self.assertIn(res.status_code, [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN])

    def test_enroll_into_ready_video_success(self):
        self.client.force_authenticate(user=self.user1)
        res = self.client.post(f"/api/shadowing/videos/{self.ready_video.id}/enroll/")
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertTrue(res.data["enrolled"])
        self.assertEqual(res.data["video_id"], str(self.ready_video.id))

        # Verify DB records created
        self.assertTrue(UserShadowingVideo.objects.filter(user=self.user1, video=self.ready_video).exists())
        self.assertEqual(
            UserShadowingSegment.objects.filter(user_video__user=self.user1, segment__video=self.ready_video).count(),
            2,
        )

    def test_enroll_is_idempotent(self):
        self.client.force_authenticate(user=self.user1)
        # First enroll
        res1 = self.client.post(f"/api/shadowing/videos/{self.ready_video.id}/enroll/")
        self.assertEqual(res1.status_code, status.HTTP_201_CREATED)

        # Second enroll
        res2 = self.client.post(f"/api/shadowing/videos/{self.ready_video.id}/enroll/")
        self.assertEqual(res2.status_code, status.HTTP_200_OK)
        self.assertTrue(res2.data["enrolled"])

        # No duplicate records
        self.assertEqual(UserShadowingVideo.objects.filter(user=self.user1, video=self.ready_video).count(), 1)
        self.assertEqual(
            UserShadowingSegment.objects.filter(user_video__user=self.user1, segment__video=self.ready_video).count(),
            2,
        )

    def test_cannot_enroll_into_non_ready_video(self):
        self.client.force_authenticate(user=self.user1)
        res = self.client.post(f"/api/shadowing/videos/{self.processing_video.id}/enroll/")
        # Normal user cannot even see non-ready video -> 404
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)

    def test_cross_user_enrollment_isolation(self):
        self.client.force_authenticate(user=self.user1)
        self.client.post(f"/api/shadowing/videos/{self.ready_video.id}/enroll/")

        # User 2 is not enrolled
        self.assertFalse(UserShadowingVideo.objects.filter(user=self.user2, video=self.ready_video).exists())


class MyShadowingAPITests(ShadowingAPITestBase):
    def setUp(self):
        super().setUp()
        self.client.force_authenticate(user=self.user1)
        self.client.post(f"/api/shadowing/videos/{self.ready_video.id}/enroll/")

    def test_unauthenticated_cannot_access_my_shadowing(self):
        self.client.logout()
        res = self.client.get("/api/my/shadowing/")
        self.assertIn(res.status_code, [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN])

    def test_my_shadowing_list_returns_enrolled_videos(self):
        self.client.force_authenticate(user=self.user1)
        res = self.client.get("/api/my/shadowing/")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        results = res.data["results"] if "results" in res.data else res.data
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["video_id"], str(self.ready_video.id))
        self.assertEqual(results[0]["completed_segments"], 0)
        self.assertEqual(results[0]["total_segments"], 2)
        self.assertEqual(results[0]["percentage"], 0.0)

    def test_my_shadowing_detail_by_video_id(self):
        self.client.force_authenticate(user=self.user1)
        res = self.client.get(f"/api/my/shadowing/{self.ready_video.id}/")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn("video", res.data)
        self.assertIn("progress", res.data)
        self.assertIn("segments", res.data)
        self.assertEqual(len(res.data["segments"]), 2)
        self.assertFalse(res.data["segments"][0]["is_completed"])

    def test_my_shadowing_cross_user_isolation(self):
        # User 2 has not enrolled
        self.client.force_authenticate(user=self.user2)
        res_list = self.client.get("/api/my/shadowing/")
        self.assertEqual(res_list.status_code, status.HTTP_200_OK)
        results = res_list.data["results"] if "results" in res_list.data else res_list.data
        self.assertEqual(len(results), 0)

        # User 2 cannot access User 1's enrolled video
        res_detail = self.client.get(f"/api/my/shadowing/{self.ready_video.id}/")
        self.assertEqual(res_detail.status_code, status.HTTP_404_NOT_FOUND)

    def test_zero_segments_video_progress_is_zero(self):
        zero_seg_video = ShadowingVideo.objects.create(
            title="Zero Segments Video",
            status=VideoStatus.READY,
        )
        self.client.force_authenticate(user=self.user1)
        self.client.post(f"/api/shadowing/videos/{zero_seg_video.id}/enroll/")
        res = self.client.get(f"/api/my/shadowing/{zero_seg_video.id}/")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["progress"]["percentage"], 0.0)
        self.assertEqual(res.data["progress"]["total_segments"], 0)


class SegmentCompletionAPITests(ShadowingAPITestBase):
    def setUp(self):
        super().setUp()
        self.client.force_authenticate(user=self.user1)
        self.client.post(f"/api/shadowing/videos/{self.ready_video.id}/enroll/")

    def test_unauthenticated_cannot_complete_segment(self):
        self.client.logout()
        res = self.client.post(
            f"/api/my/shadowing/{self.ready_video.id}/segments/{self.segment1.id}/complete/"
        )
        self.assertIn(res.status_code, [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN])

    def test_complete_segment_without_enrollment_rejected(self):
        other_ready_video = ShadowingVideo.objects.create(
            title="Another Video",
            status=VideoStatus.READY,
        )
        other_segment = ShadowingSegment.objects.create(
            video=other_ready_video,
            sequence=1,
            start_time=0.0,
            end_time=2.0,
            text="Test",
        )
        self.client.force_authenticate(user=self.user1)
        res = self.client.post(
            f"/api/my/shadowing/{other_ready_video.id}/segments/{other_segment.id}/complete/"
        )
        # Not enrolled in other_ready_video -> 404 from get_object
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)

    def test_complete_first_segment_updates_partial_progress(self):
        self.client.force_authenticate(user=self.user1)
        res = self.client.post(
            f"/api/my/shadowing/{self.ready_video.id}/segments/{self.segment1.id}/complete/"
        )
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertTrue(res.data["completed"])
        self.assertEqual(res.data["completed_segments"], 1)
        self.assertEqual(res.data["total_segments"], 2)
        self.assertEqual(res.data["percentage"], 50.0)
        self.assertEqual(res.data["video_status"], UserShadowingStatus.ACTIVE)

    def test_complete_segment_is_idempotent_and_preserves_timestamp(self):
        self.client.force_authenticate(user=self.user1)
        res1 = self.client.post(
            f"/api/my/shadowing/{self.ready_video.id}/segments/{self.segment1.id}/complete/"
        )
        completed_at_1 = res1.data["completed_at"]

        # Call again
        res2 = self.client.post(
            f"/api/my/shadowing/{self.ready_video.id}/segments/{self.segment1.id}/complete/"
        )
        self.assertEqual(res2.status_code, status.HTTP_200_OK)
        self.assertEqual(res2.data["completed_at"], completed_at_1)
        self.assertEqual(res2.data["completed_segments"], 1)

    def test_cross_video_segment_completion_returns_404(self):
        other_video = ShadowingVideo.objects.create(
            title="Video Two",
            status=VideoStatus.READY,
        )
        other_segment = ShadowingSegment.objects.create(
            video=other_video,
            sequence=1,
            start_time=0.0,
            end_time=1.0,
            text="Foreign segment",
        )
        self.client.force_authenticate(user=self.user1)
        # Attempt to complete other_segment on self.ready_video
        res = self.client.post(
            f"/api/my/shadowing/{self.ready_video.id}/segments/{other_segment.id}/complete/"
        )
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)

    def test_completing_all_segments_marks_video_completed(self):
        self.client.force_authenticate(user=self.user1)
        # Complete segment 1
        self.client.post(
            f"/api/my/shadowing/{self.ready_video.id}/segments/{self.segment1.id}/complete/"
        )
        # Complete segment 2
        res = self.client.post(
            f"/api/my/shadowing/{self.ready_video.id}/segments/{self.segment2.id}/complete/"
        )
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["completed_segments"], 2)
        self.assertEqual(res.data["total_segments"], 2)
        self.assertEqual(res.data["percentage"], 100.0)
        self.assertEqual(res.data["video_status"], UserShadowingStatus.COMPLETED)

        user_video = UserShadowingVideo.objects.get(user=self.user1, video=self.ready_video)
        self.assertEqual(user_video.status, UserShadowingStatus.COMPLETED)
        self.assertIsNotNone(user_video.completed_at)

    def test_completion_does_not_affect_other_user(self):
        # User 2 enrolls
        self.client.force_authenticate(user=self.user2)
        self.client.post(f"/api/shadowing/videos/{self.ready_video.id}/enroll/")

        # User 1 completes segment 1
        self.client.force_authenticate(user=self.user1)
        self.client.post(
            f"/api/my/shadowing/{self.ready_video.id}/segments/{self.segment1.id}/complete/"
        )

        # Check User 2 progress is still 0
        self.client.force_authenticate(user=self.user2)
        res = self.client.get(f"/api/my/shadowing/{self.ready_video.id}/")
        self.assertEqual(res.data["progress"]["percentage"], 0.0)
        self.assertEqual(res.data["progress"]["completed_segments"], 0)


class AdditionalShadowingAPITests(ShadowingAPITestBase):
    def test_unauthenticated_cannot_retrieve_video_detail(self):
        res = self.client.get(f"/api/shadowing/videos/{self.ready_video.id}/")
        self.assertIn(res.status_code, [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN])

    def test_unauthenticated_cannot_patch_video(self):
        res = self.client.patch(f"/api/shadowing/videos/{self.ready_video.id}/", {"title": "Hack"})
        self.assertIn(res.status_code, [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN])

    def test_unauthenticated_cannot_delete_video(self):
        res = self.client.delete(f"/api/shadowing/videos/{self.ready_video.id}/")
        self.assertIn(res.status_code, [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN])

    def test_admin_cannot_upload_invalid_video_extension(self):
        self.client.force_authenticate(user=self.admin_user)
        bad_file = create_mock_video_file("virus.exe", content=b"MZ\x90\x00")
        res = self.client.post("/api/shadowing/videos/", {"title": "Bad File", "video_file": bad_file}, format="multipart")
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_admin_cannot_upload_empty_video_file(self):
        self.client.force_authenticate(user=self.admin_user)
        empty_file = create_mock_video_file("empty.mp4", content=b"")
        res = self.client.post("/api/shadowing/videos/", {"title": "Empty File", "video_file": empty_file}, format="multipart")
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_admin_patch_metadata_preserves_internal_job_id(self):
        self.client.force_authenticate(user=self.admin_user)
        self.ready_video.metadata = {"job_id": "test-job-uuid-1234", "custom": "old"}
        self.ready_video.save(update_fields=["metadata"])

        res = self.client.patch(
            f"/api/shadowing/videos/{self.ready_video.id}/",
            {"metadata": {"custom": "new"}},
            format="json",
        )
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.ready_video.refresh_from_db()
        self.assertEqual(self.ready_video.metadata.get("custom"), "new")
        self.assertEqual(self.ready_video.metadata.get("job_id"), "test-job-uuid-1234")

    def test_admin_delete_nonexistent_video_returns_404(self):
        import uuid
        self.client.force_authenticate(user=self.admin_user)
        res = self.client.delete(f"/api/shadowing/videos/{uuid.uuid4()}/")
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)

    def test_admin_access_processing_status_with_job_id_in_metadata(self):
        self.client.force_authenticate(user=self.admin_user)
        job = ProcessingJobService.create_job(
            user=self.admin_user,
            job_type=JobType.VIDEO_PROCESSING,
            result={},
        )
        video = ShadowingVideo.objects.create(
            title="Metadata Job Video",
            status=VideoStatus.READY,
            metadata={"job_id": str(job.id)},
        )
        res = self.client.get(f"/api/shadowing/videos/{video.id}/processing/")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["job_id"], str(job.id))

    def test_normal_user_cannot_access_segments_nonexistent_video(self):
        import uuid
        self.client.force_authenticate(user=self.user1)
        res = self.client.get(f"/api/shadowing/videos/{uuid.uuid4()}/segments/")
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)

    def test_openapi_schema_contains_shadowing_endpoints(self):
        from drf_spectacular.generators import SchemaGenerator
        generator = SchemaGenerator(title="Test API")
        schema = generator.get_schema(request=None, public=True)
        paths = schema.get("paths", {})
        self.assertIn("/api/shadowing/videos/", paths)
        self.assertIn("/api/shadowing/videos/{id}/", paths)
        self.assertIn("/api/shadowing/videos/{id}/processing/", paths)
        self.assertIn("/api/shadowing/videos/{id}/segments/", paths)
        self.assertIn("/api/shadowing/videos/{id}/enroll/", paths)
        self.assertIn("/api/my/shadowing/", paths)
        self.assertIn("/api/my/shadowing/{id}/", paths)
        self.assertIn("/api/my/shadowing/{id}/segments/{segment_id}/complete/", paths)

        # Verify multipart/form-data for upload
        post_op = paths["/api/shadowing/videos/"]["post"]
        request_body = post_op.get("requestBody", {})
        content = request_body.get("content", {})
        self.assertIn("multipart/form-data", content)
        req_schema = content["multipart/form-data"]["schema"]
        if "$ref" in req_schema:
            ref_name = req_schema["$ref"].split("/")[-1]
            props = schema["components"]["schemas"][ref_name]["properties"]
        else:
            props = req_schema["properties"]
        self.assertEqual(props["video_file"]["type"], "string")
        self.assertEqual(props["video_file"]["format"], "binary")
