from django.db import models


class WikipediaEdit(models.Model):
    """
    Model to store processed real-time Wikipedia edit events.
    """
    # Core Data Fields
    article_title = models.CharField(max_length=500, db_index=True, help_text="Title of the article edited.")
    user_name = models.CharField(max_length=200, db_index=True, help_text="User who made the edit.")
    edit_timestamp = models.DateTimeField(db_index=True, help_text="The time the edit occurred.")

    # Edit Metadata
    byte_change = models.IntegerField(default=0, help_text="Change in bytes (+ or -) of the article size.")
    is_minor = models.BooleanField(default=False, help_text="True if the edit was marked as minor.")

    # Source & Link
    edit_url = models.URLField(max_length=1000, help_text="URL linking to the edit/diff.")

    class Meta:
        verbose_name = "Wikipedia Edit"
        verbose_name_plural = "Wikipedia Edits"
        ordering = ['-edit_timestamp']

    def __str__(self):
        return f"{self.user_name} edited '{self.article_title}' at {self.edit_timestamp.strftime('%Y-%m-%d %H:%M:%S')}"
