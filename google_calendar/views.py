from django.shortcuts import redirect
from django.views import View
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.errors import HttpError
from googleapiclient.discovery import build
from rest_framework.response import Response
from rest_framework.views import APIView
import os

# Create your views here.
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'


class GoogleCalendarInitView(View):
    def get(self, request):
        flow = InstalledAppFlow.from_client_secrets_file(
            'client_secret.json',
            scopes=['https://www.googleapis.com/auth/calendar.events'],
        )

        flow.redirect_uri = 'https://googlecalendar.mdshahzar.repl.co/rest/v1/calendar/redirect/'

        authorization_url, state = flow.authorization_url(
            access_type='offline',
            include_granted_scopes='true',
        )

        request.session['state'] = state
        return redirect(authorization_url)


class GoogleCalendarRedirectView(APIView):
    def get(self, request, *args, **kwargs):

        state = request.GET.get('state')
        if not state:
            return Response(status=400,
                            data={'message': 'Invalid state parameter'})

        flow = InstalledAppFlow.from_client_secrets_file(
            'client_secret.json',
            scopes=['https://www.googleapis.com/auth/calendar.events'],
            state=state,
        )
        flow.redirect_uri = 'https://googlecalendar.mdshahzar.repl.co/rest/v1/calendar/redirect/'

        try:
            authorization_response = request.build_absolute_uri()
            flow.fetch_token(authorization_response=authorization_response)
        except HttpError as error:
            return Response(status=400,
                            data={'message': f'An error occured: {error}'})

        try:
            service = build('calendar',
                            'v3',
                            credentials=flow.credentials,
                            static_discovery=False)
            events_result = service.events().list(
                calendarId='primary',
                timeMin='2023-04-23T00:00:00Z',
                maxResults=10,
                singleEvents=True,
                orderBy='startTime').execute()
            events = events_result.get('items', [])
        except HttpError as error:
            return Response(status=400,
                            data={'message': f'An error occurred: {error}'})

        return Response(status=200, data={'data': events})
