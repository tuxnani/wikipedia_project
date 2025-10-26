import time
import requests
import json
from datetime import datetime, timedelta
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
# UPDATED IMPORT PATH
from wiki_stream_app.models import WikipediaEdit

# Wikimedia EventStream URL for recent changes on English Wikipedia
WIKIMEDIA_STREAM_URL = "https://stream.wikimedia.org/v2/stream/recentchange"


class Command(BaseCommand):
    help = 'Initiates a data stream capture and processing of Wikipedia edits for a defined duration.'

    def add_arguments(self, parser):
        # Allow the user to specify the duration in seconds
        parser.add_argument(
            '--duration',
            type=int,
            default=600,  # Default to 10 minutes (600 seconds)
            help='Duration (in seconds) to run the stream capture. E.g., 3600 for 1 hour.',
        )

    def handle(self, *args, **options):
        duration_seconds = options['duration']

        # Calculate the end time
        end_time = timezone.now() + timedelta(seconds=duration_seconds)
        self.stdout.write(self.style.NOTICE(
            f"Starting Wikipedia edit stream capture for {duration_seconds} seconds. Will stop at {end_time.strftime('%Y-%m-%d %H:%M:%S')}."
        ))

        # Use requests.get with stream=True for continuous reading
        try:
            # Setting up a continuous GET request to the SSE endpoint
            with requests.get(WIKIMEDIA_STREAM_URL, stream=True) as response:
                if response.status_code != 200:
                    raise CommandError(f"Failed to connect to stream. Status code: {response.status_code}")

                # Iterate over lines in the stream
                for line in response.iter_lines(decode_unicode=True):

                    # Check if the duration has expired
                    if timezone.now() > end_time:
                        self.stdout.write(self.style.SUCCESS(
                            f"\nCapture duration of {duration_seconds} seconds completed. Stopping stream."
                        ))
                        break  # Exit the loop and stop the command

                    # SSE events are prefixed with "data:"
                    if line.startswith('data:'):
                        try:
                            # Extract the JSON payload
                            data_string = line.replace('data:', '').strip()
                            if not data_string:
                                continue

                            event_data = json.loads(data_string)

                            # Filter for English Wikipedia edits (domain is 'en.wikipedia.org')
                            # and check if it is a 'edit' type (rc_type == 0)
                            if event_data.get('meta', {}).get('domain') == 'en.wikipedia.org' and event_data.get(
                                    'type') == 'edit':
                                # Process and save the edit
                                self.process_edit_event(event_data)

                        except json.JSONDecodeError as e:
                            self.stdout.write(self.style.WARNING(f"Could not decode JSON: {e}"))
                        except Exception as e:
                            self.stdout.write(self.style.ERROR(f"An unexpected error occurred during processing: {e}"))

        except requests.exceptions.RequestException as e:
            raise CommandError(f"Network error during stream connection: {e}")

    def process_edit_event(self, data):
        """Extracts relevant fields from the edit event and saves it to the database."""

        # Extract necessary data points
        title = data.get('title')
        user = data.get('user')
        timestamp_str = data.get('timestamp')  # Unix timestamp
        byte_change = data.get('length', {}).get('new', 0) - data.get('length', {}).get('old', 0)
        is_minor = data.get('minor', False)

        # Construct the edit URL
        # The 'server_name' and 'page_title' can be used to construct the URL to the diff

        # NOTE: The 'meta' object contains the URI, but let's use a simpler construction
        # since recentchange doesn't always include a direct diff URL in the root object.
        # We will use the 'server_url' + 'wiki/' + 'title' as a page link proxy.
        edit_url = f"{data.get('server_url', 'https://en.wikipedia.org')}/wiki/{title.replace(' ', '_')}"

        # Convert timestamp (seconds since epoch) to datetime object
        try:
            edit_datetime = datetime.fromtimestamp(timestamp_str, tz=timezone.utc)
        except (TypeError, ValueError):
            self.stdout.write(self.style.WARNING(f"Skipping edit due to invalid timestamp: {timestamp_str}"))
            return

        # Save the processed data
        WikipediaEdit.objects.create(
            article_title=title,
            user_name=user,
            edit_timestamp=edit_datetime,
            byte_change=byte_change,
            is_minor=is_minor,
            edit_url=edit_url
        )

        self.stdout.write(self.style.SUCCESS(
            f"Saved: '{title}' by {user} ({byte_change} bytes)"
        ))
