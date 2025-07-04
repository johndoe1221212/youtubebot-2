import random
import time
import pickle
import os
import string  # Added import for random characters
from datetime import datetime
import pytz  # Added for timezone handling

from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.errors import HttpError  # Corrected this line

# YouTube Data API v3 scopes
SCOPES = ['https://www.googleapis.com/auth/youtube.force-ssl']

# Updated Channel ID (New target channel ID)
CHANNEL_ID = 'UCm-X6o81nRsXQTmqpyArkBQ'

# Define a set of random characters (letters, digits, and special characters)
RANDOM_CHARACTERS = string.ascii_letters + string.digits + "!@#$%^&*()"

# Define your timezone (GMT+1)
LOCAL_TIMEZONE = pytz.timezone("Africa/Casablanca")

def get_authenticated_service():
    creds = None
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('client_secret.json', SCOPES)
            creds = flow.run_local_server(port=0)
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)
    return build('youtube', 'v3', credentials=creds)

def get_most_recent_video(youtube, channel_id):
    try:
        request = youtube.search().list(
            part="snippet",
            channelId=channel_id,
            order="date",
            maxResults=19
        )
        response = request.execute()

        # Check if any items are returned
        if not response['items']:
            print(f"No videos found for channel {channel_id}.")
            return None  # Return None or handle this case accordingly

        video_id = response['items'][0]['id']['videoId']
        return video_id

    except HttpError as e:
        print(f"HttpError occurred: {e}")
        return None
    except Exception as e:
        print(f"An error occurred: {e}")
        return None

def convert_utc_to_local(utc_time_str):
    """Convert UTC time string to local time (GMT+1)."""
    # Parse the UTC time string into a datetime object
    utc_time = datetime.strptime(utc_time_str, "%Y-%m-%dT%H:%M:%SZ")
    
    # Convert the time to local timezone (GMT+1)
    local_time = pytz.utc.localize(utc_time).astimezone(LOCAL_TIMEZONE)
    return local_time

def main():
    youtube = get_authenticated_service()
    try:
        # Get the most recent video from the updated channel
        video_id = get_most_recent_video(youtube, CHANNEL_ID)
        if not video_id:
            print("No video found. Exiting.")
            return
        
        print(f"Most recent video ID: {video_id}")

        # Fetch the top 19 comments from the video
        request = youtube.commentThreads().list(
            part="snippet",
            videoId=video_id,
            maxResults=19,
            order="time"
        )
        response = request.execute()

    except HttpError as e:
        print(f"Failed to fetch comments: {e}")
        return

    # Loop through the comments and reply to each one
    for item in response.get('items', []):
        comment = item['snippet']['topLevelComment']
        comment_id = comment['id']
        
        # Check if the comment already has replies
        total_replies = item['snippet']['totalReplyCount']
        if total_replies > 0:
            print(f"Skipping comment ID {comment_id} because it already has replies.")
            continue  # Skip this comment and move to the next one
        
        # Convert the comment's published time to local time (GMT+1)
        published_at = comment['snippet']['publishedAt']
        local_published_time = convert_utc_to_local(published_at)
        print(f"Comment ID {comment_id} was published at {local_published_time} (local time).")

        # Add two random characters to the reply text
        random_characters = ''.join(random.choice(RANDOM_CHARACTERS) for _ in range(2))  # Pick two random characters
        reply_text = f"⬆️ I give.away R0B.UX for FR.EE! {random_characters}"
        
        print(f"Replying to comment ID: {comment_id} with text: {reply_text}")
        
        try:
            reply_response = youtube.comments().insert(
                part="snippet",
                body={
                    "snippet": {
                        "parentId": comment_id,
                        "textOriginal": reply_text
                    }
                }
            ).execute()
            print(f"Success: {reply_response.get('id')} - Replied to comment ID {comment_id}")
        except HttpError as e:
            error_content = e.content.decode() if hasattr(e, 'content') else str(e)
            print(f"HttpError replying to comment {comment_id}: {error_content}")
        except Exception as e:
            print(f"Error replying to comment {comment_id}: {e}")
        
        # Wait between 20-60 seconds before replying to the next comment
        wait_time = random.randint(20, 60)
        print(f"Waiting {wait_time} seconds before next reply...\n")
        time.sleep(wait_time)

if __name__ == "__main__":
    main()
