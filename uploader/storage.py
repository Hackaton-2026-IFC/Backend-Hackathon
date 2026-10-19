from cloudinary_storage.storage import MediaCloudinaryStorage as BaseMediaCloudinaryStorage


class MediaCloudinaryStorage(BaseMediaCloudinaryStorage):
    """Choose the Cloudinary resource type based on the media upload path."""

    def _get_resource_type(self, name):
        path_parts = name.replace("\\", "/").lower().split("/")
        if "videos" in path_parts:
            return "video"
        return super()._get_resource_type(name)
